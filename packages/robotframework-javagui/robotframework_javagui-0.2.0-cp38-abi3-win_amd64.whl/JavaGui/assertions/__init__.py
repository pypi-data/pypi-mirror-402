"""AssertionEngine integration for JavaGui library."""

from typing import Any, Optional, List, Callable, TypeVar
from enum import Flag, auto
import time

from assertionengine import (
    AssertionOperator,
    verify_assertion,
    flag_verify_assertion,
    float_str_verify_assertion,
    list_verify_assertion,
    dict_verify_assertion,
)

from .security import (
    SecureExpressionEvaluator,
    ExpressionSecurityError,
    secure_evaluate,
    validate_expression,
    is_expression_safe,
)

__all__ = [
    "AssertionOperator",
    "ElementState",
    "with_retry_assertion",
    "verify_with_retry",
    "numeric_assertion_with_retry",
    "state_assertion_with_retry",
    "AssertionConfig",
    # Security exports
    "SecureExpressionEvaluator",
    "ExpressionSecurityError",
    "secure_evaluate",
    "validate_expression",
    "is_expression_safe",
]


class ElementState(Flag):
    """Element state flags for assertions."""

    visible = auto()
    hidden = auto()
    enabled = auto()
    disabled = auto()
    focused = auto()
    unfocused = auto()
    selected = auto()
    unselected = auto()
    checked = auto()
    unchecked = auto()
    editable = auto()
    readonly = auto()
    expanded = auto()
    collapsed = auto()
    attached = auto()
    detached = auto()

    @classmethod
    def from_string(cls, state: str) -> "ElementState":
        """Convert string to ElementState."""
        return cls[state.lower().strip()]

    @classmethod
    def from_strings(cls, states: List[str]) -> "ElementState":
        """Convert list of strings to combined ElementState."""
        result = cls(0)
        for state in states:
            result |= cls.from_string(state)
        return result

    def to_list(self) -> List[str]:
        """Convert to list of state names."""
        return [flag.name for flag in type(self) if flag in self and flag.name]


class AssertionConfig:
    """Configuration for assertion behavior."""

    def __init__(
        self,
        timeout: float = 5.0,
        interval: float = 0.1,
        message_prefix: str = "",
    ):
        self.timeout = timeout
        self.interval = interval
        self.message_prefix = message_prefix


T = TypeVar("T")


def with_retry_assertion(
    get_value_func: Callable[[], T],
    operator: Optional[AssertionOperator],
    expected: Any,
    message: str = "",
    custom_message: Optional[str] = None,
    timeout: float = 5.0,
    interval: float = 0.1,
    formatters: Optional[list] = None,
) -> T:
    """Execute assertion with retry until timeout.

    Args:
        get_value_func: Function that returns the value to assert
        operator: AssertionOperator or None (return value only)
        expected: Expected value for assertion
        message: Prefix message for error
        custom_message: Custom error message
        timeout: Maximum time to retry (seconds)
        interval: Time between retries (seconds)
        formatters: Optional list of formatters

    Returns:
        The actual value (after formatters applied)

    Raises:
        AssertionError: If assertion fails after timeout
    """
    if operator is None:
        # No assertion, just return value
        return get_value_func()

    end_time = time.time() + timeout
    last_error = None
    last_value = None

    while time.time() < end_time:
        try:
            value = get_value_func()
            last_value = value
            return verify_assertion(
                value, operator, expected, message, custom_message, formatters
            )
        except AssertionError as e:
            last_error = e
            time.sleep(interval)
        except Exception as e:
            # Non-assertion errors (element not found, etc.) - retry
            last_error = AssertionError(f"{message} {e}")
            time.sleep(interval)

    # Timeout reached - raise last error with context
    if last_error:
        raise AssertionError(
            f"{last_error}\n"
            f"Assertion failed after {timeout}s timeout. "
            f"Last value was: {last_value!r}"
        )
    raise AssertionError(f"Assertion timed out after {timeout}s")


# Alias for backward compatibility
verify_with_retry = with_retry_assertion


def state_assertion_with_retry(
    get_states_func: Callable[[], ElementState],
    operator: Optional[AssertionOperator],
    expected: List[str],
    message: str = "",
    custom_message: Optional[str] = None,
    timeout: float = 5.0,
    interval: float = 0.1,
) -> List[str]:
    """Execute state assertion with retry using flag_verify_assertion.

    Returns list of state names.
    """
    if operator is None:
        states = get_states_func()
        return states.to_list()

    end_time = time.time() + timeout
    last_error = None
    last_states = None

    while time.time() < end_time:
        try:
            states = get_states_func()
            last_states = states
            flag_verify_assertion(states, operator, expected, message, custom_message)
            return states.to_list()
        except AssertionError as e:
            last_error = e
            time.sleep(interval)
        except Exception as e:
            last_error = AssertionError(f"{message} {e}")
            time.sleep(interval)

    if last_error:
        raise AssertionError(
            f"{last_error}\n"
            f"State assertion failed after {timeout}s timeout. "
            f"Last states: {last_states.to_list() if last_states else 'unknown'}"
        )
    raise AssertionError(f"State assertion timed out after {timeout}s")


def numeric_assertion_with_retry(
    get_value_func: Callable[[], int],
    operator: Optional[AssertionOperator],
    expected: Any,
    message: str = "",
    custom_message: Optional[str] = None,
    timeout: float = 5.0,
    interval: float = 0.1,
) -> int:
    """Execute numeric assertion with retry using float_str_verify_assertion."""
    if operator is None:
        return get_value_func()

    end_time = time.time() + timeout
    last_error = None
    last_value = None

    while time.time() < end_time:
        try:
            value = get_value_func()
            last_value = value
            float_str_verify_assertion(
                float(value), operator, expected, message, custom_message
            )
            return value
        except AssertionError as e:
            last_error = e
            time.sleep(interval)
        except Exception as e:
            last_error = AssertionError(f"{message} {e}")
            time.sleep(interval)

    if last_error:
        raise AssertionError(
            f"{last_error}\n"
            f"Numeric assertion failed after {timeout}s timeout. "
            f"Last value was: {last_value}"
        )
    raise AssertionError(f"Numeric assertion timed out after {timeout}s")
