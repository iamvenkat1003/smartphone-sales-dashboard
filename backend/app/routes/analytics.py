from typing import Annotated, Literal, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import (
    AnalyticsKPIResponse,
    CustomerInsightsResponse,
    ManufacturerPerformanceItem,
    PromotionAnalyticsItem,
    SalesTrendItem,
    TopPhoneItem,
)
from app.services import analytics_service
from app.services.analytics_service import AnalyticsServiceError


router = APIRouter()


def _raise_analytics_unavailable(error: AnalyticsServiceError) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Analytics data is temporarily unavailable",
    ) from error


@router.get(
    "/kpis",
    response_model=AnalyticsKPIResponse,
    summary="Get dashboard KPI totals",
)
def get_kpis(database: Session = Depends(get_db)):
    try:
        return analytics_service.get_kpis(database)
    except AnalyticsServiceError as error:
        _raise_analytics_unavailable(error)


@router.get(
    "/top-phones",
    response_model=list[TopPhoneItem],
    summary="Rank phones by units or revenue",
)
def get_top_phones(
    metric: Annotated[
        Literal["units", "revenue"],
        Query(description="Ranking metric: units sold or revenue"),
    ] = "units",
    limit: Annotated[
        int,
        Query(ge=1, le=20, description="Number of phones to return"),
    ] = 5,
    database: Session = Depends(get_db),
):
    try:
        return analytics_service.get_top_phones(database, metric, limit)
    except AnalyticsServiceError as error:
        _raise_analytics_unavailable(error)


@router.get(
    "/manufacturers",
    response_model=list[ManufacturerPerformanceItem],
    summary="Get manufacturer sales performance",
)
def get_manufacturers(database: Session = Depends(get_db)):
    try:
        return analytics_service.get_manufacturer_performance(database)
    except AnalyticsServiceError as error:
        _raise_analytics_unavailable(error)


@router.get(
    "/sales-trend",
    response_model=list[SalesTrendItem],
    summary="Get monthly sales trends",
)
def get_sales_trend(database: Session = Depends(get_db)):
    try:
        return analytics_service.get_sales_trend(database)
    except AnalyticsServiceError as error:
        _raise_analytics_unavailable(error)


@router.get(
    "/promotions",
    response_model=list[PromotionAnalyticsItem],
    summary="Get promotion usage and associated sales",
)
def get_promotions(database: Session = Depends(get_db)):
    try:
        return analytics_service.get_promotion_analytics(database)
    except AnalyticsServiceError as error:
        _raise_analytics_unavailable(error)


@router.get(
    "/customers",
    response_model=CustomerInsightsResponse,
    summary="Get aggregate customer purchasing insights",
)
def get_customer_insights(database: Session = Depends(get_db)):
    try:
        return analytics_service.get_customer_insights(database)
    except AnalyticsServiceError as error:
        _raise_analytics_unavailable(error)
