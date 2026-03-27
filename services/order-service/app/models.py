"""SQLAlchemy models for order service."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from xianyuflow_common.database import Base

if TYPE_CHECKING:
    pass


class Order(Base):
    """Order model for storing order information."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    xianyu_order_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="闲鱼订单ID",
    )
    buyer_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="买家ID",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PENDING_PAYMENT",
        index=True,
        comment="订单状态",
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="订单金额",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )

    # Relationships
    virtual_goods_codes: Mapped[list[VirtualGoodsCode]] = relationship(
        "VirtualGoodsCode",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, xianyu_order_id={self.xianyu_order_id}, status={self.status})>"


class VirtualGoodsCode(Base):
    """Virtual goods code model for storing and managing virtual product codes."""

    __tablename__ = "virtual_goods_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="关联订单ID",
    )
    code: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="卡密代码",
    )
    used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已使用",
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="使用时间",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )

    # Relationships
    order: Mapped[Order | None] = relationship(
        "Order",
        back_populates="virtual_goods_codes",
    )

    def __repr__(self) -> str:
        return f"<VirtualGoodsCode(id={self.id}, used={self.used})>"
