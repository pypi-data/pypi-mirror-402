"""SWT Get keywords with AssertionEngine support."""

from typing import Any, Optional, List, Dict

try:
    from assertionengine import AssertionOperator, dict_verify_assertion
except ImportError:
    AssertionOperator = None
    dict_verify_assertion = None

from ..assertions import (
    with_retry_assertion,
    state_assertion_with_retry,
    numeric_assertion_with_retry,
    ElementState,
)


class SwtGetterKeywords:
    """Mixin class providing SWT Get keywords with assertion support.

    These keywords follow the Browser Library pattern where assertions
    are built into Get keywords with optional operator and expected value.
    """

    # Configuration (set by main library)
    _assertion_timeout: float = 5.0
    _assertion_interval: float = 0.1

    def get_widget_text(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """Get SWT widget text with optional assertion.
=Argument=    =Description=        ``locator``    Widget locator. See `Locator Syntax`.
``assertion_operator``    Optional assertion operator (==, !=, contains, etc.).        ``expected``    Expected value when using assertion operator.
``message``    Custom error message on assertion failure.        ``timeout``    Assertion retry timeout in seconds. Default from library config.
        = Return Value =

        Returns ``str``: The text content of the SWT widget.

        - Without assertion: Returns the text immediately
        - With assertion operator: Retries until text matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if widget not found

        Example:
        ${text}=    Get Widget Text    Label#status         Get Widget Text | Label#status | == | Ready | |
Get Widget Text    Label#status    contains    Success    timeout=10
Get Widget Text    Text#input    matches    \\\\d+ items    
        Supported operators: ==, !=, <, >, <=, >=, contains, not contains,
        starts, ends, matches, validate, then
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Widget '{locator}' text"

        def get_value():
            # Use find_widget to get the widget and extract text property
            widget = self._lib.find_widget(locator)
            # Get text via property - SWT widgets commonly have getText()
            try:
                return self._lib.get_widget_property(locator, "text")
            except Exception:
                # Fallback to widget's text attribute if available
                return getattr(widget, "text", "")

        return with_retry_assertion(
            get_value,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_widget_count(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> int:
        """Get count of matching SWT widgets with optional assertion.
=Argument=    =Description=        ``locator``    Widget locator pattern.
``assertion_operator``    Optional assertion operator (==, >, <, etc.).        ``expected``    Expected count for assertion.
``message``    Custom error message.        ``timeout``    Assertion timeout in seconds.
        = Return Value =

        Returns ``int``: The count of matching SWT widgets.

        - Without assertion: Returns the count immediately
        - With assertion operator: Retries until count matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout

        Example:
        ${count}=    Get Widget Count    Button         Get Widget Count | Button | > | 0 | |
Get Widget Count    Table >> row    ==    5    
Get Widget Count    Button:enabled    >=    1    
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Widget count for '{locator}'"

        def get_count():
            widgets = self._lib.find_widgets(locator)
            return len(widgets)

        return numeric_assertion_with_retry(
            get_count,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_widget_property(
        self,
        locator: str,
        property_name: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """Get SWT widget property with optional assertion.
=Argument=    =Description=        ``locator``    Widget locator.
``property_name``    Property name (text, enabled, visible, selection, etc.).        ``assertion_operator``    Optional assertion operator.
``expected``    Expected value for assertion.        ``message``    Custom error message.
``timeout``    Assertion timeout in seconds.    = Return Value =

        Returns ``Any``: The value of the specified widget property (type depends on property).

        - Without assertion: Returns the property value immediately
        - With assertion operator: Retries until property matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if widget not found

        Example:
        ${text}=    Get Widget Property    Label#title    text    
Get Widget Property    Button#save    enabled    ==    ${True}    
Get Widget Property    Text#name    text    contains    John    
Get Widget Property    Combo#country    selectionIndex    >=    0    
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Widget '{locator}' property '{property_name}'"

        def get_prop():
            return self._lib.get_widget_property(locator, property_name)

        return with_retry_assertion(
            get_prop,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def is_widget_enabled(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> bool:
        """Check if SWT widget is enabled with optional assertion.    =Argument=    =Description=
``locator``    Widget locator.        ``assertion_operator``    Optional assertion operator (==, !=).
``expected``    Expected boolean value for assertion.        ``message``    Custom error message.
``timeout``    Assertion timeout in seconds.
        = Return Value =

        Returns ``bool``: True if widget is enabled, False otherwise.

        - Without assertion: Returns the state immediately
        - With assertion operator: Retries until state matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if widget not found

        Example:
        ${enabled}=    Is Widget Enabled    Button#submit         Is Widget Enabled | Button#submit | == | ${True} | |
Is Widget Enabled    Button#next    ==    ${False}    
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Widget '{locator}' enabled state"

        def get_enabled():
            try:
                return self._lib.get_widget_property(locator, "enabled")
            except Exception:
                # Try isEnabled if property access fails
                widget = self._lib.find_widget(locator)
                return getattr(widget, "enabled", True)

        return with_retry_assertion(
            get_enabled,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def is_widget_visible(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> bool:
        """Check if SWT widget is visible with optional assertion.
=Argument=    =Description=        ``locator``    Widget locator.
``assertion_operator``    Optional assertion operator (==, !=).        ``expected``    Expected boolean value for assertion.
``message``    Custom error message.        ``timeout``    Assertion timeout in seconds.
        = Return Value =

        Returns ``bool``: True if widget is visible, False otherwise.

        - Without assertion: Returns the state immediately
        - With assertion operator: Retries until state matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if widget not found

        Example:
        ${visible}=    Is Widget Visible    Shell#main         Is Widget Visible | Group#options | == | ${True} | |
Is Widget Visible    Label#error    ==    ${False}    
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Widget '{locator}' visible state"

        def get_visible():
            try:
                return self._lib.get_widget_property(locator, "visible")
            except Exception:
                # Try isVisible if property access fails
                widget = self._lib.find_widget(locator)
                return getattr(widget, "visible", True)

        return with_retry_assertion(
            get_visible,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def is_widget_focused(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> bool:
        """Check if SWT widget has focus with optional assertion.
=Argument=    =Description=        ``locator``    Widget locator.
``assertion_operator``    Optional assertion operator (==, !=).        ``expected``    Expected boolean value for assertion.
``message``    Custom error message.        ``timeout``    Assertion timeout in seconds.
        = Return Value =

        Returns ``bool``: True if widget has focus, False otherwise.

        - Without assertion: Returns the state immediately
        - With assertion operator: Retries until state matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if widget not found

        Example:
        ${focused}=    Is Widget Focused    Text#input         Is Widget Focused | Text#username | == | ${True} | |
Is Widget Focused    Button#cancel    ==    ${False}    
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Widget '{locator}' focused state"

        def get_focused():
            try:
                return self._lib.get_widget_property(locator, "focused")
            except Exception:
                # Fallback - check if widget is the focus control
                widget = self._lib.find_widget(locator)
                return getattr(widget, "focused", False)

        return with_retry_assertion(
            get_focused,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_widget_states(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Optional[List[str]] = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> List[str]:
        """Get SWT widget states with optional assertion.
=Argument=    =Description=        ``locator``    Widget locator.
``assertion_operator``    Optional assertion operator (contains, ==, etc.).        ``expected``    Expected states list for assertion.
``message``    Custom error message.        ``timeout``    Assertion timeout in seconds.
        Returns list of states: visible, hidden, enabled, disabled,
        focused, unfocused, selected, unselected, checked, unchecked,
        editable, readonly, attached, detached.

        = Return Value =

        Returns ``List[str]``: List of SWT widget state strings.

        - Without assertion: Returns the states immediately
        - With assertion operator: Retries until states match the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if widget not found

        Example:
        ${states}=    Get Widget States    Button#submit         Get Widget States | Button#submit | contains | visible, enabled | |
Get Widget States    Text#input    not contains    readonly    
Get Widget States    Button#check    contains    checked    
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Widget '{locator}' states"

        def get_states():
            states = ElementState(0)

            # Get visibility
            try:
                visible = self._lib.get_widget_property(locator, "visible")
                if visible:
                    states |= ElementState.visible
                else:
                    states |= ElementState.hidden
            except Exception:
                states |= ElementState.detached
                return states

            # Get enabled
            try:
                enabled = self._lib.get_widget_property(locator, "enabled")
                if enabled:
                    states |= ElementState.enabled
                else:
                    states |= ElementState.disabled
            except Exception:
                pass

            # Get selection state (for checkboxes, radio buttons)
            try:
                selection = self._lib.get_widget_property(locator, "selection")
                if selection:
                    states |= ElementState.selected
                    states |= ElementState.checked
                else:
                    states |= ElementState.unselected
                    states |= ElementState.unchecked
            except Exception:
                pass

            # Get focused
            try:
                focused = self._lib.get_widget_property(locator, "focused")
                if focused:
                    states |= ElementState.focused
                else:
                    states |= ElementState.unfocused
            except Exception:
                pass

            # Get editable (for Text widgets)
            try:
                editable = self._lib.get_widget_property(locator, "editable")
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

    def get_widget_properties(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all common SWT widget properties.
=Argument=    =Description=        ``locator``    Widget locator.
``assertion_operator``    Optional assertion operator (==, contains).        ``expected``    Expected properties dict for assertion.
``message``    Custom error message.    Returns dict with: text, enabled, visible, data (widget data), toolTipText.

        = Return Value =

        Returns ``Dict[str, Any]``: Dictionary of common SWT widget properties.

        - Without assertion: Returns the properties immediately (no retry)
        - With assertion operator: Verifies properties match the assertion immediately (no retry)
        - Raises ``AssertionError`` if assertion fails
        - Raises ``ElementNotFoundError`` if widget not found

        Example:
        ${props}=    Get Widget Properties    Button#submit         Should Be True    ${props}[enabled]        
Get Widget Properties    Button#submit    contains    {'enabled': True}    
        """
        msg = message or f"Widget '{locator}' properties"

        properties = {}
        prop_names = ["text", "enabled", "visible", "data", "toolTipText"]

        for prop in prop_names:
            try:
                properties[prop] = self._lib.get_widget_property(locator, prop)
            except Exception:
                pass

        if assertion_operator is not None and dict_verify_assertion is not None:
            dict_verify_assertion(properties, assertion_operator, expected, msg, message)

        return properties

    # Configuration keywords
    def set_swt_assertion_timeout(self, timeout: float) -> float:
        """Set the default assertion timeout for SWT keywords.
=Argument=    =Description=        ``timeout``    Timeout in seconds for assertion retries.
        Returns the previous timeout value.

        Example:
        ${old}=    Set Swt Assertion Timeout    10        # ... operations with 10s timeout ... Set Swt Assertion Timeout | ${old} |
        """
        old = self._assertion_timeout
        self._assertion_timeout = timeout
        return old

    def set_swt_assertion_interval(self, interval: float) -> float:
        """Set the assertion retry interval for SWT keywords.
=Argument=    =Description=
``interval``    Interval in seconds between assertion retries.    Returns the previous interval value.

        Example:    ${old}=    Set Swt Assertion Interval    0.5
        """
        old = self._assertion_interval
        self._assertion_interval = interval
        return old
