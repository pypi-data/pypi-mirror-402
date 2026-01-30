"""Get keywords with AssertionEngine support."""

from typing import Any, Optional, List, Dict
from assertionengine import AssertionOperator, dict_verify_assertion

from ..assertions import (
    with_retry_assertion,
    state_assertion_with_retry,
    numeric_assertion_with_retry,
    ElementState,
)
from ..assertions.formatters import apply_formatters, FORMATTERS


class GetterKeywords:
    """Mixin class providing Get keywords with assertion support.

    These keywords follow the Browser Library pattern where assertions
    are built into Get keywords with optional operator and expected value.
    """

    # Configuration (set by main library)
    _assertion_timeout: float = 5.0
    _assertion_interval: float = 0.1

    def get_text(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
        formatters: Optional[List[str]] = None,
    ) -> str:
        """Get element text with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Element locator. See `Locator Syntax`. |
        | ``assertion_operator`` | Optional assertion operator (==, !=, contains, etc.). |
        | ``expected`` | Expected value when using assertion operator. |
        | ``message`` | Custom error message on assertion failure. |
        | ``timeout`` | Assertion retry timeout in seconds. Default from library config. |
        | ``formatters`` | List of formatters: normalize_spaces, strip, lowercase, uppercase. |

        = Return Value =

        Returns ``str``: The text content of the element.

        - Without assertion: Returns the text immediately
        - With assertion operator: Retries until text matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if element not found

        Example:
        | ${text}=    Get Text    JLabel#status
        | Get Text    JLabel#status    ==    Ready
        | Get Text    JLabel#status    contains    Success    timeout=10
        | Get Text    JLabel#msg    matches    \\\\d+ items
        | Get Text    JLabel#title    ==    hello world    formatters=['lowercase', 'strip']

        Supported operators: ==, !=, <, >, <=, >=, contains, not contains,
        starts, ends, matches, validate, then
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Element '{locator}' text"

        formatter_funcs = None
        if formatters:
            # Convert formatter names to functions for AssertionEngine
            formatter_funcs = [FORMATTERS[f] for f in formatters]

        def get_value():
            text = self._lib.get_element_text(locator)
            if formatters:
                text = apply_formatters(text, formatters)
            return text

        return with_retry_assertion(
            get_value,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
            formatter_funcs,
        )

    def get_value(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """Get element value (for input fields) with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Element locator for input field. |
        | ``assertion_operator`` | Optional assertion operator. |
        | ``expected`` | Expected value for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        = Return Value =

        Returns ``str``: The value of the input field.

        - Without assertion: Returns the value immediately
        - With assertion operator: Retries until value matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if element not found

        Example:
        | ${value}=    Get Value    JTextField#username
        | Get Value    JTextField#username    ==    admin
        | Get Value    JTextField#search    contains    query
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Element '{locator}' value"

        def get_val():
            return self._lib.get_element_property(locator, "text")

        return with_retry_assertion(
            get_val,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_element_count(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> int:
        """Get count of matching elements with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Element locator pattern. |
        | ``assertion_operator`` | Optional assertion operator (==, >, <, etc.). |
        | ``expected`` | Expected count for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        = Return Value =

        Returns ``int``: The count of matching elements.

        - Without assertion: Returns the count immediately
        - With assertion operator: Retries until count matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout

        Example:
        | ${count}=    Get Element Count    JButton
        | Get Element Count    JButton    >    0
        | Get Element Count    JTable >> row    ==    5
        | Get Element Count    JButton:enabled    >=    1
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Element count for '{locator}'"

        def get_count():
            elements = self._lib.find_elements(locator)
            return len(elements)

        return numeric_assertion_with_retry(
            get_count,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_element_states(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Optional[List[str]] = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> List[str]:
        """Get element states with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Element locator. |
        | ``assertion_operator`` | Optional assertion operator (contains, ==, etc.). |
        | ``expected`` | Expected states list for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        Returns list of states: visible, hidden, enabled, disabled,
        focused, unfocused, selected, unselected, checked, unchecked,
        editable, readonly, expanded, collapsed, attached, detached.

        = Return Value =

        Returns ``List[str]``: List of element state strings.

        - Without assertion: Returns the states immediately
        - With assertion operator: Retries until states match the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if element not found

        Example:
        | ${states}=    Get Element States    JButton#submit
        | Get Element States    JButton#submit    contains    visible, enabled
        | Get Element States    JTextField#input    not contains    readonly
        | Get Element States    JCheckBox#agree    contains    checked
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Element '{locator}' states"

        def get_states():
            states = ElementState(0)

            # Get visibility
            try:
                visible = self._lib.get_element_property(locator, "visible")
                if visible:
                    states |= ElementState.visible
                else:
                    states |= ElementState.hidden
            except Exception:
                states |= ElementState.detached
                return states

            # Get enabled
            try:
                enabled = self._lib.get_element_property(locator, "enabled")
                if enabled:
                    states |= ElementState.enabled
                else:
                    states |= ElementState.disabled
            except Exception:
                pass

            # Get selected/checked
            try:
                selected = self._lib.get_element_property(locator, "selected")
                if selected:
                    states |= ElementState.selected
                    states |= ElementState.checked
                else:
                    states |= ElementState.unselected
                    states |= ElementState.unchecked
            except Exception:
                pass

            # Get focused
            try:
                focused = self._lib.get_element_property(locator, "focused")
                if focused:
                    states |= ElementState.focused
                else:
                    states |= ElementState.unfocused
            except Exception:
                pass

            # Get editable
            try:
                editable = self._lib.get_element_property(locator, "editable")
                if editable:
                    states |= ElementState.editable
                else:
                    states |= ElementState.readonly
            except Exception:
                pass

            states |= ElementState.attached
            return states

        return state_assertion_with_retry(
            get_states,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_property(
        self,
        locator: str,
        property_name: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """Get element property with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Element locator. |
        | ``property_name`` | Property name (text, enabled, visible, selected, etc.). |
        | ``assertion_operator`` | Optional assertion operator. |
        | ``expected`` | Expected value for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        = Return Value =

        Returns ``Any``: The value of the specified property (type depends on property).

        - Without assertion: Returns the property value immediately
        - With assertion operator: Retries until property matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if element not found

        Example:
        | ${text}=    Get Property    JLabel#title    text
        | Get Property    JButton#save    enabled    ==    ${True}
        | Get Property    JTextField#name    text    contains    John
        | Get Property    JSlider#volume    value    >=    0
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Element '{locator}' property '{property_name}'"

        def get_prop():
            return self._lib.get_element_property(locator, property_name)

        # Check if this is a numeric comparison operator
        numeric_operators = {
            AssertionOperator["<"],
            AssertionOperator[">"],
            AssertionOperator["<="],
            AssertionOperator[">="],
        }

        if assertion_operator in numeric_operators:
            # Use numeric assertion for comparison operators
            return numeric_assertion_with_retry(
                get_prop,
                assertion_operator,
                expected,
                msg,
                message,
                timeout_val,
                self._assertion_interval,
            )

        return with_retry_assertion(
            get_prop,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_properties(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all common element properties.

        | **Argument** | **Description** |
        | ``locator`` | Element locator. |
        | ``assertion_operator`` | Optional assertion operator (==, contains). |
        | ``expected`` | Expected properties dict for assertion. |
        | ``message`` | Custom error message. |

        Returns dict with: name, text, enabled, visible, selected.

        = Return Value =

        Returns ``Dict[str, Any]``: Dictionary of common element properties.

        - Without assertion: Returns the properties immediately
        - With assertion operator: Verifies properties match the assertion immediately (no retry)
        - Raises ``AssertionError`` if assertion fails
        - Raises ``ElementNotFoundError`` if element not found

        Example:
        | ${props}=    Get Properties    JButton#submit
        | Should Be True    ${props}[enabled]
        | Get Properties    JButton#submit    contains    {'enabled': True}
        """
        msg = message or f"Element '{locator}' properties"

        properties = {}
        for prop in ["name", "text", "enabled", "visible", "selected"]:
            try:
                properties[prop] = self._lib.get_element_property(locator, prop)
            except Exception:
                pass

        if assertion_operator is not None:
            dict_verify_assertion(properties, assertion_operator, expected, msg, message)

        return properties

    # Configuration keywords
    def set_assertion_timeout(self, timeout: float) -> float:
        """Set the default assertion timeout.

        | **Argument** | **Description** |
        | ``timeout`` | Timeout in seconds for assertion retries. |

        Returns the previous timeout value.

        Example:
        | ${old}=    Set Assertion Timeout    10
        | # ... operations with 10s timeout ...
        | Set Assertion Timeout    ${old}
        """
        old = self._assertion_timeout
        self._assertion_timeout = timeout
        return old

    def set_assertion_interval(self, interval: float) -> float:
        """Set the assertion retry interval.

        | **Argument** | **Description** |
        | ``interval`` | Interval in seconds between assertion retries. |

        Returns the previous interval value.

        Example:
        | ${old}=    Set Assertion Interval    0.5
        """
        old = self._assertion_interval
        self._assertion_interval = interval
        return old
