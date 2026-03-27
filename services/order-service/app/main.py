"""
Order Service - FastAPI Application
订单处理和虚拟商品核销服务
"""

import os
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Any, AsyncIterator

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from xianyuflow_common import (
    HealthCheckResponse,
    KafkaClient,
    TOPICS,
    get_logger,
)
from xianyuflow_common.config import (
    DatabaseConfig,
    KafkaConfig,
    ServiceConfig,
)
from xianyuflow_common.database import Database

from app.models import Order, VirtualGoodsCode
from app.state_machine import OrderState, OrderStateMachine
from app.virtual_goods import (
    CodeAlreadyUsedError,
    InvalidCodeError,
    NoAvailableCodeError,
    OrderNotPaidError,
    VirtualGoodsError,
    VirtualGoodsService,
)

logger = get_logger(__name__)

# Global instances
db: Database
kafka_client: KafkaClient | None = None


# Pydantic models for API
class OrderCreateRequest(BaseModel):
    """Request model for creating an order."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "xianyu_order_id": "XY202403270001",
            "buyer_id": "buyer_12345",
            "amount": 99.99,
        }
    })

    xianyu_order_id: str = Field(..., description="闲鱼订单ID")
    buyer_id: str = Field(..., description="买家ID")
    amount: Decimal = Field(..., ge=0, description="订单金额")


class OrderResponse(BaseModel):
    """Response model for order."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    xianyu_order_id: str
    buyer_id: str
    status: str
    amount: Decimal
    created_at: str
    updated_at: str


class OrderStatusUpdateRequest(BaseModel):
    """Request model for updating order status."""

    status: str = Field(..., description="新状态")


class StatusResponse(BaseModel):
    """Response model for status update."""

    order_id: int
    previous_status: str
    current_status: str
    allowed_transitions: list[str]


class VirtualGoodsDeliverRequest(BaseModel):
    """Request model for delivering virtual goods."""

    order_id: int = Field(..., description="订单ID")


class VirtualGoodsDeliverResponse(BaseModel):
    """Response model for virtual goods delivery."""

    order_id: int
    code_id: int
    delivered: bool
    message: str


class VirtualGoodsVerifyRequest(BaseModel):
    """Request model for verifying virtual goods code."""

    order_id: int = Field(..., description="订单ID")
    code: str = Field(..., description="卡密代码")


class VirtualGoodsVerifyResponse(BaseModel):
    """Response model for virtual goods verification."""

    order_id: int
    verified: bool
    used_at: str | None
    message: str


class InventoryResponse(BaseModel):
    """Response model for inventory status."""

    available: int
    assigned_unused: int
    used: int
    total: int


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependency to get database session."""
    async with db.session() as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan management."""
    global db, kafka_client

    # Initialize database
    db_config = DatabaseConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        name=os.getenv("DB_NAME", "xianyuflow"),
        user=os.getenv("DB_USER", "xianyuflow"),
        password=os.getenv("DB_PASSWORD", ""),
    )
    if not db_config.password:
        logger.warning("DB_PASSWORD not set — using local SQLite fallback")
    db = Database(db_config)
    await db.connect()
    logger.info("Database connected")

    # Initialize Kafka client if configured
    kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    if kafka_bootstrap:
        kafka_config = KafkaConfig(
            bootstrap_servers=kafka_bootstrap,
            client_id="order-service",
        )
        kafka_client = KafkaClient(kafka_config)
        await kafka_client.connect()
        logger.info("Kafka client connected")

        # Start consuming orders.paid topic
        await kafka_client.start_consumer(
            TOPICS["orders.paid"],
            group_id="order-service",
            message_handler=_handle_order_paid,
        )

    yield

    # Cleanup
    if kafka_client:
        await kafka_client.disconnect()
        logger.info("Kafka client disconnected")

    await db.disconnect()
    logger.info("Database disconnected")


async def _handle_order_paid(message: dict[str, Any]) -> None:
    """Handle order paid event from Kafka.

    Args:
        message: The Kafka message containing order paid event.
    """
    try:
        xianyu_order_id = message.get("xianyu_order_id")
        if not xianyu_order_id:
            logger.warning("Received order paid event without xianyu_order_id")
            return

        async with db.session() as session:
            # Find the order
            result = await session.execute(
                select(Order).where(Order.xianyu_order_id == xianyu_order_id)
            )
            order = result.scalar_one_or_none()

            if not order:
                logger.warning(f"Order not found: {xianyu_order_id}")
                return

            # Update order status to PAID
            if order.status == OrderState.PENDING_PAYMENT.value:
                state_machine = OrderStateMachine(order.status)
                state_machine.pay()
                order.status = state_machine.state_name
                logger.info(f"Order {order.id} marked as PAID via Kafka event")
            else:
                logger.info(f"Order {order.id} already in {order.status} state")

    except Exception as e:
        logger.error(f"Failed to handle order paid event: {e}")


app = FastAPI(
    title="Order Service",
    description="XianyuFlow Order Service - 订单处理和虚拟商品核销",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Health check endpoint."""
    return HealthCheckResponse(
        status="ok",
        version="0.1.0",
    )


@app.post("/api/v1/orders", response_model=OrderResponse)
async def create_order(
    request: OrderCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> Order:
    """Create a new order."""
    # Check if order already exists
    result = await session.execute(
        select(Order).where(Order.xianyu_order_id == request.xianyu_order_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Order with xianyu_order_id {request.xianyu_order_id} already exists",
        )

    order = Order(
        xianyu_order_id=request.xianyu_order_id,
        buyer_id=request.buyer_id,
        amount=request.amount,
        status=OrderState.PENDING_PAYMENT.value,
    )
    session.add(order)
    await session.flush()

    logger.info(f"Created order {order.id} for buyer {request.buyer_id}")
    return order


@app.get("/api/v1/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
) -> Order:
    """Get order by ID."""
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order


@app.post("/api/v1/orders/{order_id}/status", response_model=StatusResponse)
async def update_order_status(
    order_id: int,
    request: OrderStatusUpdateRequest,
    session: AsyncSession = Depends(get_session),
) -> StatusResponse:
    """Update order status."""
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    previous_status = order.status

    try:
        # Validate new status
        new_state = OrderState(request.status)

        # Create state machine and attempt transition
        state_machine = OrderStateMachine(order.status)

        # Find the event that leads to the desired state
        event = None
        for e, target in TRANSITIONS.get(state_machine.state, {}).items():
            if target == new_state:
                event = e
                break

        if event is None:
            allowed = [t.value for t in state_machine.get_allowed_transitions()]
            raise HTTPException(
                status_code=400,
                detail=f"Cannot transition to {request.status}. Allowed: {allowed}",
            )

        state_machine.transition(event)
        order.status = state_machine.state_name

        logger.info(f"Order {order_id} status: {previous_status} -> {order.status}")

        return StatusResponse(
            order_id=order_id,
            previous_status=previous_status,
            current_status=order.status,
            allowed_transitions=[e.name for e in state_machine.get_allowed_transitions()],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Import TRANSITIONS for status update
from app.state_machine import TRANSITIONS


@app.post("/api/v1/virtual-goods/deliver", response_model=VirtualGoodsDeliverResponse)
async def deliver_virtual_goods(
    request: VirtualGoodsDeliverRequest,
    session: AsyncSession = Depends(get_session),
) -> VirtualGoodsDeliverResponse:
    """Deliver virtual goods code to an order."""
    service = VirtualGoodsService(session)

    try:
        code = await service.deliver_code(request.order_id)
        return VirtualGoodsDeliverResponse(
            order_id=request.order_id,
            code_id=code.id,
            delivered=True,
            message="Virtual goods code delivered successfully",
        )
    except OrderNotPaidError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NoAvailableCodeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except VirtualGoodsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/virtual-goods/verify", response_model=VirtualGoodsVerifyResponse)
async def verify_virtual_goods(
    request: VirtualGoodsVerifyRequest,
    session: AsyncSession = Depends(get_session),
) -> VirtualGoodsVerifyResponse:
    """Verify and consume virtual goods code."""
    service = VirtualGoodsService(session)

    try:
        code = await service.verify_code(request.order_id, request.code)
        return VirtualGoodsVerifyResponse(
            order_id=request.order_id,
            verified=True,
            used_at=code.used_at.isoformat() if code.used_at else None,
            message="Code verified successfully",
        )
    except InvalidCodeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CodeAlreadyUsedError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except VirtualGoodsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/virtual-goods/inventory", response_model=InventoryResponse)
async def get_inventory(
    session: AsyncSession = Depends(get_session),
) -> InventoryResponse:
    """Get virtual goods inventory status."""
    service = VirtualGoodsService(session)
    inventory = await service.get_inventory_count()
    return InventoryResponse(**inventory)


@app.post("/api/v1/virtual-goods/inventory/replenish")
async def replenish_inventory(
    count: int = 10,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Replenish virtual goods inventory with generated codes."""
    service = VirtualGoodsService(session)
    codes = await service.replenish_inventory(count=count)
    return {
        "added": len(codes),
        "message": f"Added {len(codes)} codes to inventory",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )
