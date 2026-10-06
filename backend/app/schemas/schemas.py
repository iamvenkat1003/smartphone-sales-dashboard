from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class ApiStatusResponse(BaseModel):
    name: str
    status: str


class HealthResponse(BaseModel):
    status: str
    database: str


class AnalyticsKPIResponse(BaseModel):
    total_customers: int
    total_transactions: int
    total_units_sold: int
    total_revenue: float
    average_selling_price: float


class TopPhoneItem(BaseModel):
    phone_id: int
    manufacturer: str
    model_name: str
    units_sold: int
    revenue: float
    average_selling_price: float
    image_path: Optional[str]


class ManufacturerPerformanceItem(BaseModel):
    manufacturer_id: int
    manufacturer_name: str
    units_sold: int
    revenue: float
    unit_share_percentage: float


class SalesTrendItem(BaseModel):
    month: str
    transactions: int
    units_sold: int
    revenue: float


class PromotionAnalyticsItem(BaseModel):
    promotion_id: int
    promo_code: str
    promo_name: str
    manufacturer: str
    phone_model: str
    times_used: int
    units_sold: int
    associated_revenue: float
    total_discount_amount: float


class CustomerInsightsResponse(BaseModel):
    total_customers: int
    repeat_customers: int
    repeat_customer_percentage: float
    multi_phone_customers: int
    multi_manufacturer_customers: int
    multi_manufacturer_percentage: float
    average_units_per_customer: float


class PhoneListItem(BaseModel):
    phone_id: int
    manufacturer_id: int
    manufacturer_name: str
    model_name: str
    release_date: Optional[str]
    storage_gb: Optional[int]
    ram_gb: Optional[int]
    launch_price: Optional[float]
    operating_system: str
    image_path: Optional[str]
    is_active: Optional[int]
    units_sold: int
    revenue: float
    average_selling_price: Optional[float]


class PhonePromotionItem(BaseModel):
    promotion_id: int
    promo_code: str
    promo_name: str
    discount_type: str
    discount_value: float
    start_date: str
    end_date: str
    description: Optional[str]
    is_active: int
    times_used: int


class PhoneDetailResponse(BaseModel):
    phone_id: int
    manufacturer_id: int
    manufacturer_name: str
    model_name: str
    release_date: Optional[str]
    storage_gb: Optional[int]
    ram_gb: Optional[int]
    launch_price: Optional[float]
    operating_system: str
    image_path: Optional[str]
    is_active: Optional[int]
    transactions: int
    units_sold: int
    revenue: float
    average_selling_price: Optional[float]
    promotions: list[PhonePromotionItem]


class PhoneComparisonItem(BaseModel):
    phone_id: int
    manufacturer: str
    model_name: str
    release_date: Optional[str]
    storage_gb: Optional[int]
    ram_gb: Optional[int]
    launch_price: Optional[float]
    operating_system: str
    image_path: Optional[str]
    transactions: int
    units_sold: int
    revenue: float
    average_selling_price: Optional[float]
    promotion_uses: int


class AdminPublic(BaseModel):
    admin_id: int
    first_name: str
    last_name: str
    email: str
    is_active: int
    created_by: Optional[int]
    created_by_name: Optional[str] = None
    created_at: str


class AdminLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=72)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"]
    admin: AdminPublic


class AdminCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=72)

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("email")
    @classmethod
    def normalize_admin_email(cls, value: str) -> str:
        return value.strip().lower()


class StatusUpdate(BaseModel):
    is_active: Literal[0, 1]


class PhoneAdminCreate(BaseModel):
    manufacturer_id: int = Field(ge=1)
    model_name: str = Field(min_length=1, max_length=150)
    release_date: Optional[str] = None
    storage_gb: int = Field(gt=0)
    ram_gb: int = Field(gt=0)
    launch_price: float = Field(ge=0)
    operating_system: str = Field(min_length=1, max_length=100)
    image_path: Optional[str] = None
    is_active: Literal[0, 1] = 1

    @field_validator("model_name", "operating_system")
    @classmethod
    def strip_phone_text(cls, value: str) -> str:
        return value.strip()


class PhoneAdminUpdate(BaseModel):
    manufacturer_id: Optional[int] = Field(default=None, ge=1)
    model_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    release_date: Optional[str] = None
    storage_gb: Optional[int] = Field(default=None, gt=0)
    ram_gb: Optional[int] = Field(default=None, gt=0)
    launch_price: Optional[float] = Field(default=None, ge=0)
    operating_system: Optional[str] = Field(default=None, min_length=1, max_length=100)
    image_path: Optional[str] = None


class PromotionAdminCreate(BaseModel):
    phone_id: int = Field(ge=1)
    promo_code: str = Field(min_length=1, max_length=100)
    promo_name: str = Field(min_length=1, max_length=150)
    discount_type: Literal["PERCENTAGE", "FIXED"]
    discount_value: float = Field(gt=0)
    start_date: str = Field(min_length=1)
    end_date: str = Field(min_length=1)
    description: Optional[str] = None
    is_active: Literal[0, 1] = 1

    @field_validator("promo_code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

    @model_validator(mode="after")
    def validate_promotion(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if self.discount_type == "PERCENTAGE" and self.discount_value > 100:
            raise ValueError("percentage discounts cannot exceed 100")
        return self


class PromotionAdminUpdate(BaseModel):
    phone_id: Optional[int] = Field(default=None, ge=1)
    promo_code: Optional[str] = Field(default=None, min_length=1, max_length=100)
    promo_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    discount_type: Optional[Literal["PERCENTAGE", "FIXED"]] = None
    discount_value: Optional[float] = Field(default=None, gt=0)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None

    @field_validator("promo_code")
    @classmethod
    def normalize_optional_code(cls, value: Optional[str]) -> Optional[str]:
        return value.strip().upper() if value else value


class CustomerAdminUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    income_range: Optional[str] = None
    email: Optional[str] = Field(default=None, max_length=254)
    phone_number: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None


class PurchasePromotionInput(BaseModel):
    promotion_id: int = Field(ge=1)
    discount_amount: float = Field(default=0, ge=0)


class PurchaseAdminCreate(BaseModel):
    user_id: int = Field(ge=1)
    phone_id: int = Field(ge=1)
    purchase_date: str = Field(min_length=1)
    sale_price: float = Field(ge=0)
    quantity: int = Field(default=1, gt=0)
    phone_status: Literal[
        "PRIMARY", "SECONDARY", "PREVIOUS", "RETURNED", "TRADED_IN"
    ]
    promotions: list[PurchasePromotionInput] = Field(default_factory=list, max_length=2)

    @field_validator("promotions")
    @classmethod
    def unique_promotions(cls, value: list[PurchasePromotionInput]):
        ids = [item.promotion_id for item in value]
        if len(ids) != len(set(ids)):
            raise ValueError("promotion IDs must be unique")
        return value


class PurchaseAdminUpdate(BaseModel):
    user_id: Optional[int] = Field(default=None, ge=1)
    phone_id: Optional[int] = Field(default=None, ge=1)
    purchase_date: Optional[str] = Field(default=None, min_length=1)
    sale_price: Optional[float] = Field(default=None, ge=0)
    quantity: Optional[int] = Field(default=None, gt=0)
    phone_status: Optional[
        Literal["PRIMARY", "SECONDARY", "PREVIOUS", "RETURNED", "TRADED_IN"]
    ] = None
    promotions: Optional[list[PurchasePromotionInput]] = Field(
        default=None,
        max_length=2,
    )

    @field_validator("promotions")
    @classmethod
    def unique_optional_promotions(
        cls,
        value: Optional[list[PurchasePromotionInput]],
    ):
        if value is not None:
            ids = [item.promotion_id for item in value]
            if len(ids) != len(set(ids)):
                raise ValueError("promotion IDs must be unique")
        return value
