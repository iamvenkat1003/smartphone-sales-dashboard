"""Read-only queries for the public phone catalog API."""

from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.models import (
    Manufacturer,
    Phone,
    Promotion,
    Purchase,
    PurchasePromotion,
)


class PhoneServiceError(RuntimeError):
    """Raised when a phone database query cannot be completed."""


def _fetch_one_or_none(database: Session, statement):
    try:
        row = database.execute(statement).mappings().one_or_none()
        return dict(row) if row else None
    except SQLAlchemyError as error:
        raise PhoneServiceError("Phone query failed") from error


def _fetch_all(database: Session, statement):
    try:
        return [dict(row) for row in database.execute(statement).mappings().all()]
    except SQLAlchemyError as error:
        raise PhoneServiceError("Phone query failed") from error


def _sales_metrics_subquery():
    """Aggregate sales once per phone, including a quantity-weighted ASP."""

    units_sold = func.sum(Purchase.quantity)
    revenue = func.sum(Purchase.sale_price * Purchase.quantity)
    return (
        select(
            Purchase.phone_id.label("phone_id"),
            func.count(Purchase.purchase_id).label("transactions"),
            units_sold.label("units_sold"),
            revenue.label("revenue"),
            func.round(
                revenue / func.nullif(units_sold, 0),
                2,
            ).label("average_selling_price"),
        )
        .group_by(Purchase.phone_id)
        .subquery()
    )


def list_phones(
    database: Session,
    manufacturer_id: int | None,
    search: str | None,
    active_only: bool,
):
    sales = _sales_metrics_subquery()
    statement = (
        select(
            Phone.phone_id,
            Phone.manufacturer_id,
            Manufacturer.name.label("manufacturer_name"),
            Phone.model_name,
            Phone.release_date,
            Phone.storage_gb,
            Phone.ram_gb,
            Phone.launch_price,
            Phone.operating_system,
            Phone.image_path,
            Phone.is_active,
            func.coalesce(sales.c.units_sold, 0).label("units_sold"),
            func.round(func.coalesce(sales.c.revenue, 0.0), 2).label("revenue"),
            sales.c.average_selling_price,
        )
        .select_from(Phone)
        .join(
            Manufacturer,
            Manufacturer.manufacturer_id == Phone.manufacturer_id,
        )
        .outerjoin(sales, sales.c.phone_id == Phone.phone_id)
    )

    if manufacturer_id is not None:
        statement = statement.where(Phone.manufacturer_id == manufacturer_id)
    if active_only:
        statement = statement.where(Phone.is_active == 1)
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                Manufacturer.name.ilike(pattern),
                Phone.model_name.ilike(pattern),
            )
        )

    statement = statement.order_by(
        Manufacturer.name,
        Phone.model_name,
        Phone.storage_gb,
    )
    return _fetch_all(database, statement)


def get_phone_detail(database: Session, phone_id: int):
    sales = _sales_metrics_subquery()
    phone_statement = (
        select(
            Phone.phone_id,
            Phone.manufacturer_id,
            Manufacturer.name.label("manufacturer_name"),
            Phone.model_name,
            Phone.release_date,
            Phone.storage_gb,
            Phone.ram_gb,
            Phone.launch_price,
            Phone.operating_system,
            Phone.image_path,
            Phone.is_active,
            func.coalesce(sales.c.transactions, 0).label("transactions"),
            func.coalesce(sales.c.units_sold, 0).label("units_sold"),
            func.round(func.coalesce(sales.c.revenue, 0.0), 2).label("revenue"),
            sales.c.average_selling_price,
        )
        .select_from(Phone)
        .join(
            Manufacturer,
            Manufacturer.manufacturer_id == Phone.manufacturer_id,
        )
        .outerjoin(sales, sales.c.phone_id == Phone.phone_id)
        .where(Phone.phone_id == phone_id)
    )
    phone = _fetch_one_or_none(database, phone_statement)
    if phone is None:
        return None

    promotion_usage = (
        select(
            PurchasePromotion.promotion_id.label("promotion_id"),
            func.count(PurchasePromotion.purchase_promo_id).label("times_used"),
        )
        .group_by(PurchasePromotion.promotion_id)
        .subquery()
    )
    promotion_statement = (
        select(
            Promotion.promotion_id,
            Promotion.promo_code,
            Promotion.promo_name,
            Promotion.discount_type,
            Promotion.discount_value,
            Promotion.start_date,
            Promotion.end_date,
            Promotion.description,
            Promotion.is_active,
            func.coalesce(promotion_usage.c.times_used, 0).label("times_used"),
        )
        .select_from(Promotion)
        .outerjoin(
            promotion_usage,
            promotion_usage.c.promotion_id == Promotion.promotion_id,
        )
        .where(Promotion.phone_id == phone_id)
        .order_by(Promotion.promo_code)
    )
    phone["promotions"] = _fetch_all(database, promotion_statement)
    return phone


def compare_phones(database: Session, phone_ids: list[int]):
    # Sales and promotion usage are deliberately aggregated in separate
    # subqueries. Joining raw purchases to raw promotion links would multiply
    # sales for purchases that used two promotions.
    sales = _sales_metrics_subquery()
    promotion_usage = (
        select(
            Purchase.phone_id.label("phone_id"),
            func.count(PurchasePromotion.purchase_promo_id).label(
                "promotion_uses"
            ),
        )
        .select_from(PurchasePromotion)
        .join(Purchase, Purchase.purchase_id == PurchasePromotion.purchase_id)
        .group_by(Purchase.phone_id)
        .subquery()
    )

    statement = (
        select(
            Phone.phone_id,
            Manufacturer.name.label("manufacturer"),
            Phone.model_name,
            Phone.release_date,
            Phone.storage_gb,
            Phone.ram_gb,
            Phone.launch_price,
            Phone.operating_system,
            Phone.image_path,
            func.coalesce(sales.c.transactions, 0).label("transactions"),
            func.coalesce(sales.c.units_sold, 0).label("units_sold"),
            func.round(func.coalesce(sales.c.revenue, 0.0), 2).label("revenue"),
            sales.c.average_selling_price,
            func.coalesce(promotion_usage.c.promotion_uses, 0).label(
                "promotion_uses"
            ),
        )
        .select_from(Phone)
        .join(
            Manufacturer,
            Manufacturer.manufacturer_id == Phone.manufacturer_id,
        )
        .outerjoin(sales, sales.c.phone_id == Phone.phone_id)
        .outerjoin(
            promotion_usage,
            promotion_usage.c.phone_id == Phone.phone_id,
        )
        .where(Phone.phone_id.in_(phone_ids))
    )
    rows = _fetch_all(database, statement)
    rows_by_id = {row["phone_id"]: row for row in rows}
    return [rows_by_id[phone_id] for phone_id in phone_ids if phone_id in rows_by_id]
