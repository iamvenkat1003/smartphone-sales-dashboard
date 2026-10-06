from typing import Annotated, Callable

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Admin, Manufacturer
from app.schemas.schemas import (
    AdminCreate,
    AdminPublic,
    CustomerAdminUpdate,
    PhoneAdminCreate,
    PhoneAdminUpdate,
    PromotionAdminCreate,
    PromotionAdminUpdate,
    PurchaseAdminCreate,
    PurchaseAdminUpdate,
    StatusUpdate,
)
from app.services import admin_service
from app.services.admin_service import AdminServiceError
from app.services.auth_service import get_current_admin


router = APIRouter()


def _run(operation: Callable):
    try:
        return operation()
    except AdminServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message) from error


@router.get("/overview")
def overview(
    database: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return _run(lambda: admin_service.get_overview(database))


@router.get("/manufacturers")
def manufacturers(
    database: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return [
        {
            "manufacturer_id": manufacturer.manufacturer_id,
            "name": manufacturer.name,
        }
        for manufacturer in database.scalars(
            select(Manufacturer).order_by(Manufacturer.name)
        ).all()
    ]


@router.get("/admins", response_model=list[AdminPublic])
def admins(
    database: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return _run(lambda: admin_service.list_admins(database))


@router.post("/admins", response_model=AdminPublic, status_code=status.HTTP_201_CREATED)
def create_admin(
    payload: AdminCreate,
    database: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return _run(lambda: admin_service.create_admin(database, payload, current_admin))


@router.get("/admins/{admin_id}", response_model=AdminPublic)
def admin_detail(
    admin_id: Annotated[int, Path(ge=1)],
    database: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return _run(lambda: admin_service.get_admin(database, admin_id))


@router.patch("/admins/{admin_id}/status", response_model=AdminPublic)
def update_admin_status(
    admin_id: Annotated[int, Path(ge=1)],
    payload: StatusUpdate,
    database: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return _run(
        lambda: admin_service.set_admin_status(
            database,
            admin_id,
            payload.is_active,
            current_admin,
        )
    )


@router.get("/phones")
def phones(
    database: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return _run(lambda: admin_service.list_phones(database))


@router.post("/phones", status_code=status.HTTP_201_CREATED)
def create_phone(
    payload: PhoneAdminCreate,
    database: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return _run(lambda: admin_service.create_phone(database, payload))


@router.get("/phones/{phone_id}")
def phone_detail(
    phone_id: Annotated[int, Path(ge=1)],
    database: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return _run(lambda: admin_service.get_phone(database, phone_id))


@router.patch("/phones/{phone_id}")
def update_phone(
    phone_id: Annotated[int, Path(ge=1)],
    payload: PhoneAdminUpdate,
    database: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return _run(lambda: admin_service.update_phone(database, phone_id, payload))


@router.patch("/phones/{phone_id}/status")
def update_phone_status(
    phone_id: Annotated[int, Path(ge=1)],
    payload: StatusUpdate,
    database: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return _run(
        lambda: admin_service.set_phone_status(database, phone_id, payload.is_active)
    )


@router.get("/promotions")
def promotions(
    database: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return _run(lambda: admin_service.list_promotions(database))


@router.post("/promotions", status_code=status.HTTP_201_CREATED)
def create_promotion(
    payload: PromotionAdminCreate,
    database: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return _run(lambda: admin_service.create_promotion(database, payload))


@router.get("/promotions/{promotion_id}")
def promotion_detail(
    promotion_id: Annotated[int, Path(ge=1)],
    database: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return _run(lambda: admin_service.get_promotion(database, promotion_id))


@router.patch("/promotions/{promotion_id}")
def update_promotion(
    promotion_id: Annotated[int, Path(ge=1)],
    payload: PromotionAdminUpdate,
    database: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return _run(
        lambda: admin_service.update_promotion(database, promotion_id, payload)
    )


@router.patch("/promotions/{promotion_id}/status")
def update_promotion_status(
    promotion_id: Annotated[int, Path(ge=1)],
    payload: StatusUpdate,
    database: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return _run(
        lambda: admin_service.set_promotion_status(
            database,
            promotion_id,
            payload.is_active,
        )
    )


@router.get("/customers")
def customers(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    search: Annotated[str | None, Query(max_length=100)] = None,
    database: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return _run(
        lambda: admin_service.list_customers(database, page, page_size, search)
    )


@router.get("/customers/{user_id}")
def customer_detail(
    user_id: Annotated[int, Path(ge=1)],
    database: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return _run(lambda: admin_service.get_customer(database, user_id))


@router.patch("/customers/{user_id}")
def update_customer(
    user_id: Annotated[int, Path(ge=1)],
    payload: CustomerAdminUpdate,
    database: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return _run(lambda: admin_service.update_customer(database, user_id, payload))


@router.get("/purchases")
def purchases(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    search: Annotated[str | None, Query(max_length=100)] = None,
    database: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return _run(
        lambda: admin_service.list_purchases(database, page, page_size, search)
    )


@router.post("/purchases", status_code=status.HTTP_201_CREATED)
def create_purchase(
    payload: PurchaseAdminCreate,
    database: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return _run(lambda: admin_service.create_purchase(database, payload))


@router.get("/purchases/{purchase_id}")
def purchase_detail(
    purchase_id: Annotated[int, Path(ge=1)],
    database: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return _run(lambda: admin_service.get_purchase(database, purchase_id))


@router.patch("/purchases/{purchase_id}")
def update_purchase(
    purchase_id: Annotated[int, Path(ge=1)],
    payload: PurchaseAdminUpdate,
    database: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return _run(
        lambda: admin_service.update_purchase(database, purchase_id, payload)
    )
