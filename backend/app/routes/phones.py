from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import (
    PhoneComparisonItem,
    PhoneDetailResponse,
    PhoneListItem,
)
from app.services import phone_service
from app.services.phone_service import PhoneServiceError


router = APIRouter()


def _raise_phone_data_unavailable(error: PhoneServiceError) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Phone data is temporarily unavailable",
    ) from error


@router.get(
    "",
    response_model=list[PhoneListItem],
    summary="List public phone catalog items",
)
def list_phones(
    manufacturer_id: Annotated[
        int | None,
        Query(ge=1, description="Filter by manufacturer ID"),
    ] = None,
    search: Annotated[
        str | None,
        Query(
            max_length=100,
            description="Case-insensitive manufacturer or model search",
        ),
    ] = None,
    active_only: Annotated[
        bool,
        Query(description="Return only active phones"),
    ] = True,
    database: Session = Depends(get_db),
):
    try:
        return phone_service.list_phones(
            database,
            manufacturer_id,
            search,
            active_only,
        )
    except PhoneServiceError as error:
        _raise_phone_data_unavailable(error)


# Declare this static route before /{phone_id} so "compare" is never parsed as
# a path parameter.
@router.get(
    "/compare",
    response_model=list[PhoneComparisonItem],
    summary="Compare two or three phones",
)
def compare_phones(
    ids: Annotated[
        list[int],
        Query(
            min_length=2,
            max_length=3,
            description="Two or three unique phone IDs; repeat ids= for each",
        ),
    ],
    database: Session = Depends(get_db),
):
    if len(set(ids)) != len(ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Phone IDs must be unique",
        )

    try:
        phones = phone_service.compare_phones(database, ids)
    except PhoneServiceError as error:
        _raise_phone_data_unavailable(error)

    found_ids = {phone["phone_id"] for phone in phones}
    missing_ids = [phone_id for phone_id in ids if phone_id not in found_ids]
    if missing_ids:
        missing = ", ".join(str(phone_id) for phone_id in missing_ids)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phone IDs not found: {missing}",
        )
    return phones


@router.get(
    "/{phone_id}",
    response_model=PhoneDetailResponse,
    summary="Get one phone with sales and promotions",
)
def get_phone_detail(
    phone_id: Annotated[int, Path(ge=1, description="Phone ID")],
    database: Session = Depends(get_db),
):
    try:
        phone = phone_service.get_phone_detail(database, phone_id)
    except PhoneServiceError as error:
        _raise_phone_data_unavailable(error)

    if phone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phone {phone_id} not found",
        )
    return phone
