from __future__ import annotations

from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    REAL,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Manufacturer(Base):
    __tablename__ = "manufacturer"

    manufacturer_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    country: Mapped[Optional[str]] = mapped_column(Text)
    website: Mapped[Optional[str]] = mapped_column(Text)

    phones: Mapped[list[Phone]] = relationship(back_populates="manufacturer")


class Phone(Base):
    __tablename__ = "phone"
    __table_args__ = (
        CheckConstraint("storage_gb > 0"),
        CheckConstraint("ram_gb > 0"),
        CheckConstraint("launch_price >= 0"),
        CheckConstraint("is_active IN (0, 1)"),
        UniqueConstraint("manufacturer_id", "model_name", "storage_gb"),
        Index("idx_phone_manufacturer", "manufacturer_id"),
    )

    phone_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    manufacturer_id: Mapped[int] = mapped_column(
        ForeignKey("manufacturer.manufacturer_id"),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    release_date: Mapped[Optional[str]] = mapped_column(Text)
    storage_gb: Mapped[Optional[int]] = mapped_column(Integer)
    ram_gb: Mapped[Optional[int]] = mapped_column(Integer)
    launch_price: Mapped[Optional[float]] = mapped_column(REAL)
    operating_system: Mapped[str] = mapped_column(Text, nullable=False)
    image_path: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[Optional[int]] = mapped_column(
        Integer,
        server_default=text("1"),
    )

    manufacturer: Mapped[Manufacturer] = relationship(back_populates="phones")
    purchases: Mapped[list[Purchase]] = relationship(back_populates="phone")
    promotions: Mapped[list[Promotion]] = relationship(back_populates="phone")


class User(Base):
    __tablename__ = "user"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_name: Mapped[str] = mapped_column(Text, nullable=False)
    date_of_birth: Mapped[Optional[str]] = mapped_column(Text)
    gender: Mapped[Optional[str]] = mapped_column(Text)
    occupation: Mapped[Optional[str]] = mapped_column(Text)
    income_range: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    contact: Mapped[Optional[UserContact]] = relationship(
        back_populates="user",
        uselist=False,
        passive_deletes=True,
    )
    purchases: Mapped[list[Purchase]] = relationship(back_populates="user")


class UserContact(Base):
    __tablename__ = "user_contact"

    contact_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "user.user_id",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )
    email: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    phone_number: Mapped[Optional[str]] = mapped_column(Text)
    street: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(Text)
    state: Mapped[Optional[str]] = mapped_column(Text)
    zip_code: Mapped[Optional[str]] = mapped_column(Text)
    country: Mapped[Optional[str]] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="contact")


class Purchase(Base):
    __tablename__ = "purchase"
    __table_args__ = (
        CheckConstraint("sale_price >= 0"),
        CheckConstraint("quantity > 0"),
        CheckConstraint(
            "phone_status IN "
            "('PRIMARY', 'SECONDARY', 'PREVIOUS', 'RETURNED', 'TRADED_IN')"
        ),
        Index("idx_purchase_user", "user_id"),
        Index("idx_purchase_phone", "phone_id"),
        Index("idx_purchase_date", "purchase_date"),
    )

    purchase_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.user_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    phone_id: Mapped[int] = mapped_column(
        ForeignKey("phone.phone_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    purchase_date: Mapped[str] = mapped_column(Text, nullable=False)
    sale_price: Mapped[float] = mapped_column(REAL, nullable=False)
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("1"),
    )
    phone_status: Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped[User] = relationship(back_populates="purchases")
    phone: Mapped[Phone] = relationship(back_populates="purchases")
    purchase_promotions: Mapped[list[PurchasePromotion]] = relationship(
        back_populates="purchase",
        passive_deletes=True,
    )


class Promotion(Base):
    __tablename__ = "promotion"
    __table_args__ = (
        CheckConstraint("discount_type IN ('PERCENTAGE', 'FIXED')"),
        CheckConstraint("discount_value > 0"),
        CheckConstraint("end_date >= start_date"),
        CheckConstraint("is_active IN (0, 1)"),
        Index("idx_promotion_phone", "phone_id"),
    )

    promotion_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone_id: Mapped[int] = mapped_column(
        ForeignKey("phone.phone_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    promo_code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    promo_name: Mapped[str] = mapped_column(Text, nullable=False)
    discount_type: Mapped[str] = mapped_column(Text, nullable=False)
    discount_value: Mapped[float] = mapped_column(REAL, nullable=False)
    start_date: Mapped[str] = mapped_column(Text, nullable=False)
    end_date: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("1"),
    )

    phone: Mapped[Phone] = relationship(back_populates="promotions")
    purchase_promotions: Mapped[list[PurchasePromotion]] = relationship(
        back_populates="promotion"
    )


class PurchasePromotion(Base):
    __tablename__ = "purchase_promotion"
    __table_args__ = (
        CheckConstraint("discount_amount >= 0"),
        UniqueConstraint("purchase_id", "promotion_id"),
        Index("idx_purchase_promotion_purchase", "purchase_id"),
        Index("idx_purchase_promotion_promotion", "promotion_id"),
    )

    purchase_promo_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_id: Mapped[int] = mapped_column(
        ForeignKey(
            "purchase.purchase_id",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    promotion_id: Mapped[int] = mapped_column(
        ForeignKey(
            "promotion.promotion_id",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    discount_amount: Mapped[float] = mapped_column(
        REAL,
        nullable=False,
        server_default=text("0"),
    )

    purchase: Mapped[Purchase] = relationship(back_populates="purchase_promotions")
    promotion: Mapped[Promotion] = relationship(
        back_populates="purchase_promotions"
    )


class Admin(Base):
    __tablename__ = "admin"
    __table_args__ = (CheckConstraint("is_active IN (0, 1)"),)

    admin_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("1"),
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey(
            "admin.admin_id",
            onupdate="CASCADE",
            ondelete="SET NULL",
        )
    )
    created_at: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    created_by_admin: Mapped[Optional[Admin]] = relationship(
        remote_side=[admin_id],
        foreign_keys=[created_by],
        back_populates="created_admins",
    )
    created_admins: Mapped[list[Admin]] = relationship(
        foreign_keys=[created_by],
        back_populates="created_by_admin",
        passive_deletes=True,
    )
