"""Virtual goods service for code delivery and verification."""

from __future__ import annotations

import secrets
import string
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from xianyuflow_common import get_logger

from app.models import Order, VirtualGoodsCode
from app.state_machine import OrderEvent, OrderState, OrderStateMachine

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


class VirtualGoodsError(Exception):
    """Base exception for virtual goods operations."""

    pass


class NoAvailableCodeError(VirtualGoodsError):
    """Raised when no available codes in inventory."""

    pass


class CodeAlreadyUsedError(VirtualGoodsError):
    """Raised when trying to use an already used code."""

    pass


class InvalidCodeError(VirtualGoodsError):
    """Raised when code is invalid."""

    pass


class OrderNotPaidError(VirtualGoodsError):
    """Raised when trying to deliver to unpaid order."""

    pass


class VirtualGoodsService:
    """Service for managing virtual goods codes."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session

    async def deliver_code(self, order_id: int) -> VirtualGoodsCode:
        """Deliver a virtual goods code to an order.

        Args:
            order_id: The order ID to deliver to.

        Returns:
            The delivered virtual goods code.

        Raises:
            OrderNotPaidError: If order is not in PAID state.
            NoAvailableCodeError: If no codes available in inventory.
        """
        # Get order
        result = await self.session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()

        if not order:
            raise VirtualGoodsError(f"Order {order_id} not found")

        # Check order state
        if order.status != OrderState.PAID.value:
            raise OrderNotPaidError(
                f"Cannot deliver to order in {order.status} state. "
                f"Order must be in PAID state."
            )

        # Check if order already has a code
        result = await self.session.execute(
            select(VirtualGoodsCode).where(
                VirtualGoodsCode.order_id == order_id,
                VirtualGoodsCode.used == False,  # noqa: E712
            )
        )
        existing_code = result.scalar_one_or_none()
        if existing_code:
            logger.info(f"Order {order_id} already has code {existing_code.id}")
            return existing_code

        # Find available code from inventory
        result = await self.session.execute(
            select(VirtualGoodsCode).where(
                VirtualGoodsCode.order_id.is_(None),
                VirtualGoodsCode.used == False,  # noqa: E712
            )
        )
        available_code = result.scalar_one_or_none()

        if not available_code:
            raise NoAvailableCodeError("No available codes in inventory")

        # Assign code to order
        available_code.order_id = order_id
        await self.session.flush()

        # Update order state to SHIPPED
        state_machine = OrderStateMachine(order.status)
        state_machine.ship()
        order.status = state_machine.state_name

        logger.info(f"Delivered code {available_code.id} to order {order_id}")
        return available_code

    async def verify_code(self, order_id: int, code: str) -> VirtualGoodsCode:
        """Verify and consume a virtual goods code.

        Args:
            order_id: The order ID.
            code: The code to verify.

        Returns:
            The verified code record.

        Raises:
            InvalidCodeError: If code is invalid.
            CodeAlreadyUsedError: If code was already used.
        """
        # Find the code
        result = await self.session.execute(
            select(VirtualGoodsCode).where(
                VirtualGoodsCode.order_id == order_id,
                VirtualGoodsCode.code == code,
            )
        )
        code_record = result.scalar_one_or_none()

        if not code_record:
            raise InvalidCodeError("Invalid code for this order")

        if code_record.used:
            raise CodeAlreadyUsedError("Code has already been used")

        # Mark as used
        code_record.used = True
        code_record.used_at = datetime.utcnow()

        # Update order to COMPLETED
        result = await self.session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one()

        state_machine = OrderStateMachine(order.status)
        if state_machine.can_transition(OrderEvent.COMPLETE):
            state_machine.complete()
            order.status = state_machine.state_name
            logger.info(f"Order {order_id} completed after code verification")

        logger.info(f"Verified code {code_record.id} for order {order_id}")
        return code_record

    async def replenish_inventory(
        self, codes: list[str] | None = None, count: int = 10
    ) -> list[VirtualGoodsCode]:
        """Add new codes to inventory.

        Args:
            codes: List of codes to add. If None, generates random codes.
            count: Number of codes to generate if codes is None.

        Returns:
            List of created code records.
        """
        if codes is None:
            codes = [self._generate_code() for _ in range(count)]

        created_codes = []
        for code in codes:
            # Check if code already exists
            result = await self.session.execute(
                select(VirtualGoodsCode).where(VirtualGoodsCode.code == code)
            )
            if result.scalar_one_or_none():
                logger.warning(f"Code already exists, skipping: {code}")
                continue

            code_record = VirtualGoodsCode(code=code)
            self.session.add(code_record)
            created_codes.append(code_record)

        await self.session.flush()
        logger.info(f"Added {len(created_codes)} codes to inventory")
        return created_codes

    async def get_inventory_count(self) -> dict:
        """Get inventory statistics.

        Returns:
            Dictionary with inventory counts.
        """
        # Total available (not assigned)
        result = await self.session.execute(
            select(VirtualGoodsCode).where(VirtualGoodsCode.order_id.is_(None))
        )
        available = len(result.scalars().all())

        # Total assigned but not used
        result = await self.session.execute(
            select(VirtualGoodsCode).where(
                VirtualGoodsCode.order_id.isnot(None),
                VirtualGoodsCode.used == False,  # noqa: E712
            )
        )
        assigned_unused = len(result.scalars().all())

        # Total used
        result = await self.session.execute(
            select(VirtualGoodsCode).where(VirtualGoodsCode.used == True)  # noqa: E712
        )
        used = len(result.scalars().all())

        return {
            "available": available,
            "assigned_unused": assigned_unused,
            "used": used,
            "total": available + assigned_unused + used,
        }

    async def get_order_code(self, order_id: int) -> VirtualGoodsCode | None:
        """Get the code assigned to an order.

        Args:
            order_id: The order ID.

        Returns:
            The code record or None if not found.
        """
        result = await self.session.execute(
            select(VirtualGoodsCode).where(VirtualGoodsCode.order_id == order_id)
        )
        return result.scalar_one_or_none()

    def _generate_code(self, length: int = 16) -> str:
        """Generate a random code.

        Args:
            length: Length of the code.

        Returns:
            Generated code string.
        """
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))
