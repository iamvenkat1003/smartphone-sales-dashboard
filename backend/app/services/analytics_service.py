"""Read-only aggregate queries for the analytics API.

The calculations in this module mirror backend/analytics_queries.sql, which is
the source of truth for the dashboard's business metrics.
"""

from typing import Literal

from sqlalchemy import case, distinct, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.models import (
    Manufacturer,
    Phone,
    Promotion,
    Purchase,
    PurchasePromotion,
    User,
)


TopPhoneMetric = Literal["units", "revenue"]


class AnalyticsServiceError(RuntimeError):
    """Raised when an analytics database query cannot be completed."""


def _fetch_one(database: Session, statement):
    try:
        return dict(database.execute(statement).mappings().one())
    except SQLAlchemyError as error:
        raise AnalyticsServiceError("Analytics query failed") from error


def _fetch_all(database: Session, statement):
    try:
        return [dict(row) for row in database.execute(statement).mappings().all()]
    except SQLAlchemyError as error:
        raise AnalyticsServiceError("Analytics query failed") from error


def get_kpis(database: Session):
    total_units = func.coalesce(func.sum(Purchase.quantity), 0)
    total_revenue = func.coalesce(
        func.sum(Purchase.sale_price * Purchase.quantity),
        0.0,
    )
    weighted_average = case(
        (total_units == 0, 0.0),
        else_=total_revenue / total_units,
    )

    statement = select(
        func.count(distinct(Purchase.user_id)).label("total_customers"),
        func.count(Purchase.purchase_id).label("total_transactions"),
        total_units.label("total_units_sold"),
        func.round(total_revenue, 2).label("total_revenue"),
        func.round(weighted_average, 2).label("average_selling_price"),
    )
    return _fetch_one(database, statement)


def get_top_phones(database: Session, metric: TopPhoneMetric, limit: int):
    units_sold = func.coalesce(func.sum(Purchase.quantity), 0)
    revenue = func.coalesce(
        func.sum(Purchase.sale_price * Purchase.quantity),
        0.0,
    )
    weighted_average = case(
        (units_sold == 0, 0.0),
        else_=revenue / units_sold,
    )

    order_expression = units_sold.desc() if metric == "units" else revenue.desc()
    statement = (
        select(
            Phone.phone_id,
            Manufacturer.name.label("manufacturer"),
            Phone.model_name,
            units_sold.label("units_sold"),
            func.round(revenue, 2).label("revenue"),
            func.round(weighted_average, 2).label("average_selling_price"),
            Phone.image_path,
        )
        .select_from(Phone)
        .join(
            Manufacturer,
            Manufacturer.manufacturer_id == Phone.manufacturer_id,
        )
        .outerjoin(Purchase, Purchase.phone_id == Phone.phone_id)
        .group_by(
            Phone.phone_id,
            Manufacturer.name,
            Phone.model_name,
            Phone.image_path,
        )
        .order_by(order_expression, Manufacturer.name, Phone.model_name)
        .limit(limit)
    )
    return _fetch_all(database, statement)


def get_manufacturer_performance(database: Session):
    units_sold = func.coalesce(func.sum(Purchase.quantity), 0)
    revenue = func.coalesce(
        func.sum(Purchase.sale_price * Purchase.quantity),
        0.0,
    )
    total_units = select(
        func.coalesce(func.sum(Purchase.quantity), 0)
    ).scalar_subquery()
    unit_share = case(
        (total_units == 0, 0.0),
        else_=100.0 * units_sold / total_units,
    )

    statement = (
        select(
            Manufacturer.manufacturer_id,
            Manufacturer.name.label("manufacturer_name"),
            units_sold.label("units_sold"),
            func.round(revenue, 2).label("revenue"),
            func.round(unit_share, 2).label("unit_share_percentage"),
        )
        .select_from(Manufacturer)
        .outerjoin(Phone, Phone.manufacturer_id == Manufacturer.manufacturer_id)
        .outerjoin(Purchase, Purchase.phone_id == Phone.phone_id)
        .group_by(Manufacturer.manufacturer_id, Manufacturer.name)
        .order_by(units_sold.desc(), Manufacturer.name)
    )
    return _fetch_all(database, statement)


def get_sales_trend(database: Session):
    month = func.strftime("%Y-%m", Purchase.purchase_date)
    statement = (
        select(
            month.label("month"),
            func.count(Purchase.purchase_id).label("transactions"),
            func.sum(Purchase.quantity).label("units_sold"),
            func.round(
                func.sum(Purchase.sale_price * Purchase.quantity),
                2,
            ).label("revenue"),
        )
        .group_by(month)
        .order_by(month)
    )
    return _fetch_all(database, statement)


def get_promotion_analytics(database: Session):
    """Return promotion-level results without using them as company totals.

    One purchase may be attached to two promotions. Its units and revenue are
    intentionally associated with each promotion it used, so summing revenue
    across this endpoint would double-count those multi-promotion purchases.
    """

    times_used = func.count(distinct(PurchasePromotion.purchase_id))
    units_sold = func.coalesce(func.sum(Purchase.quantity), 0)
    associated_revenue = func.coalesce(
        func.sum(Purchase.sale_price * Purchase.quantity),
        0.0,
    )
    total_discount = func.coalesce(
        func.sum(PurchasePromotion.discount_amount),
        0.0,
    )

    statement = (
        select(
            Promotion.promotion_id,
            Promotion.promo_code,
            Promotion.promo_name,
            Manufacturer.name.label("manufacturer"),
            Phone.model_name.label("phone_model"),
            times_used.label("times_used"),
            units_sold.label("units_sold"),
            func.round(associated_revenue, 2).label("associated_revenue"),
            func.round(total_discount, 2).label("total_discount_amount"),
        )
        .select_from(Promotion)
        .join(Phone, Phone.phone_id == Promotion.phone_id)
        .join(
            Manufacturer,
            Manufacturer.manufacturer_id == Phone.manufacturer_id,
        )
        .outerjoin(
            PurchasePromotion,
            PurchasePromotion.promotion_id == Promotion.promotion_id,
        )
        .outerjoin(
            Purchase,
            Purchase.purchase_id == PurchasePromotion.purchase_id,
        )
        .group_by(
            Promotion.promotion_id,
            Promotion.promo_code,
            Promotion.promo_name,
            Manufacturer.name,
            Phone.model_name,
        )
        .order_by(times_used.desc(), Promotion.promo_code)
    )
    return _fetch_all(database, statement)


def get_customer_insights(database: Session):
    repeat_customer_ids = (
        select(Purchase.user_id)
        .group_by(Purchase.user_id)
        .having(func.count(Purchase.purchase_id) > 1)
        .subquery()
    )
    multi_phone_customer_ids = (
        select(Purchase.user_id)
        .group_by(Purchase.user_id)
        .having(func.count(distinct(Purchase.phone_id)) > 1)
        .subquery()
    )
    multi_manufacturer_customer_ids = (
        select(Purchase.user_id)
        .join(Phone, Phone.phone_id == Purchase.phone_id)
        .group_by(Purchase.user_id)
        .having(func.count(distinct(Phone.manufacturer_id)) > 1)
        .subquery()
    )

    total_customers = select(func.count()).select_from(User).scalar_subquery()
    repeat_customers = (
        select(func.count()).select_from(repeat_customer_ids).scalar_subquery()
    )
    multi_phone_customers = (
        select(func.count()).select_from(multi_phone_customer_ids).scalar_subquery()
    )
    multi_manufacturer_customers = (
        select(func.count())
        .select_from(multi_manufacturer_customer_ids)
        .scalar_subquery()
    )
    total_units = select(
        func.coalesce(func.sum(Purchase.quantity), 0)
    ).scalar_subquery()

    repeat_percentage = case(
        (total_customers == 0, 0.0),
        else_=100.0 * repeat_customers / total_customers,
    )
    multi_manufacturer_percentage = case(
        (total_customers == 0, 0.0),
        else_=100.0 * multi_manufacturer_customers / total_customers,
    )
    average_units = case(
        (total_customers == 0, 0.0),
        else_=1.0 * total_units / total_customers,
    )

    statement = select(
        total_customers.label("total_customers"),
        repeat_customers.label("repeat_customers"),
        func.round(repeat_percentage, 2).label("repeat_customer_percentage"),
        multi_phone_customers.label("multi_phone_customers"),
        multi_manufacturer_customers.label("multi_manufacturer_customers"),
        func.round(multi_manufacturer_percentage, 2).label(
            "multi_manufacturer_percentage"
        ),
        func.round(average_units, 2).label("average_units_per_customer"),
    )
    return _fetch_one(database, statement)
