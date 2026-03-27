"""Order state machine implementation."""

from __future__ import annotations

from enum import Enum, auto
from typing import Callable

from xianyuflow_common import get_logger

logger = get_logger(__name__)


class OrderState(Enum):
    """Order state enumeration."""

    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class OrderEvent(Enum):
    """Order state transition events."""

    PAY = auto()
    SHIP = auto()
    COMPLETE = auto()
    CANCEL = auto()
    REFUND = auto()


# State transition rules: current_state -> {event: new_state}
TRANSITIONS: dict[OrderState, dict[OrderEvent, OrderState]] = {
    OrderState.PENDING_PAYMENT: {
        OrderEvent.PAY: OrderState.PAID,
        OrderEvent.CANCEL: OrderState.CANCELLED,
    },
    OrderState.PAID: {
        OrderEvent.SHIP: OrderState.SHIPPED,
        OrderEvent.REFUND: OrderState.REFUNDED,
    },
    OrderState.SHIPPED: {
        OrderEvent.COMPLETE: OrderState.COMPLETED,
        OrderEvent.REFUND: OrderState.REFUNDED,
    },
    OrderState.COMPLETED: {
        # Terminal state - no transitions
    },
    OrderState.CANCELLED: {
        # Terminal state - no transitions
    },
    OrderState.REFUNDED: {
        # Terminal state - no transitions
    },
}


class OrderStateMachine:
    """Order state machine for managing order lifecycle."""

    def __init__(self, current_state: OrderState | str = OrderState.PENDING_PAYMENT) -> None:
        """Initialize state machine.

        Args:
            current_state: Initial state of the order.
        """
        if isinstance(current_state, str):
            self._state = OrderState(current_state)
        else:
            self._state = current_state

        self._transitions: dict[OrderEvent, list[Callable]] = {
            event: [] for event in OrderEvent
        }

    @property
    def state(self) -> OrderState:
        """Get current state."""
        return self._state

    @property
    def state_name(self) -> str:
        """Get current state name."""
        return self._state.value

    def can_transition(self, event: OrderEvent) -> bool:
        """Check if transition is allowed.

        Args:
            event: The event to check.

        Returns:
            True if transition is allowed, False otherwise.
        """
        return event in TRANSITIONS.get(self._state, {})

    def get_allowed_transitions(self) -> list[OrderEvent]:
        """Get list of allowed transitions from current state.

        Returns:
            List of allowed events.
        """
        return list(TRANSITIONS.get(self._state, {}).keys())

    def transition(self, event: OrderEvent) -> OrderState:
        """Execute state transition.

        Args:
            event: The event triggering the transition.

        Returns:
            The new state.

        Raises:
            ValueError: If transition is not allowed.
        """
        if not self.can_transition(event):
            allowed = [e.name for e in self.get_allowed_transitions()]
            raise ValueError(
                f"Cannot transition from {self._state.value} with event {event.name}. "
                f"Allowed events: {allowed}"
            )

        new_state = TRANSITIONS[self._state][event]
        old_state = self._state

        # Execute pre-transition callbacks
        for callback in self._transitions.get(event, []):
            try:
                callback(old_state, new_state, event)
            except Exception as e:
                logger.error(f"Transition callback failed: {e}")

        self._state = new_state
        logger.info(
            f"Order state transitioned: {old_state.value} -> {new_state.value} "
            f"(event: {event.name})"
        )

        return new_state

    def on_transition(self, event: OrderEvent, callback: Callable) -> None:
        """Register a callback for a transition event.

        Args:
            event: The event to listen for.
            callback: Function to call on transition.
                   Signature: callback(old_state, new_state, event)
        """
        if event not in self._transitions:
            self._transitions[event] = []
        self._transitions[event].append(callback)

    def pay(self) -> OrderState:
        """Transition to PAID state."""
        return self.transition(OrderEvent.PAY)

    def ship(self) -> OrderState:
        """Transition to SHIPPED state."""
        return self.transition(OrderEvent.SHIP)

    def complete(self) -> OrderState:
        """Transition to COMPLETED state."""
        return self.transition(OrderEvent.COMPLETE)

    def cancel(self) -> OrderState:
        """Transition to CANCELLED state."""
        return self.transition(OrderEvent.CANCEL)

    def refund(self) -> OrderState:
        """Transition to REFUNDED state."""
        return self.transition(OrderEvent.REFUND)

    def is_terminal(self) -> bool:
        """Check if current state is terminal."""
        return self._state in {
            OrderState.COMPLETED,
            OrderState.CANCELLED,
            OrderState.REFUNDED,
        }

    def to_dict(self) -> dict:
        """Convert state machine to dictionary."""
        return {
            "state": self._state.value,
            "is_terminal": self.is_terminal(),
            "allowed_transitions": [e.name for e in self.get_allowed_transitions()],
        }
