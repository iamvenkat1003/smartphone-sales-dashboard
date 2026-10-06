"""Protected admin queries and mutations for the interview demo."""

from sqlalchemy import delete, distinct, func, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, aliased

from app.models.models import (
    Admin,
    Manufacturer,
    Phone,
    Promotion,
    Purchase,
    PurchasePromotion,
    User,
    UserContact,
)
from app.services.auth_service import admin_to_public, hash_password, normalize_email


class AdminServiceError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _commit(database: Session, conflict_message: str):
    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise AdminServiceError(conflict_message, 409) from error
    except SQLAlchemyError as error:
        database.rollback()
        raise AdminServiceError("Database operation failed", 500) from error


def get_overview(database: Session) -> dict:
    total_units = func.coalesce(func.sum(Purchase.quantity), 0)
    total_revenue = func.coalesce(func.sum(Purchase.sale_price * Purchase.quantity), 0)
    result = database.execute(
        select(
            func.count(distinct(Purchase.user_id)).label("total_customers"),
            func.count(Purchase.purchase_id).label("total_transactions"),
            total_units.label("total_units_sold"),
            func.round(total_revenue, 2).label("total_revenue"),
        )
    ).mappings().one()
    return {
        **dict(result),
        "active_phones": database.scalar(
            select(func.count()).select_from(Phone).where(Phone.is_active == 1)
        ),
        "active_promotions": database.scalar(
            select(func.count()).select_from(Promotion).where(Promotion.is_active == 1)
        ),
    }


def list_admins(database: Session) -> list[dict]:
    creator = aliased(Admin)
    rows = database.execute(
        select(Admin, creator.first_name, creator.last_name)
        .outerjoin(creator, creator.admin_id == Admin.created_by)
        .order_by(Admin.created_at, Admin.admin_id)
    ).all()
    return [
        admin_to_public(
            admin,
            f"{creator_first} {creator_last}" if creator_first else None,
        )
        for admin, creator_first, creator_last in rows
    ]


def get_admin(database: Session, admin_id: int) -> dict:
    admin = database.get(Admin, admin_id)
    if admin is None:
        raise AdminServiceError("Admin not found", 404)
    creator_name = None
    if admin.created_by:
        creator = database.get(Admin, admin.created_by)
        if creator:
            creator_name = f"{creator.first_name} {creator.last_name}"
    return admin_to_public(admin, creator_name)


def create_admin(database: Session, payload, current_admin: Admin) -> dict:
    admin = Admin(
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=normalize_email(payload.email),
        password_hash=hash_password(payload.password),
        is_active=1,
        created_by=current_admin.admin_id,
    )
    database.add(admin)
    _commit(database, "An admin with this email already exists")
    database.refresh(admin)
    return admin_to_public(
        admin,
        f"{current_admin.first_name} {current_admin.last_name}",
    )


def set_admin_status(
    database: Session,
    admin_id: int,
    is_active: int,
    current_admin: Admin,
) -> dict:
    admin = database.get(Admin, admin_id)
    if admin is None:
        raise AdminServiceError("Admin not found", 404)
    if admin.admin_id == current_admin.admin_id and is_active == 0:
        raise AdminServiceError("You cannot deactivate your own admin account", 409)
    if is_active == 0:
        active_count = database.scalar(
            select(func.count()).select_from(Admin).where(Admin.is_active == 1)
        )
        if active_count <= 1:
            raise AdminServiceError("At least one active admin is required", 409)
    admin.is_active = is_active
    _commit(database, "Unable to update admin status")
    return get_admin(database, admin_id)


def _phone_dict(phone: Phone, manufacturer_name: str) -> dict:
    return {
        "phone_id": phone.phone_id,
        "manufacturer_id": phone.manufacturer_id,
        "manufacturer_name": manufacturer_name,
        "model_name": phone.model_name,
        "release_date": phone.release_date,
        "storage_gb": phone.storage_gb,
        "ram_gb": phone.ram_gb,
        "launch_price": phone.launch_price,
        "operating_system": phone.operating_system,
        "image_path": phone.image_path,
        "is_active": phone.is_active,
    }


def list_phones(database: Session) -> list[dict]:
    rows = database.execute(
        select(Phone, Manufacturer.name)
        .join(Manufacturer, Manufacturer.manufacturer_id == Phone.manufacturer_id)
        .order_by(Manufacturer.name, Phone.model_name, Phone.storage_gb)
    ).all()
    return [_phone_dict(phone, manufacturer_name) for phone, manufacturer_name in rows]


def get_phone(database: Session, phone_id: int) -> dict:
    row = database.execute(
        select(Phone, Manufacturer.name)
        .join(Manufacturer, Manufacturer.manufacturer_id == Phone.manufacturer_id)
        .where(Phone.phone_id == phone_id)
    ).one_or_none()
    if row is None:
        raise AdminServiceError("Phone not found", 404)
    return _phone_dict(row[0], row[1])


def _ensure_manufacturer(database: Session, manufacturer_id: int):
    if database.get(Manufacturer, manufacturer_id) is None:
        raise AdminServiceError("Manufacturer not found", 404)


def create_phone(database: Session, payload) -> dict:
    _ensure_manufacturer(database, payload.manufacturer_id)
    phone = Phone(**payload.model_dump())
    database.add(phone)
    _commit(database, "This phone configuration already exists")
    return get_phone(database, phone.phone_id)


def update_phone(database: Session, phone_id: int, payload) -> dict:
    phone = database.get(Phone, phone_id)
    if phone is None:
        raise AdminServiceError("Phone not found", 404)
    values = payload.model_dump(exclude_unset=True)
    if "manufacturer_id" in values:
        _ensure_manufacturer(database, values["manufacturer_id"])
    for field, value in values.items():
        setattr(phone, field, value)
    _commit(database, "This phone configuration conflicts with an existing phone")
    return get_phone(database, phone_id)


def set_phone_status(database: Session, phone_id: int, is_active: int) -> dict:
    phone = database.get(Phone, phone_id)
    if phone is None:
        raise AdminServiceError("Phone not found", 404)
    phone.is_active = is_active
    _commit(database, "Unable to update phone status")
    return get_phone(database, phone_id)


def _promotion_dict(promotion: Promotion, phone: Phone, manufacturer: str) -> dict:
    return {
        "promotion_id": promotion.promotion_id,
        "phone_id": promotion.phone_id,
        "phone_model": phone.model_name,
        "manufacturer": manufacturer,
        "promo_code": promotion.promo_code,
        "promo_name": promotion.promo_name,
        "discount_type": promotion.discount_type,
        "discount_value": promotion.discount_value,
        "start_date": promotion.start_date,
        "end_date": promotion.end_date,
        "description": promotion.description,
        "is_active": promotion.is_active,
    }


def list_promotions(database: Session) -> list[dict]:
    rows = database.execute(
        select(Promotion, Phone, Manufacturer.name)
        .join(Phone, Phone.phone_id == Promotion.phone_id)
        .join(Manufacturer, Manufacturer.manufacturer_id == Phone.manufacturer_id)
        .order_by(Promotion.promo_code)
    ).all()
    return [_promotion_dict(promotion, phone, manufacturer) for promotion, phone, manufacturer in rows]


def get_promotion(database: Session, promotion_id: int) -> dict:
    row = database.execute(
        select(Promotion, Phone, Manufacturer.name)
        .join(Phone, Phone.phone_id == Promotion.phone_id)
        .join(Manufacturer, Manufacturer.manufacturer_id == Phone.manufacturer_id)
        .where(Promotion.promotion_id == promotion_id)
    ).one_or_none()
    if row is None:
        raise AdminServiceError("Promotion not found", 404)
    return _promotion_dict(row[0], row[1], row[2])


def _validate_promotion_values(values: dict, existing: Promotion | None = None):
    discount_type = values.get("discount_type", existing.discount_type if existing else None)
    discount_value = values.get("discount_value", existing.discount_value if existing else None)
    start_date = values.get("start_date", existing.start_date if existing else None)
    end_date = values.get("end_date", existing.end_date if existing else None)
    if discount_type == "PERCENTAGE" and discount_value > 100:
        raise AdminServiceError("Percentage discounts cannot exceed 100")
    if start_date and end_date and end_date < start_date:
        raise AdminServiceError("End date must be on or after start date")


def create_promotion(database: Session, payload) -> dict:
    if database.get(Phone, payload.phone_id) is None:
        raise AdminServiceError("Phone not found", 404)
    values = payload.model_dump()
    _validate_promotion_values(values)
    promotion = Promotion(**values)
    database.add(promotion)
    _commit(database, "A promotion with this code already exists")
    return get_promotion(database, promotion.promotion_id)


def update_promotion(database: Session, promotion_id: int, payload) -> dict:
    promotion = database.get(Promotion, promotion_id)
    if promotion is None:
        raise AdminServiceError("Promotion not found", 404)
    values = payload.model_dump(exclude_unset=True)
    if "phone_id" in values and database.get(Phone, values["phone_id"]) is None:
        raise AdminServiceError("Phone not found", 404)
    _validate_promotion_values(values, promotion)
    for field, value in values.items():
        setattr(promotion, field, value)
    _commit(database, "A promotion with this code already exists")
    return get_promotion(database, promotion_id)


def set_promotion_status(database: Session, promotion_id: int, is_active: int) -> dict:
    promotion = database.get(Promotion, promotion_id)
    if promotion is None:
        raise AdminServiceError("Promotion not found", 404)
    promotion.is_active = is_active
    _commit(database, "Unable to update promotion status")
    return get_promotion(database, promotion_id)


def _customer_metrics_subquery():
    return (
        select(
            Purchase.user_id.label("user_id"),
            func.count(Purchase.purchase_id).label("purchase_count"),
            func.coalesce(func.sum(Purchase.quantity), 0).label("units_purchased"),
            func.round(
                func.coalesce(func.sum(Purchase.sale_price * Purchase.quantity), 0),
                2,
            ).label("total_spend"),
        )
        .group_by(Purchase.user_id)
        .subquery()
    )


def _customer_row_to_dict(row) -> dict:
    return {
        "user_id": row.user_id,
        "first_name": row.first_name,
        "last_name": row.last_name,
        "date_of_birth": row.date_of_birth,
        "gender": row.gender,
        "occupation": row.occupation,
        "income_range": row.income_range,
        "created_at": row.created_at,
        "email": row.email,
        "phone_number": row.phone_number,
        "street": row.street,
        "city": row.city,
        "state": row.state,
        "zip_code": row.zip_code,
        "country": row.country,
        "purchase_count": row.purchase_count,
        "units_purchased": row.units_purchased,
        "total_spend": row.total_spend,
    }


def _customer_statement():
    metrics = _customer_metrics_subquery()
    return (
        select(
            User.user_id,
            User.first_name,
            User.last_name,
            User.date_of_birth,
            User.gender,
            User.occupation,
            User.income_range,
            User.created_at,
            UserContact.email,
            UserContact.phone_number,
            UserContact.street,
            UserContact.city,
            UserContact.state,
            UserContact.zip_code,
            UserContact.country,
            func.coalesce(metrics.c.purchase_count, 0).label("purchase_count"),
            func.coalesce(metrics.c.units_purchased, 0).label("units_purchased"),
            func.coalesce(metrics.c.total_spend, 0).label("total_spend"),
        )
        .outerjoin(UserContact, UserContact.user_id == User.user_id)
        .outerjoin(metrics, metrics.c.user_id == User.user_id)
    )


def list_customers(database: Session, page: int, page_size: int, search: str | None) -> dict:
    statement = _customer_statement()
    count_statement = select(func.count()).select_from(User).outerjoin(
        UserContact, UserContact.user_id == User.user_id
    )
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        condition = or_(
            User.first_name.ilike(pattern),
            User.last_name.ilike(pattern),
            UserContact.email.ilike(pattern),
        )
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    total = database.scalar(count_statement)
    rows = database.execute(
        statement.order_by(User.user_id).offset((page - 1) * page_size).limit(page_size)
    ).mappings().all()
    return {
        "items": [_customer_row_to_dict(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_customer(database: Session, user_id: int) -> dict:
    row = database.execute(
        _customer_statement().where(User.user_id == user_id)
    ).mappings().one_or_none()
    if row is None:
        raise AdminServiceError("Customer not found", 404)
    return _customer_row_to_dict(row)


def update_customer(database: Session, user_id: int, payload) -> dict:
    user = database.get(User, user_id)
    if user is None:
        raise AdminServiceError("Customer not found", 404)
    values = payload.model_dump(exclude_unset=True)
    user_fields = {
        "first_name", "last_name", "date_of_birth", "gender", "occupation", "income_range"
    }
    contact_fields = {
        "email", "phone_number", "street", "city", "state", "zip_code", "country"
    }
    for field in user_fields & values.keys():
        setattr(user, field, values[field])
    contact_values = contact_fields & values.keys()
    if contact_values:
        contact = database.scalar(
            select(UserContact).where(UserContact.user_id == user_id)
        )
        if contact is None:
            contact = UserContact(user_id=user_id)
            database.add(contact)
        for field in contact_values:
            value = values[field]
            if field == "email" and value:
                value = normalize_email(value)
            setattr(contact, field, value)
    _commit(database, "Customer contact information conflicts with another customer")
    return get_customer(database, user_id)


def _purchase_dict(row) -> dict:
    return {
        "purchase_id": row.purchase_id,
        "user_id": row.user_id,
        "customer_name": row.customer_name,
        "phone_id": row.phone_id,
        "phone_name": row.phone_name,
        "purchase_date": row.purchase_date,
        "sale_price": row.sale_price,
        "quantity": row.quantity,
        "phone_status": row.phone_status,
    }


def _purchase_statement():
    return (
        select(
            Purchase.purchase_id,
            Purchase.user_id,
            (User.first_name + " " + User.last_name).label("customer_name"),
            Purchase.phone_id,
            (Manufacturer.name + " " + Phone.model_name).label("phone_name"),
            Purchase.purchase_date,
            Purchase.sale_price,
            Purchase.quantity,
            Purchase.phone_status,
        )
        .join(User, User.user_id == Purchase.user_id)
        .join(Phone, Phone.phone_id == Purchase.phone_id)
        .join(Manufacturer, Manufacturer.manufacturer_id == Phone.manufacturer_id)
    )


def list_purchases(database: Session, page: int, page_size: int, search: str | None) -> dict:
    statement = _purchase_statement()
    count_statement = select(func.count()).select_from(Purchase)
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        condition = or_(
            User.first_name.ilike(pattern),
            User.last_name.ilike(pattern),
            Phone.model_name.ilike(pattern),
            Manufacturer.name.ilike(pattern),
        )
        statement = statement.where(condition)
        count_statement = (
            count_statement.join(User, User.user_id == Purchase.user_id)
            .join(Phone, Phone.phone_id == Purchase.phone_id)
            .join(Manufacturer, Manufacturer.manufacturer_id == Phone.manufacturer_id)
            .where(condition)
        )
    total = database.scalar(count_statement)
    rows = database.execute(
        statement.order_by(Purchase.purchase_id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).mappings().all()
    return {
        "items": [_purchase_dict(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_purchase(database: Session, purchase_id: int) -> dict:
    row = database.execute(
        _purchase_statement().where(Purchase.purchase_id == purchase_id)
    ).mappings().one_or_none()
    if row is None:
        raise AdminServiceError("Purchase not found", 404)
    result = _purchase_dict(row)
    links = database.execute(
        select(
            PurchasePromotion.promotion_id,
            Promotion.promo_code,
            PurchasePromotion.discount_amount,
        )
        .join(Promotion, Promotion.promotion_id == PurchasePromotion.promotion_id)
        .where(PurchasePromotion.purchase_id == purchase_id)
    ).mappings().all()
    result["promotions"] = [dict(link) for link in links]
    return result


def _validate_purchase_references(database: Session, user_id: int, phone_id: int):
    if database.get(User, user_id) is None:
        raise AdminServiceError("Customer not found", 404)
    if database.get(Phone, phone_id) is None:
        raise AdminServiceError("Phone not found", 404)


def _replace_purchase_promotions(
    database: Session,
    purchase_id: int,
    phone_id: int,
    promotions,
):
    database.execute(
        delete(PurchasePromotion).where(PurchasePromotion.purchase_id == purchase_id)
    )
    database.flush()
    for item in promotions:
        promotion = database.get(Promotion, item.promotion_id)
        if promotion is None:
            raise AdminServiceError(f"Promotion {item.promotion_id} not found", 404)
        if promotion.phone_id != phone_id:
            raise AdminServiceError(
                f"Promotion {item.promotion_id} does not belong to the selected phone"
            )
        database.add(
            PurchasePromotion(
                purchase_id=purchase_id,
                promotion_id=item.promotion_id,
                discount_amount=item.discount_amount,
            )
        )


def create_purchase(database: Session, payload) -> dict:
    _validate_purchase_references(database, payload.user_id, payload.phone_id)
    values = payload.model_dump(exclude={"promotions"})
    purchase = Purchase(**values)
    try:
        database.add(purchase)
        database.flush()
        _replace_purchase_promotions(
            database,
            purchase.purchase_id,
            purchase.phone_id,
            payload.promotions,
        )
        database.commit()
    except AdminServiceError:
        database.rollback()
        raise
    except IntegrityError as error:
        database.rollback()
        raise AdminServiceError("Purchase violates a database constraint", 409) from error
    database.refresh(purchase)
    return get_purchase(database, purchase.purchase_id)


def update_purchase(database: Session, purchase_id: int, payload) -> dict:
    purchase = database.get(Purchase, purchase_id)
    if purchase is None:
        raise AdminServiceError("Purchase not found", 404)
    values = payload.model_dump(exclude_unset=True, exclude={"promotions"})
    previous_phone_id = purchase.phone_id
    user_id = values.get("user_id", purchase.user_id)
    phone_id = values.get("phone_id", purchase.phone_id)
    _validate_purchase_references(database, user_id, phone_id)
    try:
        for field, value in values.items():
            setattr(purchase, field, value)
        if payload.promotions is not None:
            _replace_purchase_promotions(
                database,
                purchase_id,
                phone_id,
                payload.promotions,
            )
        elif phone_id != previous_phone_id:
            existing_count = database.scalar(
                select(func.count())
                .select_from(PurchasePromotion)
                .where(PurchasePromotion.purchase_id == purchase_id)
            )
            if existing_count:
                raise AdminServiceError(
                    "Provide promotions when changing a phone on a promoted purchase"
                )
        database.commit()
    except AdminServiceError:
        database.rollback()
        raise
    except IntegrityError as error:
        database.rollback()
        raise AdminServiceError("Purchase violates a database constraint", 409) from error
    return get_purchase(database, purchase_id)
