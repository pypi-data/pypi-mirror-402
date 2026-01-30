"""Robot Framework JavaGUI Library - High-performance automation for Java GUI applications.

This library provides comprehensive support for automating Java Swing, SWT, and
Eclipse RCP applications with Robot Framework. It features:

- CSS/XPath-like locator syntax for finding UI elements
- High-performance Rust core with Python bindings
- Support for Swing, SWT, and Eclipse RCP toolkits
- Bundled Java agent JAR for easy setup
- Full Robot Framework keyword integration

Basic Usage:
    *** Settings ***
    Library    JavaGui.Swing

    *** Test Cases ***
    Click Submit Button
        Connect To Application    MyApp
        Click Element    JButton#submit
        Disconnect

For SWT applications:
    *** Settings ***
    Library    JavaGui.Swt

For Eclipse RCP applications:
    *** Settings ***
    Library    JavaGui.Swt    WITH NAME    SWT
    Library    JavaGui.Rcp    WITH NAME    RCP
"""

import os
import sys
from typing import Any, Dict, List, Optional, Union

# AssertionEngine integration imports
try:
    from assertionengine import AssertionOperator

    from JavaGui.assertions import AssertionConfig, ElementState
    from JavaGui.keywords import (
        GetterKeywords,
        ListKeywords,
        RcpKeywords,
        SwtGetterKeywords,
        SwtTableKeywords,
        SwtTreeKeywords,
        TableKeywords,
        TreeKeywords,
    )

    _ASSERTION_ENGINE_AVAILABLE = True
except ImportError:
    _ASSERTION_ENGINE_AVAILABLE = False
    AssertionOperator = None
    GetterKeywords = object
    TableKeywords = object
    TreeKeywords = object
    ListKeywords = object
    RcpKeywords = object
    SwtGetterKeywords = object
    SwtTableKeywords = object
    SwtTreeKeywords = object

# Deprecation system imports
try:
    from JavaGui.deprecation import (
        DeprecatedKeywordWarning,
        create_keyword_alias,
        deprecated,
        get_alias_registry,
    )

    _DEPRECATION_AVAILABLE = True
except ImportError:
    _DEPRECATION_AVAILABLE = False
    deprecated = None
    DeprecatedKeywordWarning = None

# Path to bundled Java agent JAR
_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_JAR_PATH = os.path.join(_PACKAGE_DIR, "jars", "javagui-agent.jar")


def get_agent_jar_path() -> str:
    """Get the path to the bundled Java agent JAR file.

    Returns:
        str: Absolute path to the Java agent JAR file.

    Raises:
        FileNotFoundError: If the agent JAR is not found (incomplete installation).

    Example:
        >>> from JavaGui import get_agent_jar_path
        >>> agent_jar = get_agent_jar_path()
        >>> # Use: java -javaagent:{agent_jar}=port=5678 -jar your-app.jar

    """
    if not os.path.exists(AGENT_JAR_PATH):
        raise FileNotFoundError(
            f"Agent JAR not found at {AGENT_JAR_PATH}. "
            "This may indicate an incomplete installation."
        )
    return AGENT_JAR_PATH


# Import the Rust core module
try:
    from JavaGui._core import (
        ActionFailedError,
        ElementNotFoundError,
        LocatorParseError,
        MultipleElementsFoundError,
        SwingConnectionError,
    )
    from JavaGui._core import (
        RcpLibrary as _RcpLibrary,
    )
    from JavaGui._core import (
        SwingElement as _SwingElement,
    )
    from JavaGui._core import (
        SwingLibrary as _SwingLibrary,
    )
    from JavaGui._core import (
        SwtElement as _SwtElement,
    )
    from JavaGui._core import (
        SwtLibrary as _SwtLibrary,
    )
    from JavaGui._core import (
        TimeoutError as SwingTimeoutError,
    )

    # Aliases for backwards compatibility
    SwingError = SwingConnectionError
    ConnectionError = SwingConnectionError
    _RUST_AVAILABLE = True
except ImportError as e:
    _RUST_AVAILABLE = False
    _IMPORT_ERROR = str(e)


__version__ = "0.1.0"
__all__ = [
    # Main library classes (preferred names)
    "Swing",
    "Swt",
    "Rcp",
    # Legacy names for backwards compatibility
    "SwingLibrary",
    "SwingElement",
    "SwtLibrary",
    "SwtElement",
    "RcpLibrary",
    # Agent JAR utilities
    "get_agent_jar_path",
    "AGENT_JAR_PATH",
    # Exceptions
    "SwingError",
    "ConnectionError",
    "ElementNotFoundError",
    "SwingTimeoutError",
    # Robot Framework metadata
    "ROBOT_LIBRARY_DOC_FORMAT",
    "ROBOT_LIBRARY_SCOPE",
    "ROBOT_LIBRARY_VERSION",
    # AssertionEngine exports
    "AssertionOperator",
    "ElementState",
    # Deprecation exports
    "deprecated",
    "DeprecatedKeywordWarning",
]

# Re-export SWT/RCP classes with public names
if _RUST_AVAILABLE:
    SwtLibrary = _SwtLibrary
    SwtElement = _SwtElement
    RcpLibrary = _RcpLibrary
else:
    SwtLibrary = None
    SwtElement = None
    RcpLibrary = None


# Preferred class aliases for Robot Framework usage:
# Library    JavaGui.Swing
# Library    JavaGui.Swt
# Library    JavaGui.Rcp
# NOTE: We use Python wrapper classes (defined below) instead of the Rust classes directly
# because Robot Framework needs to introspect __init__ signatures, which PyO3 classes don't expose properly.

ROBOT_LIBRARY_SCOPE = "GLOBAL"
ROBOT_LIBRARY_VERSION = __version__


class SwingLibrary(GetterKeywords, TableKeywords, TreeKeywords, ListKeywords):
    r"""Robot Framework library for Java Swing application automation.

    This library provides keywords for automating Java Swing desktop applications.
    It supports advanced locator syntax including CSS selectors and XPath.

    **Initialization**

    The library can be imported with optional default timeout:

    | **Setting** | **Value** |
    | Library | swing_library.SwingLibrary |
    | Library | swing_library.SwingLibrary | timeout=30 |

    **Locator Syntax**

    The library supports multiple locator strategies:

    *CSS-like Selectors*

    | *Selector* | *Description* | *Example* |
    | Type | Match by class name | JButton |
    | #id | Match by name | #submitBtn |
    | .class | Match by class | .primary |
    | [attr=value] | Match by attribute | [text='Save'] |
    | :pseudo | Match by state | :enabled |
    | > | Child combinator | JPanel > JButton |
    | (space) | Descendant combinator | JFrame JButton |

    *XPath Selectors*

    | *Selector* | *Description* | *Example* |
    | //Type | Descendant | //JButton |
    | /Type | Child | /JPanel/JButton |
    | [@attr='val'] | Attribute match | //JButton[@text='OK'] |
    | [n] | Index | //JButton[1] |

    **Assertion Keywords**

    Get keywords support inline assertions following the Browser Library pattern:

    | *Keyword* | *Example* |
    | Get Text | Get Text \| JLabel#status \| == \| Ready |
    | Get Element Count | Get Element Count \| JButton \| > \| 0 |
    | Get Element States | Get Element States \| JButton \| contains \| visible, enabled |
    | Get Table Cell Value | Get Table Cell Value \| JTable \| 0 \| Name \| == \| John |

    Supported operators: ==, !=, <, >, <=, >=, contains, not contains,
    starts, ends, matches, validate, then
    """

    ROBOT_LIBRARY_SCOPE = "GLOBAL"
    ROBOT_LIBRARY_VERSION = __version__

    def __init__(
        self,
        timeout: float = 10.0,
        poll_interval: float = 0.5,
        screenshot_directory: str = ".",
    ) -> None:
        """Initialize the Swing Library.

        | **Argument** | **Description** |
        | ``timeout`` | Default timeout in seconds for wait operations. Default ``10.0``. |
        | ``poll_interval`` | Polling interval in seconds for wait operations. Default ``0.5``. |
        | ``screenshot_directory`` | Directory to save screenshots. Default ``.`` (current). |

        Example:
        | **Setting** | **Value** | **Value** |
        | Library | swing_library.SwingLibrary | |
        | Library | swing_library.SwingLibrary | timeout=30 |

        """
        if not _RUST_AVAILABLE:
            raise ImportError(
                f"Swing Library Rust core not available: {_IMPORT_ERROR}\n"
                "Please ensure the library is properly installed with: pip install robotframework-swing"
            )

        self._lib = _SwingLibrary(
            timeout=timeout,
            poll_interval=poll_interval,
            screenshot_directory=screenshot_directory,
        )
        self._timeout = timeout

        # AssertionEngine configuration
        self._assertion_timeout = 5.0
        self._assertion_interval = 0.1

    # ==========================================================================
    # Connection Keywords
    # ==========================================================================

    def connect_to_application(
        self,
        application: str = "",
        pid: Optional[int] = None,
        main_class: Optional[str] = None,
        title: Optional[str] = None,
        host: str = "localhost",
        port: int = 5678,
        timeout: Optional[float] = None,
    ) -> None:
        """Connect to a running Java Swing application.

        Connects to a JVM running a Swing application. The target application
        can be identified by name, process ID, main class name, or window title.

        | **Argument** | **Description** |
        | ``application`` | Application identifier (name, pid, main_class, or title). |
        | ``pid`` | Process ID of the target JVM (alternative to application). |
        | ``main_class`` | Fully qualified or simple name of the main class. |
        | ``title`` | Window title pattern (supports wildcards with ``*``). |
        | ``host`` | Host where the agent is running. Default ``localhost``. |
        | ``port`` | Port the agent is listening on. Default ``5678``. |
        | ``timeout`` | Connection timeout in seconds. Uses library default if not set. |

        Example:
        | Connect To Application    MyApp
        | Connect To Application    main_class=com.example.MyApp
        | Connect To Application    title=*Main Window*
        | Connect To Application    application=MyApp    host=localhost    port=5678

        """
        # Build application identifier from various options
        app_id = application
        if not app_id:
            if pid:
                app_id = str(pid)
            elif main_class:
                app_id = main_class
            elif title:
                app_id = title
            else:
                app_id = "default"

        timeout_val = timeout if timeout is not None else self._timeout
        self._lib.connect_to_application(app_id, host, port, timeout_val)

    def disconnect(self) -> None:
        """Disconnect from the current application.

        Closes the connection to the Swing application and cleans up resources.
        This should be called in test teardown.

        Example:
        | Connect To Application    MyApp
        | # ... perform test actions ...
        | Disconnect

        """
        self._lib.disconnect_from_application()

    def is_connected(self) -> bool:
        """Check if connected to an application.

        Returns ``True`` if currently connected to a Swing application,
        ``False`` otherwise.

        Example:
        | ${connected}=    Is Connected
        | Should Be True    ${connected}

        """
        return self._lib.is_connected()

    def get_connection_info(self) -> Dict[str, Any]:
        """Get information about the current connection.

        Returns a dictionary containing connection details such as host, port,
        and application identifier.

        Example:
        | ${info}=    Get Connection Info
        | Log    Connected to: ${info}[host]:${info}[port]

        """
        return self._lib.get_connection_info()

    # ==========================================================================
    # Element Finding Keywords
    # ==========================================================================

    def find_element(self, locator: str) -> "_SwingElement":
        """Find a single element matching the locator.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |

        Returns a ``SwingElement`` matching the locator.

        Raises ``ElementNotFoundError`` if no element matches the locator.

        Example:
        | ${button}=    Find Element    JButton#submit
        | ${field}=    Find Element    //JTextField[@name='username']

        """
        return self._lib.find_element(locator)

    def find_elements(self, locator: str) -> List["_SwingElement"]:
        """Find all elements matching the locator.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |

        Returns a list of ``SwingElement`` objects matching the locator.
        Returns an empty list if no elements match.

        Example:
        | ${buttons}=    Find Elements    JButton
        | Length Should Be    ${buttons}    5

        """
        return self._lib.find_elements(locator)

    def wait_until_element_exists(
        self,
        locator: str,
        timeout: Optional[float] = None,
    ) -> None:
        """Wait until an element exists in the UI tree.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |
        | ``timeout`` | Maximum wait time in seconds. Uses library default if not set. |

        Raises ``TimeoutError`` if element does not exist within timeout.

        Example:
        | Wait Until Element Exists    JButton#submit
        | Wait Until Element Exists    JButton#submit    timeout=30

        """
        timeout_val = timeout if timeout is not None else self._timeout
        self._lib.wait_until_element_exists(locator, timeout_val)

    def wait_until_element_does_not_exist(
        self,
        locator: str,
        timeout: Optional[float] = None,
    ) -> None:
        """Wait until an element no longer exists in the UI tree.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |
        | ``timeout`` | Maximum wait time in seconds. Uses library default if not set. |

        Raises ``TimeoutError`` if element still exists after timeout.

        Example:
        | Wait Until Element Does Not Exist    JDialog#loading
        | Wait Until Element Does Not Exist    JDialog#loading    timeout=60

        """
        timeout_val = timeout if timeout is not None else self._timeout
        self._lib.wait_until_element_does_not_exist(locator, timeout_val)

    # ==========================================================================
    # Click Keywords
    # ==========================================================================

    def click(self, locator: str) -> None:
        """Click on an element.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |

        Performs a single left-click on the element.

        Example:
        | Click    JButton#submit
        | Click    //JButton[@text='OK']

        """
        self._lib.click_element(locator, click_count=1)

    def click_element(self, locator: str, click_count: int = 1) -> None:
        """Click on an element with specified click count.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |
        | ``click_count`` | Number of clicks. ``1`` for single click, ``2`` for double click. Default ``1``. |

        Example:
        | Click Element    JButton#submit
        | Click Element    JTable    click_count=2

        """
        self._lib.click_element(locator, click_count=click_count)

    def double_click(self, locator: str) -> None:
        """Double-click on an element.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |

        Performs a double left-click on the element. Useful for opening items
        in tables, lists, or trees.

        Example:
        | Double Click    JTable
        | Double Click    JList#items

        """
        self._lib.click_element(locator, click_count=2)

    def click_button(self, locator: str) -> None:
        """Click a button element.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string for the button. See `Locator Syntax`. |

        Specialized click for ``JButton`` components. Ensures the element
        is a button before clicking.

        Example:
        | Click Button    JButton#submit
        | Click Button    #okButton

        """
        self._lib.click_button(locator)

    # ==========================================================================
    # Input Keywords
    # ==========================================================================

    def input_text(self, locator: str, text: str, clear: bool = True) -> None:
        """Input text into a text field.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |
        | ``text`` | Text to input into the field. |
        | ``clear`` | Whether to clear existing text first. Default ``True``. |

        When ``clear`` is ``True``, any existing text is removed before typing.
        Set ``clear=False`` to append to existing text.

        Example:
        | Input Text    #username    testuser
        | Input Text    JTextField:first-child    Hello World
        | Input Text    #field    append this    clear=False

        """
        self._lib.input_text(locator, text, clear=clear)

    def clear_text(self, locator: str) -> None:
        """Clear text from a text field.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |

        Removes all text from the specified text field.

        Example:
        | Clear Text    #searchField
        | Clear Text    JTextField#input

        """
        self._lib.clear_text(locator)

    # ==========================================================================
    # Selection Keywords
    # ==========================================================================

    def select_from_combobox(self, locator: str, value: str) -> None:
        """Select an item from a combo box.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator for the ``JComboBox``. See `Locator Syntax`. |
        | ``value`` | Item text to select from the dropdown. |

        Example:
        | Select From Combobox    #countryCombo    United States
        | Select From Combobox    JComboBox#language    English

        """
        self._lib.select_from_combobox(locator, value)

    def check_checkbox(self, locator: str) -> None:
        """Check a checkbox.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator for the ``JCheckBox``. See `Locator Syntax`. |

        Sets the checkbox to checked state. If already checked, does nothing.

        Example:
        | Check Checkbox    #rememberMe
        | Check Checkbox    JCheckBox#acceptTerms

        """
        self._lib.check_checkbox(locator)

    def uncheck_checkbox(self, locator: str) -> None:
        """Uncheck a checkbox.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator for the ``JCheckBox``. See `Locator Syntax`. |

        Sets the checkbox to unchecked state. If already unchecked, does nothing.

        Example:
        | Uncheck Checkbox    #newsletter
        | Uncheck Checkbox    JCheckBox#sendUpdates

        """
        self._lib.uncheck_checkbox(locator)

    def select_radio_button(self, locator: str) -> None:
        """Select a radio button.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator for the ``JRadioButton``. See `Locator Syntax`. |

        Selects the specified radio button within its button group.

        Example:
        | Select Radio Button    #optionA
        | Select Radio Button    JRadioButton#male

        """
        self._lib.select_radio_button(locator)

    # ==========================================================================
    # Table Keywords
    # ==========================================================================
    # Note: get_table_cell_value, get_table_row_count, get_table_column_count
    # are inherited from TableKeywords mixin with assertion support.
    # See python/JavaGui/keywords/tables.py for their implementation.

    def select_table_cell(self, locator: str, row: int, column: int) -> None:
        """Select a table cell.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator for the ``JTable``. See `Locator Syntax`. |
        | ``row`` | Row index (0-based). |
        | ``column`` | Column index (0-based). |

        Selects (clicks) the specified cell in the table.

        Example:
        | Select Table Cell    #dataTable    2    3
        | Select Table Cell    JTable#users    0    0

        """
        self._lib.select_table_cell(locator, row, column)

    def select_table_row(self, locator: str, row: int) -> None:
        """Select a table row.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator for the ``JTable``. See `Locator Syntax`. |
        | ``row`` | Row index (0-based). |

        Selects the entire row in the table.

        Example:
        | Select Table Row    #dataTable    2
        | Select Table Row    JTable#users    0

        """
        self._lib.select_table_row(locator, row)

    # ==========================================================================
    # Tree Keywords
    # ==========================================================================

    def expand_tree_node(self, locator: str, path: str) -> None:
        """Expand a tree node.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator for the ``JTree``. See `Locator Syntax`. |
        | ``path`` | Node path separated by ``/`` or ``|`` (pipe). |

        Expands the tree node at the specified path, making child nodes visible.

        Example:
        | Expand Tree Node    JTree    Root/Folder/Subfolder
        | Expand Tree Node    JTree    Root|Folder|Subfolder
        | Expand Tree Node    #fileTree    Documents

        """
        # Convert pipe separator to slash for Java agent compatibility
        normalized_path = path.replace("    ", "/")
        self._lib.expand_tree_node(locator, normalized_path)

    def collapse_tree_node(self, locator: str, path: str) -> None:
        """Collapse a tree node.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator for the ``JTree``. See `Locator Syntax`. |
        | ``path`` | Node path separated by ``/`` or ``|`` (pipe). |

        Collapses the tree node at the specified path, hiding child nodes.

        Example:
        | Collapse Tree Node    #fileTree    Documents/Downloads
        | Collapse Tree Node    JTree    Root|Folder

        """
        # Convert pipe separator to slash for Java agent compatibility
        normalized_path = path.replace("|", "/")
        self._lib.collapse_tree_node(locator, normalized_path)

    def select_tree_node(self, locator: str, path: str) -> None:
        """Select a tree node.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator for the ``JTree``. See `Locator Syntax`. |
        | ``path`` | Node path separated by ``/`` or ``|`` (pipe). |

        Selects (highlights) the tree node at the specified path.

        Example:
        | Select Tree Node    JTree    Root/Config/Settings
        | Select Tree Node    JTree    Root|Config|Settings
        | Select Tree Node    #projectTree    src/main/java

        """
        # Convert pipe separator to slash for Java agent compatibility
        normalized_path = path.replace("    ", "/")
        self._lib.select_tree_node(locator, normalized_path)

    def get_selected_tree_node(self, locator: str) -> Optional[str]:
        """Get the currently selected tree node path.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator for the ``JTree``. See `Locator Syntax`. |

        Returns the path of the currently selected node, or ``None`` if no node is selected.

        Example:
        | ${path}=    Get Selected Tree Node    JTree
        | Should Be Equal    ${path}    Root/Config/Settings

        """
        return self._lib.get_selected_tree_node(locator)

    # ==========================================================================
    # Menu Keywords
    # ==========================================================================

    def select_menu(self, menu_path: str) -> None:
        """Select a menu item from the menu bar.

        | **Argument** | **Description** |
        | ``menu_path`` | Menu path separated by ``|`` (pipe character). |

        Navigates through the menu hierarchy and clicks the final item.

        Example:
        | Select Menu    File    New
        | Select Menu    Edit|Copy
        | Select Menu    File    Export    As PDF

        """
        self._lib.select_menu(menu_path)

    def select_from_popup_menu(self, menu_path: str) -> None:
        """Select an item from a popup/context menu.

        | **Argument** | **Description** |
        | ``menu_path`` | Menu path separated by ``|`` (pipe character). |

        Use after right-clicking to open a context menu. Navigates through
        the popup menu hierarchy and clicks the final item.

        Example:
        | Right Click    JTree#files
        | Select From Popup Menu    Copy
        | Select From Popup Menu    Edit    Paste

        """
        self._lib.select_from_popup_menu(menu_path)

    # ==========================================================================
    # Wait Keywords
    # ==========================================================================

    def wait_until_element_is_visible(
        self,
        locator: str,
        timeout: Optional[float] = None,
    ) -> None:
        """Wait until an element becomes visible.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |
        | ``timeout`` | Maximum wait time in seconds. Uses library default if not set. |

        Waits until the element exists and is visible (not hidden).
        Raises ``TimeoutError`` if element is not visible within timeout.

        Example:
        | Wait Until Element Is Visible    JLabel#status
        | Wait Until Element Is Visible    JLabel#status    timeout=15

        """
        timeout_val = timeout if timeout is not None else self._timeout
        self._lib.wait_until_element_is_visible(locator, timeout_val)

    def wait_until_element_is_enabled(
        self,
        locator: str,
        timeout: Optional[float] = None,
    ) -> None:
        """Wait until an element becomes enabled.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |
        | ``timeout`` | Maximum wait time in seconds. Uses library default if not set. |

        Waits until the element is enabled and can receive user input.
        Raises ``TimeoutError`` if element is not enabled within timeout.

        Example:
        | Wait Until Element Is Enabled    JButton#next
        | Wait Until Element Is Enabled    JButton#next    timeout=10

        """
        timeout_val = timeout if timeout is not None else self._timeout
        self._lib.wait_until_element_is_enabled(locator, timeout_val)

    # ==========================================================================
    # Verification Keywords
    # ==========================================================================

    def element_should_be_visible(self, locator: str) -> None:
        """Verify that an element is visible.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |

        Fails if the element is not visible.

        Example:
        | Element Should Be Visible    JPanel#main
        | Element Should Be Visible    #loginForm

        """
        self._lib.element_should_be_visible(locator)

    def element_should_not_be_visible(self, locator: str) -> None:
        """Verify that an element is not visible.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |

        Fails if the element is visible.

        Example:
        | Element Should Not Be Visible    JDialog#loading
        | Element Should Not Be Visible    #errorPanel

        """
        self._lib.element_should_not_be_visible(locator)

    def element_should_be_enabled(self, locator: str) -> None:
        """Verify that an element is enabled.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |

        Fails if the element is disabled.

        Example:
        | Element Should Be Enabled    JButton#save
        | Element Should Be Enabled    #submitBtn

        """
        self._lib.element_should_be_enabled(locator)

    def element_should_be_disabled(self, locator: str) -> None:
        """Verify that an element is disabled.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |

        Fails if the element is enabled.

        Example:
        | Element Should Be Disabled    JButton#next
        | Element Should Be Disabled    #deleteBtn

        """
        self._lib.element_should_be_disabled(locator)

    def get_element_text(self, locator: str) -> str:
        """Get the text content of an element.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |

        Returns the text content of the element (e.g., label text, button text).

        Example:
        | ${text}=    Get Element Text    JLabel#status
        | Should Be Equal    ${text}    Ready

        """
        return self._lib.get_element_text(locator)

    def element_text_should_be(self, locator: str, expected: str) -> None:
        """Verify that element text matches expected value exactly.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |
        | ``expected`` | Expected text value. |

        Fails if the element text does not match exactly.

        Example:
        | Element Text Should Be    JLabel#status    Ready
        | Element Text Should Be    #message    Operation completed

        """
        self._lib.element_text_should_be(locator, expected)

    def element_text_should_contain(self, locator: str, expected: str) -> None:
        """Verify that element text contains expected substring.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |
        | ``expected`` | Expected substring. |

        Fails if the element text does not contain the expected substring.

        Example:
        | Element Text Should Contain    JLabel#status    Success
        | Element Text Should Contain    #message    completed

        """
        self._lib.element_text_should_contain(locator, expected)

    def get_element_property(self, locator: str, property_name: str) -> Any:
        """Get a property value from an element.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |
        | ``property_name`` | Name of the property to retrieve (e.g., ``text``, ``enabled``, ``visible``). |

        Returns the value of the specified property.

        Example:
        | ${text}=    Get Element Property    JTextField#input    text
        | ${enabled}=    Get Element Property    JButton#save    enabled

        """
        return self._lib.get_element_property(locator, property_name)

    # ==========================================================================
    # UI Tree Keywords
    # ==========================================================================

    def log_ui_tree(self, locator: Optional[str] = None) -> None:
        """Log the UI component tree to the test log.

        | **Argument** | **Description** |
        | ``locator`` | Optional locator to start from. Logs entire tree if not specified. |

        Prints the component hierarchy for debugging purposes.

        Example:
        | Log UI Tree
        | Log UI Tree    JPanel#main

        """
        # Get tree as text and log it
        tree = self.get_ui_tree(format="text")
        print(tree)

    def get_ui_tree(
        self, format: str = "text", max_depth: Optional[int] = None, visible_only: bool = False
    ) -> str:
        """Get the UI component tree as a string.

        | **Argument** | **Description** |
        | ``format`` | Output format: ``text``, ``json``, or ``xml``. Default ``text``. |
        | ``max_depth`` | Maximum depth to traverse. ``None`` for unlimited. |
        | ``visible_only`` | Only include visible components. Default ``False``. |

        Returns the component tree in the specified format.

        Example:
        | ${tree}=    Get UI Tree
        | ${json}=    Get UI Tree    format=json
        | ${tree}=    Get UI Tree    format=text    max_depth=3

        """
        return self._lib.get_ui_tree(format, max_depth, visible_only)

    def save_ui_tree(self, filename: str, locator: Optional[str] = None) -> None:
        """Save the UI component tree to a file.

        | **Argument** | **Description** |
        | ``filename`` | Path to save the tree file. |
        | ``locator`` | Optional locator to start from. Saves entire tree if not specified. |

        Saves the component hierarchy to a file for analysis.

        Example:
        | Save UI Tree    tree.txt
        | Save UI Tree    panel_tree.txt    JPanel#main

        """
        self._lib.save_ui_tree(filename, locator)

    def refresh_ui_tree(self) -> None:
        """Refresh the cached UI component tree.

        Call this after UI changes to update the internal component cache.
        Useful when the UI has been modified and you need to find new elements.

        Example:
        | Click Button    JButton#addItem
        | Refresh UI Tree
        | Find Element    JLabel#newItem

        """
        self._lib.refresh_ui_tree()

    # ==========================================================================
    # Screenshot Keywords
    # ==========================================================================

    def capture_screenshot(self, filename: Optional[str] = None) -> str:
        """Capture a screenshot of the application.

        | **Argument** | **Description** |
        | ``filename`` | Optional filename for the screenshot. Auto-generated if not specified. |

        Returns the path to the saved screenshot file.

        Example:
        | ${path}=    Capture Screenshot
        | ${path}=    Capture Screenshot    filename=error.png
        | Log    Screenshot saved to: ${path}

        """
        return self._lib.capture_screenshot(filename)

    def set_screenshot_directory(self, directory: str) -> None:
        """Set the directory for saving screenshots.

        | **Argument** | **Description** |
        | ``directory`` | Path to the screenshot directory. |

        All subsequent screenshots will be saved to this directory.

        Example:
        | Set Screenshot Directory    ${OUTPUT_DIR}/screenshots
        | Set Screenshot Directory    /tmp/test-screenshots

        """
        self._lib.set_screenshot_directory(directory)

    # ==========================================================================
    # Configuration Keywords
    # ==========================================================================

    def set_timeout(self, timeout: float) -> None:
        """Set the default timeout for wait operations.

        | **Argument** | **Description** |
        | ``timeout`` | Timeout in seconds. |

        Sets the default timeout used by all wait keywords when no explicit
        timeout is provided.

        Example:
        | Set Timeout    30
        | Set Timeout    60

        """
        self._timeout = timeout
        self._lib.set_timeout(timeout)

    # ==========================================================================
    # Additional Convenience Keywords
    # ==========================================================================

    def select_tab(self, locator: str, tab_identifier: str) -> None:
        """Select a tab in a JTabbedPane.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator for the ``JTabbedPane``. See `Locator Syntax`. |
        | ``tab_identifier`` | Tab title (string) or index (integer) to select. |

        Selects the specified tab by title or index.

        Example:
        | Select Tab    JTabbedPane[name='mainTabbedPane']    Form Input
        | Select Tab    #mainTabs    Settings
        | Select Tab    JTabbedPane    0

        """
        # Delegate to Rust library's select_tab which uses selectItem RPC
        self._lib.select_tab(locator, str(tab_identifier))

    def type_text(self, locator: str, text: str) -> None:
        """Type text character by character into a text field.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |
        | ``text`` | Text to type character by character. |

        Simulates actual key presses rather than setting the text directly.
        Does not clear existing text - use `Clear Text` first if needed.

        Example:
        | Type Text    #searchField    hello
        | Type Text    JTextField#input    test@example.com

        """
        # For now, use input_text as the underlying implementation
        # The Rust library handles the actual typing
        self._lib.input_text(locator, text, clear=False)

    def right_click(self, locator: str) -> None:
        """Right-click (context click) on an element.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |

        Performs a right-click to open context menus.
        Use `Select From Popup Menu` after this to select menu items.

        Example:
        | Right Click    JTree#fileTree
        | Select From Popup Menu    Delete

        """
        self._lib.right_click_element(locator)

    def element_should_be_selected(self, locator: str) -> None:
        """Verify that an element is selected (checked).

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |

        Works with checkboxes, radio buttons, list items, etc.
        Fails if the element is not selected.

        Example:
        | Element Should Be Selected    JCheckBox#rememberMe
        | Element Should Be Selected    JRadioButton#optionA

        """
        selected = self._lib.get_element_property(locator, "selected")
        if not selected:
            raise AssertionError(f"Element '{locator}' should be selected but was not")

    def element_should_not_be_selected(self, locator: str) -> None:
        """Verify that an element is not selected (unchecked).

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |

        Works with checkboxes, radio buttons, list items, etc.
        Fails if the element is selected.

        Example:
        | Element Should Not Be Selected    JRadioButton#optionB
        | Element Should Not Be Selected    JCheckBox#newsletter

        """
        selected = self._lib.get_element_property(locator, "selected")
        if selected:
            raise AssertionError(f"Element '{locator}' should not be selected but was")

    def element_should_exist(self, locator) -> None:
        """Verify that an element exists in the UI tree.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string or SwingElement object. See `Locator Syntax`. |

        Fails if the element does not exist.

        Example:
        | Element Should Exist    JButton#submit
        | Element Should Exist    #loginForm
        | ${elem}=    Find Element    JButton
        | Element Should Exist    ${elem}

        """
        # Handle SwingElement objects - check type name to avoid PyO3 conversion issues
        if type(locator).__name__ == 'SwingElement':
            # It's a SwingElement and it exists by definition
            # (Find Element already validated it)
            return

        # Handle locator strings
        try:
            elements = self._lib.find_elements(locator)
            if not elements:
                raise AssertionError(f"Element '{locator}' should exist but was not found")
        except AssertionError:
            raise
        except Exception as e:
            raise AssertionError(f"Element '{locator}' should exist but was not found: {e}")

    def element_should_not_exist(self, locator) -> None:
        """Verify that an element does not exist in the UI tree.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string or SwingElement object. See `Locator Syntax`. |

        Fails if the element exists.

        Example:
        | Element Should Not Exist    JDialog#error
        | Element Should Not Exist    #loadingSpinner

        """
        # Handle SwingElement objects - if we have the object, it exists (duck typing)
        if hasattr(locator, '_elem'):
            raise AssertionError(f"Element '{locator}' should not exist but was found")

        # Handle locator strings
        try:
            elements = self._lib.find_elements(locator)
            if elements:
                raise AssertionError(f"Element '{locator}' should not exist but was found")
        except AssertionError:
            raise
        except Exception:
            # Element not found is the expected outcome
            pass

    # ==========================================================================
    # Keyword Aliases for Compatibility
    # ==========================================================================

    def wait_until_element_visible(
        self,
        locator: str,
        timeout: Optional[float] = None,
    ) -> None:
        """Alias for `Wait Until Element Is Visible`."""
        self.wait_until_element_is_visible(locator, timeout)

    def wait_until_element_enabled(
        self,
        locator: str,
        timeout: Optional[float] = None,
    ) -> None:
        """Alias for `Wait Until Element Is Enabled`."""
        self.wait_until_element_is_enabled(locator, timeout)

    def wait_for_element(
        self,
        locator: str,
        timeout: Optional[float] = None,
    ) -> "_SwingElement":
        """Wait for an element to exist and return it.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |
        | ``timeout`` | Maximum wait time in seconds. Uses library default if not set. |

        Returns the found ``SwingElement`` after it exists.
        Raises ``TimeoutError`` if element does not exist within timeout.

        Example:
        | ${elem}=    Wait For Element    JButton#submit
        | ${elem}=    Wait For Element    JButton#submit    timeout=10

        """
        timeout_val = timeout if timeout is not None else self._timeout
        self._lib.wait_until_element_exists(locator, timeout_val)
        return self._lib.find_element(locator)

    def wait_until_element_contains(
        self,
        locator: str,
        text: str,
        timeout: Optional[float] = None,
    ) -> None:
        """Wait until element text contains the expected substring.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |
        | ``text`` | Text substring to wait for. |
        | ``timeout`` | Maximum wait time in seconds. Uses library default if not set. |

        Raises ``TimeoutError`` if element text does not contain the expected
        substring within timeout.

        Example:
        | Wait Until Element Contains    JLabel#status    complete
        | Wait Until Element Contains    JLabel#status    complete    timeout=10

        """
        import time

        timeout_val = timeout if timeout is not None else self._timeout
        end_time = time.time() + timeout_val
        poll_interval = 0.5

        while time.time() < end_time:
            try:
                actual_text = self._lib.get_element_text(locator)
                if text in actual_text:
                    return
            except Exception:
                pass
            time.sleep(poll_interval)

        raise TimeoutError(f"Element '{locator}' did not contain '{text}' within {timeout_val}s")

    def get_component_tree(
        self,
        locator: Optional[str] = None,
        format: str = "text",
        max_depth: Optional[int] = None,
    ) -> str:
        """Get the component tree in various formats.

        | **Argument** | **Description** |
        | ``locator`` | Optional locator to start from. Uses root if not specified. |
        | ``format`` | Output format: ``text``, ``json``, or ``yaml``. Default ``text``. |
        | ``max_depth`` | Maximum depth to traverse. ``None`` for unlimited. |

        Returns the component tree as a string in the specified format.

        Example:
        | ${tree}=    Get Component Tree
        | ${json}=    Get Component Tree    format=json
        | ${tree}=    Get Component Tree    format=text    max_depth=2

        """
        tree_str = self._lib.get_ui_tree(locator)
        # The Rust library returns text format by default
        # Format conversion would be done here if needed
        return tree_str

    def log_component_tree(self, locator: Optional[str] = None) -> None:
        """Alias for `Log UI Tree`."""
        self._lib.log_ui_tree(locator)

    def list_applications(self) -> List[str]:
        """List available Java applications to connect to.

        Returns a list of available application identifiers that can be
        used with `Connect To Application`.

        *Note:* This is a placeholder - actual discovery requires JVM enumeration.

        Example:
        | ${apps}=    List Applications
        | Log Many    @{apps}

        """
        # Placeholder - actual implementation would use JVM discovery
        return []

    # ==========================================================================
    # List Operations
    # ==========================================================================

    def get_list_items(self, locator: str) -> List[str]:
        """Get all items from a JList component.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator for the ``JList``. See `Locator Syntax`. |

        Returns a list of all item texts in the list.

        Example:
        | ${items}=    Get List Items    JList[name='itemList']
        | Length Should Be    ${items}    5

        """
        # Delegate to Rust library's get_list_items which uses getListItems RPC
        return self._lib.get_list_items(locator)

    def select_from_list(self, locator: str, value: str) -> None:
        """Select an item from a JList component by text.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator for the ``JList``. See `Locator Syntax`. |
        | ``value`` | Item text to select. |

        Selects the item matching the specified text.

        Example:
        | Select From List    JList[name='itemList']    Item 1
        | Select From List    #fileList    document.txt

        """
        # Delegate to Rust library's select_from_list which uses selectItem RPC
        self._lib.select_from_list(locator, value)

    def select_list_item_by_index(self, locator: str, index: int) -> None:
        """Select an item from a JList by index.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator for the ``JList``. See `Locator Syntax`. |
        | ``index`` | Index of the item to select (0-based). |

        Selects the item at the specified index.

        Example:
        | Select List Item By Index    JList[name='itemList']    0
        | Select List Item By Index    #fileList    2

        """
        # Delegate to Rust library's select_list_item_by_index which uses selectItem RPC
        self._lib.select_list_item_by_index(locator, index)

    # ==========================================================================
    # Tree Operations
    # ==========================================================================

    def get_tree_nodes(self, locator: str) -> List[str]:
        """Get all node paths from a JTree component.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator for the ``JTree``. See `Locator Syntax`. |

        Returns a list of all node paths in the tree.

        Example:
        | ${nodes}=    Get Tree Nodes    JTree#fileTree
        | Should Contain    ${nodes}    Root/Documents

        """
        # Get tree structure via RPC and extract node paths
        tree_data = self._lib.get_tree_data(locator)
        if not tree_data:
            return []
        # tree_data is a dict with text and children - flatten to paths
        return self._flatten_tree_paths(tree_data, "")

    def _flatten_tree_paths(self, node: dict, prefix: str) -> List[str]:
        """Helper to flatten tree structure into list of paths."""
        paths = []
        text = node.get("text", "")
        current_path = f"{prefix}/{text}" if prefix else text
        paths.append(current_path)

        children = node.get("children", [])
        for child in children:
            paths.extend(self._flatten_tree_paths(child, current_path))

        return paths

    # ==========================================================================
    # Additional Table and Property Keywords
    # ==========================================================================

    def get_table_data(self, locator: str) -> List[List[str]]:
        """Get all data from a table as a 2D list.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator for the ``JTable``. See `Locator Syntax`. |

        Returns a 2D list of cell values (rows x columns).

        Example:
        | ${data}=    Get Table Data    JTable#dataTable
        | ${first_row}=    Set Variable    ${data}[0]
        | ${cell}=    Set Variable    ${data}[0][1]

        """
        row_count = self._lib.get_table_row_count(locator)
        col_count = self._lib.get_table_column_count(locator)
        data = []
        for row in range(row_count):
            row_data = []
            for col in range(col_count):
                # Convert column to string as required by Rust function
                value = self._lib.get_table_cell_value(locator, row, str(col))
                row_data.append(value)
            data.append(row_data)
        return data

    def get_element_properties(self, locator: str) -> Dict[str, Any]:
        """Get all common properties from an element.

        | **Argument** | **Description** |
        | ``locator`` | CSS or XPath-like locator string. See `Locator Syntax`. |

        Returns a dictionary containing common properties: ``name``, ``text``,
        ``enabled``, ``visible``, and ``selected``.

        Example:
        | ${props}=    Get Element Properties    JButton#submit
        | Should Be True    ${props}[enabled]
        | Log    Button text: ${props}[text]

        """
        properties = {}
        for prop in ["name", "text", "enabled", "visible", "selected"]:
            try:
                properties[prop] = self._lib.get_element_property(locator, prop)
            except Exception:
                pass
        return properties


# Apply deprecation aliases to SwingLibrary
# This adds backward-compatible keyword aliases that issue deprecation warnings
if _DEPRECATION_AVAILABLE and _ASSERTION_ENGINE_AVAILABLE:
    _alias_registry = get_alias_registry()
    _alias_registry.apply_to_class(SwingLibrary)


# Legacy SwingElement wrapper (if needed)
class SwingElement:
    """Represents a Swing UI element.

    This class wraps a reference to a Swing component and provides
    methods for interaction and inspection.
    """

    def __init__(self, elem: "_SwingElement") -> None:
        """Initialize with a Rust SwingElement."""
        self._elem = elem

    @property
    def hash_code(self) -> int:
        """Get the element's hash code."""
        return self._elem.hash_code

    @property
    def class_name(self) -> str:
        """Get the element's Java class name."""
        return self._elem.class_name

    @property
    def simple_name(self) -> str:
        """Get the element's simple class name."""
        return self._elem.simple_name

    @property
    def name(self) -> Optional[str]:
        """Get the element's name property."""
        return self._elem.name

    @property
    def text(self) -> Optional[str]:
        """Get the element's text content."""
        return self._elem.text

    @property
    def visible(self) -> bool:
        """Check if the element is visible."""
        return self._elem.visible

    @property
    def enabled(self) -> bool:
        """Check if the element is enabled."""
        return self._elem.enabled

    @property
    def bounds(self) -> tuple:
        """Get the element's bounds (x, y, width, height)."""
        return self._elem.bounds

    def __repr__(self) -> str:
        name = f"[{self.name}]" if self.name else ""
        text = (
            f'"{self.text[:20]}..."'
            if self.text and len(self.text) > 20
            else f'"{self.text}"'
            if self.text
            else ""
        )
        return f"<SwingElement {self.simple_name}{name} {text}>".strip()


class SwtLibrary(SwtGetterKeywords, SwtTableKeywords, SwtTreeKeywords):
    """Robot Framework library for SWT (Standard Widget Toolkit) application automation.

    This library provides comprehensive keywords for automating SWT-based desktop
    applications including Eclipse IDE and other Eclipse RCP-based applications.
    SWT (Standard Widget Toolkit) is a GUI toolkit for Java that provides native
    widget access through JNI, resulting in fast, platform-native user interfaces.

    **Table of Contents**

    - `Introduction`
    - `Installation & Setup`
    - `Connecting to Applications`
    - `Locator Syntax`
    - `Shell Management`
    - `Widget Hierarchy`
    - `Assertion Engine`
    - `Common Workflows`
    - `Troubleshooting`
    - `See Also`

    **Introduction**

    SWT (Standard Widget Toolkit) is a native widget library for Java developed
    by the Eclipse Foundation. Unlike Java Swing which draws widgets using Java
    graphics primitives, SWT uses native operating system widgets through JNI
    (Java Native Interface), providing:

    - *Native Look and Feel*: Applications appear identical to native OS applications
    - *High Performance*: Direct access to native widgets eliminates abstraction overhead
    - *Platform Integration*: Full access to OS-specific features and behaviors
    - *Eclipse Foundation*: Powers Eclipse IDE and thousands of RCP applications

    This library enables Robot Framework to automate any SWT-based application
    through a Java agent that communicates via JSON-RPC over a socket connection.

    **Installation & Setup**

    *Installing the Library*

    Install via pip:

    | ``pip install robotframework-javagui``

    This installs:
    - Python bindings with Robot Framework keywords
    - Bundled Java agent JAR for instrumenting SWT applications
    - Rust core library for high-performance widget operations

    *Starting SWT Applications with the Agent*

    To automate an SWT application, it must be started with the Java agent:

    | ``java -javaagent:path/to/javagui-agent.jar=port=5679 -jar your-swt-app.jar``

    The agent JAR path can be retrieved programmatically:

    | from JavaGui import get_agent_jar_path
    | agent_jar = get_agent_jar_path()
    | # Use in your application startup script

    *Agent Configuration Options*

    | *Option* | *Description* | *Default* |
    | port | TCP port for JSON-RPC server | 5679 |
    | host | Network interface to bind | localhost |
    | debug | Enable debug logging | false |

    Example with options:

    | ``java -javaagent:agent.jar=port=5679,host=0.0.0.0,debug=true -jar app.jar``

    **Connecting to Applications**

    After starting an SWT application with the agent, connect from Robot Framework:

    | *** Settings ***
    | Library    JavaGui.Swt
    |
    | *** Test Cases ***
    | Connect To My SWT Application
    |     Connect To Swt Application    MyApp    host=localhost    port=5679
    |     # Application is now ready for automation
    |     Disconnect

    The connection identifies applications by:
    - Application name (any unique identifier)
    - Host and port where the agent is listening

    Multiple connections to different applications are not supported in the same
    test execution - disconnect from one before connecting to another.

    **Locator Syntax**

    SWT widget locators use CSS-like syntax adapted for SWT's widget model.
    Locators can be simple (widget type only) or complex (multiple criteria).

    *Basic Locators*

    | *Locator* | *Description* | *Example* |
    | Type | Match by widget class name | ``Button``, ``Text``, ``Label`` |

    Common SWT widget types: ``Button``, ``Text``, ``Label``, ``Combo``, ``List``,
    ``Table``, ``Tree``, ``Shell``, ``Composite``, ``CLabel``, ``StyledText``,
    ``ToolBar``, ``Menu``, ``TabFolder``, ``Group``, ``Canvas``

    *ID-Based Locators*

    | *Locator* | *Description* | *Example* |
    | #id | Match by widget name/ID | ``#submitBtn``, ``#userNameField`` |
    | Type#id | Widget type + ID | ``Button#submitBtn``, ``Text#username`` |

    Note: SWT widget IDs are set programmatically via ``setData("name", "widgetId")``
    or equivalent methods. Not all SWT applications use widget IDs consistently.

    *Attribute-Based Locators*

    | *Locator* | *Description* | *Example* |
    | [text='value'] | Match by text content | ``[text='Save']``, ``Button[text='OK']`` |
    | [tooltip='value'] | Match by tooltip text | ``[tooltip='Submit form']`` |
    | [enabled=true] | Match by enabled state | ``Button[enabled=true]`` |
    | [visible=true] | Match by visibility | ``Text[visible=true]`` |

    *Hierarchical Locators*

    | *Locator* | *Description* | *Example* |
    | Parent > Child | Direct child | ``Shell > Button``, ``Composite > Text`` |
    | Ancestor Descendant | Any descendant | ``Shell Button``, ``TabFolder Text`` |
    | Parent >> Descendant | Explicit descendant | ``Composite >> Button`` |

    *XPath-Style Locators*

    | *Locator* | *Description* | *Example* |
    | //Type | Any descendant | ``//Button``, ``//Text`` |
    | /Type | Direct child | ``/Shell/Composite/Button`` |
    | [@attr='val'] | XPath attribute | ``//Button[@text='OK']``, ``//Text[@enabled='true']`` |
    | [n] | Index selection | ``//Button[0]``, ``//Table[1]`` |

    *Combining Locators*

    Locators can combine multiple criteria:

    | ``Button#submit[text='Save'][enabled=true]`` |
    | ``Shell[text='Preferences'] Composite Button`` |
    | ``//Shell[@text='Main Window']//Button[0]`` |
    | ``TabFolder > Composite >> Text[visible=true]`` |

    **Shell Management**

    In SWT, a Shell is a top-level window (equivalent to JFrame in Swing or
    Window in native applications). Understanding Shells is crucial for SWT
    automation:

    *What is a Shell?*

    - *Top-Level Container*: Every SWT application has one or more Shells
    - *Window Management*: Shells can be minimized, maximized, closed
    - *Modal vs Non-Modal*: Shells can block interaction with other windows
    - *Parent-Child Relationship*: Child Shells belong to parent Shells

    *Working with Shells*

    List all open Shells:
    | ${shells}=    Get Shells
    | Log Many    @{shells}

    Activate a specific Shell (bring to front):
    | Activate Shell    Shell[text='Preferences']
    | Activate Shell    #mainWindow

    Close a Shell:

    | Close Shell    Shell[text='About Dialog']
    | Close Shell    #errorDialog

    *Shell Activation and Focus*

    Before interacting with widgets in a Shell, it's recommended to activate it:

    | Activate Shell    Shell[text='Main Window']
    | Click Widget      Button#submitBtn
    | Input Text        Text#username    testuser

    This ensures the Shell has focus and widgets are accessible.

    *Multiple Shell Scenarios*

    When multiple Shells are open (e.g., main window + dialog), specify which
    Shell contains the target widget:

    | # Activate parent Shell first
    | Activate Shell    Shell[text='Main Window']
    | Click Widget      Button#openDialog
    |
    | # Now work with the dialog Shell
    | Activate Shell    Shell[text='Preferences']
    | Click Widget      Button[text='OK']

    **Widget Hierarchy**

    SWT applications follow a hierarchical widget structure, similar to HTML DOM:

    *Widget Tree Structure*

    | Shell (top-level window)
    |   └─ Composite (container)
    |       ├─ Label (text display)
    |       ├─ Text (input field)
    |       └─ Button (clickable button)

    *Common Widget Types*

    | *Widget Class* | *Purpose* | *Common Operations* |
    | Shell | Top-level window | Activate, Close |
    | Composite | Container for other widgets | Navigate children |
    | Button | Clickable button | Click |
    | Text | Single/multi-line text input | Input Text, Clear |
    | Label | Static text display | Get Text |
    | Combo | Dropdown selection | Select Item |
    | List | List of selectable items | Select Item |
    | Table | Tabular data display | Select Row, Get Cell |
    | Tree | Hierarchical data display | Expand, Select Node |
    | TabFolder | Tab container | Select Tab |
    | StyledText | Rich text editor | Input Text, Get Text |
    | Group | Labeled container | Navigate children |
    | Menu | Application menu | Select Menu Item |
    | ToolBar | Toolbar with buttons | Click Tool Item |

    *Controls vs Composites*

    - *Control*: Base class for all widgets (Button, Text, Label, etc.)
    - *Composite*: Control that can contain other Controls
    - *Shell*: Special Composite representing a window

    When searching for widgets, understanding this hierarchy helps construct
    effective locators:

    | # Find Button anywhere in Shell
    | Find Widget    Shell Button
    |
    | # Find Button as direct child of Composite
    | Find Widget    Composite > Button
    |
    | # Find all Text widgets in application
    | ${texts}=    Find Widgets    Text

    **Assertion Engine**

    The library integrates the ``assertionengine`` library for inline assertions,
    following the Browser Library pattern. Get keywords return values that can
    be immediately validated.

    *Assertion Keyword Pattern*

    Instead of separate get/assert steps:
    | # Old pattern (still supported)
    | ${text}=    Get Widget Text    Label#status
    | Should Be Equal    ${text}    Ready

    Use inline assertions:
    | # New pattern (preferred)
    | Get Widget Text    Label#status    ==    Ready

    *Supported Operators*

    | *Operator* | *Description* | *Example* |
    | == | Equal to | Get Widget Text    Label    ==    Ready |
    | != | Not equal to | Get Widget Text    Label    !=    Error |
    | < | Less than | Get Widget Count    Button    <    10 |
    | > | Greater than | Get Widget Count    Button    >    0 |
    | <= | Less than or equal | Get Swt Table Row Count    Table    <=    100 |
    | >= | Greater than or equal | Get Swt Table Row Count    Table    >=    1 |
    | contains | Contains substring/item | Get Widget Text    Label    contains    Success |
    | not contains | Does not contain | Get Widget States    Button    not contains    disabled |
    | starts | Starts with | Get Widget Text    Label    starts    Loading |
    | ends | Ends with | Get Widget Text    Label    ends    complete |
    | matches | Regex pattern match | Get Widget Text    Label    matches    \\d{3}-\\d{4} |
    | validate | Custom validator function | Get Widget Text    Label    validate    ${validator} |
    | then | Custom then block | Get Widget Text    Label    then    Should Not Be Empty |

    *Assertion Examples*

    Text assertions:
    | Get Widget Text    Label#status    ==    Ready
    | Get Widget Text    Text#username    !=    ${EMPTY}
    | Get Widget Text    Label#error    contains    failed
    | Get Widget Text    Label#progress    matches    \\d+%

    Count assertions:
    | Get Widget Count    Button    >    0
    | Get Widget Count    Text[visible=true]    ==    3
    | Get Swt Table Row Count    Table#data    >=    1

    State assertions:
    | Get Widget States    Button#submit    contains    enabled, visible
    | Get Widget States    Text#field    not contains    read_only

    Table assertions:
    | Get Swt Table Cell    Table    0    0    ==    John Doe
    | Get Swt Table Cell    Table    1    Name    contains    Smith
    | Get Swt Table Row Count    Table#users    >    0

    Tree assertions:
    | Get Swt Tree Item Text    Tree    Root/Folder    ==    Documents
    | Get Swt Tree Item Count    Tree    >    0

    *Custom Validators*

    Use the ``validate`` operator with custom validation functions:
    | ${validator}=    Create Validator    ${custom_check}
    | Get Widget Text    Label    validate    ${validator}

    *Then Blocks*

    Use ``then`` for complex assertions:
    | Get Widget Text    Label#status    then
    |     Should Not Be Empty
    |     Should Contain    Success

    **Common Workflows**

    *Connecting and Basic Interaction*

    | *** Settings ***
    | Library    JavaGui.Swt
    |
    | *** Test Cases ***
    | Basic SWT Application Test
    |     # Start application with agent first (external)
    |     # Then connect from test
    |     Connect To Swt Application    MyApp
    |
    |     # Verify main window is open
    |     Get Widget Count    Shell[text='Main Window']    ==    1
    |
    |     # Interact with widgets
    |     Input Text    Text#username    testuser
    |     Input Text    Text#password    secret123
    |     Click Widget    Button#loginBtn
    |
    |     # Verify result
    |     Wait Until Widget Exists    Label#welcome
    |     Get Widget Text    Label#welcome    ==    Welcome, testuser!
    |
    |     # Cleanup
    |     Disconnect
    *Working with Tables*

    | *** Test Cases ***
    | Table Operations
    |     Connect To Swt Application    MyApp
    |
    |     # Verify table has data
    |     Get Swt Table Row Count    Table#dataGrid    >    0
    |
    |     # Read cell values
    |     ${name}=    Get Swt Table Cell    Table#dataGrid    0    0
    |     ${email}=    Get Swt Table Cell    Table#dataGrid    0    1
    |
    |     # Or with inline assertion
    |     Get Swt Table Cell    Table#dataGrid    0    Name    ==    John Doe
    |
    |     # Select a row
    |     Select Table Row    Table#dataGrid    2
    |
    |     # Select by value
    |     ${row}=    Select Table Row By Value    Table#dataGrid    0    John
    |
    |     Disconnect

    *Working with Trees*

    | *** Test Cases ***
    | Tree Navigation
    |     Connect To Swt Application    Eclipse
    |
    |     # Expand tree nodes
    |     Expand Tree Item    Tree#fileTree    Project Explorer
    |     Expand Tree Item    Tree#fileTree    Project Explorer/src
    |     Expand Tree Item    Tree#fileTree    Project Explorer/src/main
    |
    |     # Select a node
    |     Select Tree Item    Tree#fileTree    Project Explorer/src/main/Main.java
    |
    |     # Verify selection
    |     ${selected}=    Get Selected Tree Nodes    Tree#fileTree
    |     Should Contain    ${selected}    Main.java
    |
    |     Disconnect
    *Working with Multiple Shells*

    | *** Test Cases ***
    | Dialog Interaction
    |     Connect To Swt Application    MyApp
    |
    |     # Work in main window
    |     Activate Shell    Shell[text='Main Window']
    |     Click Widget      Button[text='Open Preferences']
    |
    |     # Wait for dialog to open
    |     Wait Until Widget Exists    Shell[text='Preferences']
    |
    |     # Switch to dialog
    |     Activate Shell    Shell[text='Preferences']
    |     Input Text        Text#settingValue    new value
    |     Click Widget      Button[text='OK']
    |
    |     # Wait for dialog to close
    |     Wait Until Widget Does Not Exist    Shell[text='Preferences']
    |
    |     # Back to main window
    |     Activate Shell    Shell[text='Main Window']
    |
    |     Disconnect

    *Form Fill Workflow*

    | *** Test Cases ***
    | Complete Form Submission
    |     Connect To Swt Application    FormApp
    |
    |     # Fill text fields
    |     Input Text    Text#firstName    John
    |     Input Text    Text#lastName     Doe
    |     Input Text    Text#email        john.doe@example.com
    |
    |     # Select from combo box
    |     Select Combo Item    Combo#country    United States
    |
    |     # Check checkbox
    |     Check Button    Button[text='I agree to terms']
    |
    |     # Submit form
    |     Click Widget    Button#submitBtn
    |
    |     # Verify success
    |     Wait Until Widget Exists    Label#successMsg
    |     Get Widget Text    Label#successMsg    contains    successfully
    |
    |     Disconnect

    **Troubleshooting**

    *Connection Issues*

    *Problem*: "Connection refused" or timeout errors

    *Solutions*:
    - Verify the SWT application is running with the Java agent
    - Check the agent port matches (default 5679 for SWT)
    - Ensure no firewall is blocking localhost connections
    - Verify the agent JAR is compatible with your SWT version

    *Widget Not Found*

    *Problem*: "Widget not found" or ElementNotFoundError

    *Solutions*:
    - Use ``Get Shells`` to list available Shells
    - Activate the correct Shell before finding widgets
    - Verify the widget locator syntax (try simpler locators first)
    - Use ``Log UI Tree`` to inspect the widget hierarchy (if available)
    - Check if widget is created dynamically (use ``Wait Until Widget Exists``)
    - Ensure the widget is in the active Shell

    *Locator Debugging*

    To debug locator issues, log the available Shells:
    | ${shells}=    Get Shells
    | Log Many    @{shells}

    Or use a broader locator to find widgets:
    | ${widgets}=    Find Widgets    Button
    | Log Many    @{widgets}

    *Timing Issues*

    *Problem*: Test fails intermittently due to slow UI updates

    *Solutions*:
    - Use explicit waits: ``Wait Until Widget Exists``
    - Increase default timeout: ``Set Timeout    30``
    - Wait for Shell activation before interactions
    - Use ``Wait Until Widget Enabled`` before clicking

    *Text Input Issues*

    *Problem*: Text not appearing in input fields

    *Solutions*:
    - Ensure the Shell is activated
    - Click on the Text widget before typing
    - Use ``Clear Text`` before ``Input Text`` if needed
    - Check if widget is read-only or disabled

    *Agent Version Compatibility*

    *Problem*: RPC method not found or incompatible agent version

    *Solutions*:
    - Update both the library and agent JAR to the same version
    - Check release notes for breaking changes
    - Ensure the SWT version is compatible with the agent

    **See Also**

    *Related Libraries*

    - `JavaGui.Swing` - For Java Swing application automation
    - `JavaGui.Rcp` - Extended keywords for Eclipse RCP applications
    - ``assertionengine`` - Assertion operator engine
    - Browser Library - Similar assertion pattern for web automation

    *Documentation*

    - Library keyword documentation (generated by libdoc)
    - GitHub repository: https://github.com/your-org/robotframework-javagui
    - SWT official documentation: https://www.eclipse.org/swt/
    - Eclipse RCP documentation: https://wiki.eclipse.org/Rich_Client_Platform

    *Examples*

    Example test suites are available in the repository:
    - tests/robot/swt/ - Basic SWT automation examples
    - tests/robot/rcp/ - Eclipse RCP automation examples

    *Support*

    - GitHub Issues: Report bugs and feature requests
    - Stack Overflow: Tag questions with ``robotframework`` and ``swt``
    - Robot Framework Slack: #libraries channel
    """

    ROBOT_LIBRARY_SCOPE = "GLOBAL"
    ROBOT_LIBRARY_VERSION = __version__

    def __init__(
        self,
        timeout: float = 10.0,
    ) -> None:
        """Initialize the SWT Library.

        | **Argument** | **Description** |
        | ``timeout`` | Default timeout in seconds for wait operations. Default ``10.0``. |

        Example:
        | **Setting** | **Value** | **Value** |
        | Library | JavaGui.SwtLibrary | |
        | Library | JavaGui.SwtLibrary | timeout=30 |

        """
        if not _RUST_AVAILABLE:
            raise ImportError(
                f"SWT Library Rust core not available: {_IMPORT_ERROR}\n"
                "Please ensure the library is properly installed with: pip install robotframework-javagui"
            )

        self._lib = _SwtLibrary(timeout=timeout)
        self._timeout = timeout

        # AssertionEngine configuration
        self._assertion_timeout = 5.0
        self._assertion_interval = 0.1

    # Connection Keywords
    def connect_to_swt_application(
        self, app: str, host: str = "localhost", port: int = 5679, timeout: Optional[float] = None
    ):
        """Connect to an SWT application."""
        return self._lib.connect_to_swt_application(app, host, port, timeout)

    def disconnect(self):
        """Disconnect from the SWT application."""
        return self._lib.disconnect()

    def is_connected(self) -> bool:
        """Check if connected to an SWT application."""
        return self._lib.is_connected()

    # Shell Keywords
    def get_shells(self):
        """Get all shells."""
        return self._lib.get_shells()

    def activate_shell(self, locator: str):
        """Activate a shell."""
        return self._lib.activate_shell(locator)

    def close_shell(self, locator: str):
        """Close a shell."""
        return self._lib.close_shell(locator)

    # Widget Finding Keywords
    def find_widget(self, locator: str):
        """Find a single widget."""
        return self._lib.find_widget(locator)

    def find_widgets(self, locator: str):
        """Find all matching widgets."""
        return self._lib.find_widgets(locator)

    # Click Keywords
    def click_widget(self, locator: str):
        """Click on a widget."""
        return self._lib.click_widget(locator)

    def double_click_widget(self, locator: str):
        """Double-click on a widget."""
        return self._lib.double_click_widget(locator)

    # Text Input Keywords
    def input_text(self, locator: str, text: str, clear: bool = True):
        """Input text into a widget."""
        return self._lib.input_text(locator, text, clear)

    def clear_text(self, locator: str):
        """Clear text from a widget."""
        return self._lib.clear_text(locator)

    # Selection Keywords
    def select_combo_item(self, locator: str, item: str):
        """Select an item from a combo box."""
        return self._lib.select_combo_item(locator, item)

    def select_list_item(self, locator: str, item: str):
        """Select an item from a list."""
        return self._lib.select_list_item(locator, item)

    def check_button(self, locator: str):
        """Check a checkbox or toggle button."""
        return self._lib.check_button(locator)

    def uncheck_button(self, locator: str):
        """Uncheck a checkbox or toggle button."""
        return self._lib.uncheck_button(locator)

    # Table Keywords
    def get_table_row_count(self, locator: str) -> int:
        """Get the number of rows in a table."""
        return self._lib.get_table_row_count(locator)

    def get_table_cell(self, locator: str, row: int, col: int) -> str:
        """Get the value of a table cell."""
        return self._lib.get_table_cell(locator, row, col)

    def select_table_row(self, locator: str, row: int):
        """Select a table row."""
        return self._lib.select_table_row(locator, row)

    def get_table_row_values(self, locator: str, row: int):
        """Get all values from a table row."""
        return self._lib.get_table_row_values(locator, row)

    def select_table_rows(self, locator: str, rows: List[int]):
        """Select multiple table rows."""
        return self._lib.select_table_rows(locator, rows)

    def deselect_all_table_rows(self, locator: str):
        """Deselect all table rows."""
        return self._lib.deselect_all_table_rows(locator)

    def select_table_row_by_value(self, locator: str, column: int, value: str) -> int:
        """Select a table row by cell value."""
        return self._lib.select_table_row_by_value(locator, column, value)

    def select_table_row_range(self, locator: str, start_row: int, end_row: int):
        """Select a range of table rows."""
        return self._lib.select_table_row_range(locator, start_row, end_row)

    def click_table_column_header(self, locator: str, column: int):
        """Click a table column header."""
        return self._lib.click_table_column_header(locator, column)

    def get_table_columns(self, locator: str):
        """Get table column headers."""
        return self._lib.get_table_columns(locator)

    # Tree Keywords
    def expand_tree_item(self, locator: str, path: str):
        """Expand a tree item."""
        return self._lib.expand_tree_item(locator, path)

    def collapse_tree_item(self, locator: str, path: str):
        """Collapse a tree item."""
        return self._lib.collapse_tree_item(locator, path)

    def select_tree_item(self, locator: str, path: str):
        """Select a tree item."""
        return self._lib.select_tree_item(locator, path)

    def select_tree_nodes(self, locator: str, paths: List[str]):
        """Select multiple tree nodes."""
        return self._lib.select_tree_nodes(locator, paths)

    def get_tree_node_parent(self, locator: str, node_name: str) -> str:
        """Get the parent of a tree node."""
        return self._lib.get_tree_node_parent(locator, node_name)

    def get_tree_node_level(self, locator: str, node_name: str) -> int:
        """Get the level of a tree node."""
        return self._lib.get_tree_node_level(locator, node_name)

    def tree_node_exists(self, locator: str, node_name: str) -> bool:
        """Check if a tree node exists."""
        return self._lib.tree_node_exists(locator, node_name)

    def get_selected_tree_nodes(self, locator: str):
        """Get selected tree nodes."""
        return self._lib.get_selected_tree_nodes(locator)

    def deselect_all_tree_nodes(self, locator: str):
        """Deselect all tree nodes."""
        return self._lib.deselect_all_tree_nodes(locator)

    # Wait Keywords
    def wait_until_widget_exists(self, locator: str, timeout: Optional[float] = None):
        """Wait until a widget exists."""
        return self._lib.wait_until_widget_exists(locator, timeout)

    def wait_until_widget_enabled(self, locator: str, timeout: Optional[float] = None):
        """Wait until a widget is enabled."""
        return self._lib.wait_until_widget_enabled(locator, timeout)

    # Verification Keywords
    def widget_should_be_visible(self, locator: str):
        """Verify that a widget is visible."""
        return self._lib.widget_should_be_visible(locator)

    def widget_should_be_enabled(self, locator: str):
        """Verify that a widget is enabled."""
        return self._lib.widget_should_be_enabled(locator)

    def widget_text_should_be(self, locator: str, expected: str):
        """Verify widget text."""
        return self._lib.widget_text_should_be(locator, expected)

    def get_widget_property(self, locator: str, property_name: str) -> Any:
        """Get a property value from an SWT widget.

        | **Argument** | **Description** |
        | ``locator`` | Widget locator. |
        | ``property_name`` | Property name (text, enabled, visible, selection, etc.). |

        Returns the value of the specified property.

        Example:
        | ${text}=    Get Element Property    Text#input    text
        | ${enabled}=    Get Element Property    Button#save    enabled

        """
        return self._lib.get_widget_property(locator, property_name)

    # Configuration Keywords
    def set_timeout(self, timeout: float) -> float:
        """Set the default timeout."""
        self._timeout = timeout
        return self._lib.set_timeout(timeout)

    def __getattr__(self, name: str):
        """Delegate other attribute access to the underlying Rust library."""
        return getattr(self._lib, name)


class RcpLibrary(RcpKeywords):
    r"""Robot Framework library for Eclipse RCP (Rich Client Platform) application automation.

    This library provides comprehensive support for automating Eclipse RCP applications,
    including the Eclipse IDE and any application built on the Eclipse RCP framework.
    It extends SWT support with RCP-specific keywords for the workbench model:
    perspectives, views, editors, commands, and preferences.

    = What is Eclipse RCP? =

    Eclipse RCP is a platform for building and deploying rich client applications.
    Applications built on Eclipse RCP include:

    - Eclipse IDE (Java, C++, PHP development)
    - IBM Rational products
    - SAP development tools
    - Many enterprise desktop applications

    This library enables Robot Framework test automation for any Eclipse RCP application
    by providing keywords that understand the Eclipse workbench architecture.

    = Initialization =

    The library can be imported with optional default timeout:

    | **Setting** | **Value** |
    | Library | JavaGui.RcpLibrary |
    | Library | JavaGui.RcpLibrary | timeout=30 |

    For typical usage with both SWT and RCP keywords:

    | **Setting** | **Value** | **Value** |
    | Library | JavaGui.Swt | WITH NAME | SWT |
    | Library | JavaGui.Rcp | WITH NAME | RCP |

    = Eclipse Workbench Model =

    Understanding the Eclipse workbench hierarchy is essential for RCP automation.
    The workbench follows a structured architecture:

    |     Workbench (Application)
    |     └── Workbench Window (Main window)
    |          ├── Menu Bar (File, Edit, View, etc.)
    |          ├── Tool Bar (Quick access buttons)
    |          ├── Perspectives (Different layouts)
    |          │   ├── Java Perspective
    |          │   ├── Debug Perspective
    |          │   └── Resource Perspective
    |          ├── Views (Information panels)
    |          │   ├── Package Explorer
    |          │   ├── Project Explorer
    |          │   ├── Console
    |          │   ├── Problems
    |          │   ├── Outline
    |          │   └── Properties
    |          ├── Editors (Central editing area)
    |          │   ├── Java Editor
    |          │   ├── XML Editor
    |          │   ├── Text Editor
    |          │   └── Custom Editors
    |          ├── Commands (Executable actions)
    |          └── Preferences (Application settings)

    == Workbench ==

    The top-level application container. Typically one per RCP application.
    Controls the overall application lifecycle and manages windows.

    == Workbench Window ==

    The main application window containing all UI elements. An application can have
    multiple workbench windows, but typically has only one.

    == Perspectives ==

    A perspective defines the initial layout and visible views/editors for a task.
    Examples: Java, Debug, Resource, Team Synchronizing.

    - Identified by perspective ID (e.g., ``org.eclipse.jdt.ui.JavaPerspective``)
    - Can be switched, reset, or customized
    - Each perspective remembers its own layout

    == Views ==

    Views are UI panels that display information and support specific tasks.
    Examples: Package Explorer, Console, Problems, Outline.

    - Identified by view ID (e.g., ``org.eclipse.ui.navigator.ProjectExplorer``)
    - Can be shown, hidden, moved, or stacked
    - Persist within their perspective

    == Editors ==

    Editors are the central work area for editing files or resources.
    Examples: Java Editor, XML Editor, Text Editor.

    - Identified by file path or editor title
    - Support save/dirty state tracking
    - Can have multiple editors open simultaneously

    == Commands ==

    Commands are executable actions in the workbench.
    Examples: Save All, Build Project, Run Tests.

    - Identified by command ID (e.g., ``org.eclipse.ui.file.saveAll``)
    - Can be executed programmatically
    - May require parameters

    == Preferences ==

    Preferences are application settings organized in a tree structure.
    Examples: General > Appearance, Java > Compiler, Team > Git.

    - Organized by path (e.g., ``General|Appearance``)
    - Accessed through Preferences dialog

    == Connection ==

    Connect to an Eclipse RCP application using the SWT agent:

    | Connect To Application    MyApp    host=localhost    port=5679

    The RCP application must be started with the JavaGUI agent:

    ``eclipse -vmargs -javaagent:/path/to/javagui-agent.jar=port=5679``

    Or for custom RCP applications:

    ``java -javaagent:/path/to/javagui-agent.jar=port=5679 -jar myapp.jar``

    == Typical Workflows ==

    === Opening a Perspective ===

    | Open Perspective    org.eclipse.jdt.ui.JavaPerspective
    | Get Active Perspective    ==    org.eclipse.jdt.ui.JavaPerspective

    === Working with Views ===

    | # Show a view
    | Show View    org.eclipse.ui.navigator.ProjectExplorer
    |
    | # Verify view is visible
    | View Should Be Visible    org.eclipse.ui.navigator.ProjectExplorer
    |
    | # Get view title
    | Get View Title    org.eclipse.ui.navigator.ProjectExplorer    ==    Project Explorer
    |
    | # Close a view
    | Close View    org.eclipse.ui.console.ConsoleView

    === Working with Editors ===

    | # Open an editor
    | Open Editor    /workspace/MyProject/src/Main.java
    |
    | # Check if editor is dirty (has unsaved changes)
    | Is Editor Dirty    Main.java    ==    ${True}
    |
    | # Save the editor
    | Save Editor    Main.java
    |
    | # Verify editor is clean
    | Get Editor Dirty State    Main.java    ==    ${False}
    |
    | # Close editor without saving
    | Close Editor    Main.java    save=False

    === Executing Commands ===

    | # Execute a command by ID
    | Execute Command    org.eclipse.ui.file.saveAll
    |
    | # Execute build command
    | Execute Command    org.eclipse.ui.project.buildAll
    |
    | # Open quick access
    | Execute Command    org.eclipse.ui.window.quickAccess

    === Working with Preferences ===

    | # Open preferences dialog
    | Open Preferences
    |
    | # Navigate to a preference page
    | Navigate To Preference Page    General|Appearance
    |
    | # Change a preference using SWT widgets
    | SWT.Input Text    Text[name='fontSize']    12
    | SWT.Click Widget    Button[text='Apply']

    === Complete Example ===

    | *** Settings ***
    | Library    JavaGui.Swt    WITH NAME    SWT
    | Library    JavaGui.Rcp    WITH NAME    RCP
    | Suite Setup    Connect To Eclipse
    | Suite Teardown    RCP.Disconnect
    |
    | *** Test Cases ***
    | Open Java Perspective and Create Project
    |     RCP.Open Perspective    org.eclipse.jdt.ui.JavaPerspective
    |     RCP.Get Active Perspective    ==    org.eclipse.jdt.ui.JavaPerspective
    |     # Show Project Explorer
    |     RCP.Show View    org.eclipse.ui.navigator.ProjectExplorer
    |     RCP.Get Open View Count    >    0
    |     # Execute New Java Project wizard
    |     RCP.Execute Command    org.eclipse.jdt.ui.wizards.JavaProjectWizard
    |     # Fill in project details
    |     SWT.Input Text    Text[name='projectName']    MyProject
    |     SWT.Click Widget    Button[text='Finish']
    |
    | Edit Java File
    |     RCP.Open Editor    /MyProject/src/Main.java
    |     ${content}=    SWT.Get Widget Property    StyledText    text
    |     # Modify content
    |     SWT.Input Text    StyledText    ${content}\nSystem.out.println("Hello");
    |     # Verify dirty state
    |     RCP.Get Editor Dirty State    Main.java    ==    ${True}
    |     # Save and verify
    |     RCP.Execute Command    org.eclipse.ui.file.save
    |     RCP.Get Editor Dirty State    Main.java    ==    ${False}
    |
    | *** Keywords ***
    | Connect To Eclipse
    |     RCP.Connect To Application    eclipse    port=5679    timeout=30
    |     RCP.Wait For Workbench    timeout=60

    **View and Editor IDs**

    Eclipse uses unique identifiers for views, editors, perspectives, and commands.
    These IDs follow Java package naming conventions.

    *Common View IDs*

    | *ID* | *View Name* | *Description* |
    | org.eclipse.ui.navigator.ProjectExplorer | Project Explorer | Navigate project structure |
    | org.eclipse.jdt.ui.PackageExplorer | Package Explorer | Java-specific navigation |
    | org.eclipse.ui.console.ConsoleView | Console | Output and logging |
    | org.eclipse.ui.views.ProblemView | Problems | Errors and warnings |
    | org.eclipse.ui.views.ContentOutline | Outline | Document structure |
    | org.eclipse.ui.views.PropertySheet | Properties | Object properties |
    | org.eclipse.jdt.ui.TypeHierarchy | Type Hierarchy | Java type hierarchy |
    | org.eclipse.debug.ui.DebugView | Debug | Debugging information |
    | org.eclipse.debug.ui.VariableView | Variables | Variable inspection |
    | org.eclipse.debug.ui.BreakpointView | Breakpoints | Breakpoint management |
    | org.eclipse.ui.views.TaskList | Tasks | Task annotations |
    | org.eclipse.ui.views.BookmarkView | Bookmarks | Code bookmarks |

    *Common Perspective IDs*

    | *ID* | *Perspective Name* | *Purpose* |
    | org.eclipse.jdt.ui.JavaPerspective | Java | Java development |
    | org.eclipse.debug.ui.DebugPerspective | Debug | Debugging |
    | org.eclipse.ui.resourcePerspective | Resource | General resources |
    | org.eclipse.team.ui.TeamSynchronizingPerspective | Team Synchronizing | Version control |
    | org.eclipse.jdt.ui.JavaBrowsingPerspective | Java Browsing | Browse Java code |
    | org.eclipse.jdt.ui.JavaHierarchyPerspective | Java Hierarchy | Type hierarchies |

    *Common Command IDs*

    | *ID* | *Command* |
    | org.eclipse.ui.file.save | Save |
    | org.eclipse.ui.file.saveAll | Save All |
    | org.eclipse.ui.file.close | Close |
    | org.eclipse.ui.file.closeAll | Close All |
    | org.eclipse.ui.project.buildAll | Build All |
    | org.eclipse.ui.project.buildProject | Build Project |
    | org.eclipse.ui.project.cleanBuild | Clean Build |
    | org.eclipse.jdt.ui.edit.text.java.organize.imports | Organize Imports |
    | org.eclipse.jdt.ui.edit.text.java.correction.assist.proposals | Quick Fix |
    | org.eclipse.debug.ui.commands.RunLast | Run Last |
    | org.eclipse.debug.ui.commands.DebugLast | Debug Last |
    | org.eclipse.ui.window.preferences | Preferences |

    *Finding IDs*

    To find view, perspective, or command IDs:

    1. **Using Help > About > Installation Details**
       - Shows installed plugins and their IDs

    2. **Using Window > Show View > Other**
       - View names often indicate IDs

    3. **Checking plugin.xml files**
       - Contains extension point definitions with IDs

    4. **Using Get Available Commands keyword**
       | ${commands}=    Get Available Commands
       | Log Many    @{commands}

    5. **Using Get Available Perspectives keyword**
       | ${perspectives}=    Get Available Perspectives
       | Log Many    @{perspectives}

    **Assertion Engine**

    RCP keywords support inline assertions following the Browser Library pattern.
    This allows compact assertion syntax without separate verification keywords.

    *Supported Operators*

    | *Operator* | *Description* | *Example* |
    | == | Equal | value    ==    expected |
    | != | Not equal | value    !=    unexpected |
    | < | Less than | count    <    10 |
    | > | Greater than | count    >    0 |
    | <= | Less or equal | version    <=    2.0 |
    | >= | Greater or equal | version    >=    1.0 |
    | contains | String contains | text    contains    substring |
    | not contains | Does not contain | text    not contains    error |
    | starts | Starts with | path    starts    /workspace |
    | ends | Ends with | file    ends    .java |
    | matches | Regex match | id    matches    .*\.ui\..* |
    | validate | Custom validator | value    validate    ${validator} |
    | then | Value passthrough | Get X    then    Log |

    *RCP Assertion Examples*

    **Perspective Assertions**

    | # Verify active perspective
    | Get Active Perspective    ==    org.eclipse.jdt.ui.JavaPerspective
    |
    | # Check perspective ID pattern
    | Get Active Perspective    matches    org\.eclipse\.jdt\.*
    |
    | # Store and verify
    | ${perspective}=    Get Active Perspective    then    Log
    | Should Be Equal    ${perspective}    org.eclipse.jdt.ui.JavaPerspective

    **View Assertions**

    | # Check view count
    | Get Open View Count    >    0
    | Get Open View Count    <=    10
    |
    | # Verify view title
    | Get View Title    org.eclipse.ui.console.ConsoleView    ==    Console
    | Get View Title    org.eclipse.ui.navigator.ProjectExplorer    contains    Explorer
    |
    | # Check view visibility
    | View Should Be Visible    org.eclipse.ui.views.ProblemView

    **Editor Assertions**

    | # Check editor count
    | Get Open Editor Count    ==    3
    | Get Open Editor Count    >    0
    |
    | # Verify dirty state
    | Get Editor Dirty State    Main.java    ==    ${False}
    | Get Editor Dirty State    Main.java    ==    ${True}
    |
    | # Check active editor
    | ${editor}=    Get Active Editor    then    Log
    | Should Contain    ${editor}[title]    Main.java

    **Command Assertions**

    | # Get available commands
    | ${commands}=    Get Available Commands
    | Length Should Be Greater Than    ${commands}    0
    |
    | # Get commands by category
    | ${file_commands}=    Get Available Commands    category=File
    | Should Contain    ${file_commands}    org.eclipse.ui.file.save

    **Combined Assertions**

    | # Chain assertions with then
    | ${count}=    Get Open View Count    >    0    then    Log
    | ${perspective}=    Get Active Perspective    contains    eclipse    then    Log
    |
    | # Multiple inline assertions
    | Get Open Editor Count    >=    1
    | Get Editor Dirty State    Main.java    ==    ${False}
    | Get View Title    org.eclipse.ui.console.ConsoleView    ==    Console

    **Best Practices**

    *1. Wait for Workbench*

    Always wait for the workbench to be ready before automation:

    | Connect To Application    eclipse    port=5679
    | Wait For Workbench    timeout=60

    *2. Use IDs Instead of Titles*

    View and perspective IDs are stable, titles may change with localization:

    | # Good - uses ID
    | Show View    org.eclipse.ui.navigator.ProjectExplorer
    |
    | # Bad - title may change
    | SWT.Click Widget    Button[text='Project Explorer']

    *3. Verify State Before Actions*

    Check current state before performing actions:
    | ${perspective}=    Get Active Perspective
    | Run Keyword If    '${perspective}' != 'org.eclipse.jdt.ui.JavaPerspective'
    | ...    Open Perspective    org.eclipse.jdt.ui.JavaPerspective

    *4. Save or Discard Changes*

    Always handle dirty editors explicitly:

    | # Save before closing
    | Save All Editors
    | Close All Editors    save=False
    |
    | # Or discard changes
    | Close All Editors    save=False

    *5. Clean Up Views*

    Reset perspective to clean state between tests:

    | [Teardown]    Reset Test Perspective
    |
    | *** Keywords ***
    | Reset Test Perspective
    |     Reset Perspective
    |     Close All Editors    save=False

    *6. Use Commands When Possible*

    Commands are more stable than UI interactions:

    | # Good - uses command
    | Execute Command    org.eclipse.ui.file.saveAll
    |
    | # Bad - UI may change
    | Select Main Menu    File|Save All

    *7. Handle Async Operations*

    Some RCP operations are asynchronous - add waits:

    | Execute Command    org.eclipse.ui.project.buildAll
    | Sleep    2s    # Wait for build to start
    | Wait Until Widget Exists    Label[text*='Building']    timeout=5

    *8. Combine SWT and RCP Keywords*

    Use RCP for workbench model, SWT for widget interactions:

    | # RCP - Open perspective and view
    | RCP.Open Perspective    org.eclipse.jdt.ui.JavaPerspective
    | RCP.Show View    org.eclipse.ui.navigator.ProjectExplorer
    |
    | # SWT - Interact with tree widget in view
    | SWT.Expand Tree Item    Tree    MyProject
    | SWT.Select Tree Item    Tree    MyProject/src

    **Troubleshooting**

    *Connection Issues*

    **Problem:** Cannot connect to RCP application

    **Solutions:**
    - Verify agent JAR is in command line: ``-javaagent:/path/to/javagui-agent.jar=port=5679``
    - Check port is not in use: ``netstat -an | grep 5679``
    - Verify firewall allows connection
    - Try connecting with ``timeout=60`` for slow startup

    *View Not Found*

    **Problem:** View ID not recognized

    **Solutions:**
    - Use ``Get Available Views`` to list available view IDs
    - Check plugin is installed and activated
    - Use full qualified ID (e.g., ``org.eclipse.ui.console.ConsoleView``)
    - Verify view is part of current perspective

    *Command Fails*

    **Problem:** ``Execute Command`` doesn't work

    **Solutions:**
    - Use ``Get Available Commands`` to verify command ID
    - Check command requires parameters (some commands need context)
    - Verify command is enabled in current context
    - Try using menu selection instead: ``Select Main Menu    File|Save``

    *Slow Response*

    **Problem:** Keywords take too long

    **Solutions:**
    - Increase timeout: ``Set Timeout    30``
    - Wait for workbench ready: ``Wait For Workbench    timeout=60``
    - Check Eclipse is not running builds or indexing
    - Disable automatic builds: ``Execute Command    org.eclipse.ui.project.toggleAutoBuild``

    *Widget Not Found in View*

    **Problem:** Cannot find widget inside a view

    **Solutions:**
    - Activate view first: ``Activate View    view.id``
    - Use ``Get View Widget`` for view-scoped search
    - Log widget tree: ``SWT.Log Widget Tree``
    - Check view is fully loaded (may need wait)

    *Editor State Issues*

    **Problem:** Editor dirty state incorrect

    **Solutions:**
    - Add short delay after editing: ``Sleep    500ms``
    - Verify editor is active: ``Activate Editor    filename``
    - Check autosave settings (may save automatically)
    - Use command instead: ``Execute Command    org.eclipse.ui.file.save``

    *Perspective Not Opening*

    **Problem:** ``Open Perspective`` fails

    **Solutions:**
    - Verify perspective ID in available perspectives
    - Check perspective plugin is installed
    - Try closing all editors first: ``Close All Editors``
    - Reset workspace: ``Execute Command    org.eclipse.ui.window.resetPerspective``

    **See Also**

    - SwtLibrary documentation for widget interaction keywords
    - Eclipse Platform documentation: https://www.eclipse.org/platform/
    - Eclipse RCP Tutorial: https://www.vogella.com/tutorials/EclipseRCP/article.html
    - RobotFramework Browser Library assertion syntax: https://marketsquare.github.io/robotframework-browser/

    """

    ROBOT_LIBRARY_SCOPE = "GLOBAL"
    ROBOT_LIBRARY_VERSION = __version__

    def __init__(
        self,
        timeout: float = 10.0,
    ) -> None:
        """Initialize the RCP Library.

        | **Argument** | **Description** |
        | ``timeout`` | Default timeout in seconds for wait operations. Default ``10.0``. |

        Example:
        | **Setting** | **Value** | **Value** |
        | Library | JavaGui.RcpLibrary | |
        | Library | JavaGui.RcpLibrary | timeout=30 |

        """
        if not _RUST_AVAILABLE:
            raise ImportError(
                f"RCP Library Rust core not available: {_IMPORT_ERROR}\n"
                "Please ensure the library is properly installed with: pip install robotframework-javagui"
            )

        self._lib = _RcpLibrary(timeout=timeout)
        self._timeout = timeout

        # AssertionEngine configuration
        self._assertion_timeout = 5.0
        self._assertion_interval = 0.1

    # Connection Keywords (delegated from SWT)
    def connect_to_swt_application(
        self, app: str, host: str = "localhost", port: int = 5679, timeout: Optional[float] = None
    ):
        """Connect to an RCP/SWT application."""
        return self._lib.connect_to_swt_application(app, host, port, timeout)

    def connect_to_application(
        self, app: str, host: str = "localhost", port: int = 5679, timeout: Optional[float] = None
    ):
        """Connect to an RCP application (alias)."""
        return self._lib.connect_to_application(app, host, port, timeout)

    def disconnect(self):
        """Disconnect from the RCP application."""
        return self._lib.disconnect()

    def is_connected(self) -> bool:
        """Check if connected to an RCP application."""
        return self._lib.is_connected()

    # Shell Keywords
    def get_shells(self):
        """Get all shells."""
        return self._lib.get_shells()

    def activate_shell(self, locator: str):
        """Activate a shell."""
        return self._lib.activate_shell(locator)

    def close_shell(self, locator: str):
        """Close a shell."""
        return self._lib.close_shell(locator)

    # Widget Finding Keywords
    def find_widget(self, locator: str):
        """Find a single widget."""
        return self._lib.find_widget(locator)

    def find_widgets(self, locator: str):
        """Find all matching widgets."""
        return self._lib.find_widgets(locator)

    # Click Keywords
    def click_widget(self, locator: str):
        """Click on a widget."""
        return self._lib.click_widget(locator)

    def double_click_widget(self, locator: str):
        """Double-click on a widget."""
        return self._lib.double_click_widget(locator)

    # Text Input Keywords
    def input_text(self, locator: str, text: str, clear: bool = True):
        """Input text into a widget."""
        return self._lib.input_text(locator, text, clear)

    def clear_text(self, locator: str):
        """Clear text from a widget."""
        return self._lib.clear_text(locator)

    # Selection Keywords
    def select_combo_item(self, locator: str, item: str):
        """Select an item from a combo box."""
        return self._lib.select_combo_item(locator, item)

    def select_list_item(self, locator: str, item: str):
        """Select an item from a list."""
        return self._lib.select_list_item(locator, item)

    def check_button(self, locator: str):
        """Check a checkbox or toggle button."""
        return self._lib.check_button(locator)

    def uncheck_button(self, locator: str):
        """Uncheck a checkbox or toggle button."""
        return self._lib.uncheck_button(locator)

    # Table Keywords
    def get_table_row_count(self, locator: str) -> int:
        """Get the number of rows in a table."""
        return self._lib.get_table_row_count(locator)

    def get_table_cell(self, locator: str, row: int, col: int) -> str:
        """Get the value of a table cell."""
        return self._lib.get_table_cell(locator, row, col)

    def select_table_row(self, locator: str, row: int):
        """Select a table row."""
        return self._lib.select_table_row(locator, row)

    # Tree Keywords
    def expand_tree_item(self, locator: str, path: str):
        """Expand a tree item."""
        return self._lib.expand_tree_item(locator, path)

    def collapse_tree_item(self, locator: str, path: str):
        """Collapse a tree item."""
        return self._lib.collapse_tree_item(locator, path)

    def select_tree_item(self, locator: str, path: str):
        """Select a tree item."""
        return self._lib.select_tree_item(locator, path)

    # Wait Keywords
    def wait_until_widget_exists(self, locator: str, timeout: Optional[float] = None):
        """Wait until a widget exists."""
        return self._lib.wait_until_widget_exists(locator, timeout)

    def wait_until_widget_enabled(self, locator: str, timeout: Optional[float] = None):
        """Wait until a widget is enabled."""
        return self._lib.wait_until_widget_enabled(locator, timeout)

    # Verification Keywords
    def widget_should_be_visible(self, locator: str):
        """Verify that a widget is visible."""
        return self._lib.widget_should_be_visible(locator)

    def widget_should_be_enabled(self, locator: str):
        """Verify that a widget is enabled."""
        return self._lib.widget_should_be_enabled(locator)

    def widget_text_should_be(self, locator: str, expected: str):
        """Verify widget text."""
        return self._lib.widget_text_should_be(locator, expected)

    # Configuration Keywords
    def set_timeout(self, timeout: float) -> float:
        """Set the default timeout."""
        self._timeout = timeout
        return self._lib.set_timeout(timeout)

    # RCP-Specific Keywords
    def get_workbench_info(self):
        """Get workbench information."""
        return self._lib.get_workbench_info()

    def get_active_perspective(self) -> str:
        """Get the active perspective ID."""
        return self._lib.get_active_perspective()

    def open_perspective(self, perspective_id: str):
        """Open a perspective by ID."""
        return self._lib.open_perspective(perspective_id)

    def reset_perspective(self):
        """Reset the current perspective."""
        return self._lib.reset_perspective()

    def get_available_perspectives(self):
        """Get available perspectives."""
        return self._lib.get_available_perspectives()

    def show_view(self, view_id: str, secondary_id: Optional[str] = None):
        """Show a view by ID."""
        return self._lib.show_view(view_id, secondary_id)

    def close_view(self, view_id: str, secondary_id: Optional[str] = None):
        """Close a view by ID."""
        return self._lib.close_view(view_id, secondary_id)

    def activate_view(self, view_id: str):
        """Activate a view."""
        return self._lib.activate_view(view_id)

    def view_should_be_visible(self, view_id: str):
        """Verify view is visible."""
        return self._lib.view_should_be_visible(view_id)

    def get_open_views(self):
        """Get open views."""
        return self._lib.get_open_views()

    def get_view_widget(self, view_id: str, locator: str):
        """Get a widget in a view."""
        return self._lib.get_view_widget(view_id, locator)

    def get_active_editor(self):
        """Get the active editor."""
        return self._lib.get_active_editor()

    def get_open_editors(self):
        """Get all open editors.

        Returns a list of open editors with their titles and dirty state.

        Example:
        | ${editors}=    Get Open Editors
        | FOR    ${editor}    IN    @{editors}
        |     Log    ${editor}[title] - Dirty: ${editor}[dirty]
        | END

        """
        return self._lib.get_open_editors()

    def open_editor(self, file_path: str):
        """Open an editor for a file."""
        return self._lib.open_editor(file_path)

    def close_editor(self, title: str, save: bool = False):
        """Close an editor."""
        return self._lib.close_editor(title, save)

    def close_all_editors(self, save: bool = False) -> bool:
        """Close all editors."""
        return self._lib.close_all_editors(save)

    def save_editor(self, title: Optional[str] = None):
        """Save an editor."""
        return self._lib.save_editor(title)

    def save_all_editors(self):
        """Save all editors."""
        return self._lib.save_all_editors()

    def activate_editor(self, title: str):
        """Activate an editor."""
        return self._lib.activate_editor(title)

    def is_editor_dirty(self, file_path: str) -> bool:
        """Check if an editor has unsaved changes."""
        return self._lib.is_editor_dirty(file_path)

    def editor_should_be_dirty(self, file_path: str):
        """Verify that an editor has unsaved changes."""
        return self._lib.editor_should_be_dirty(file_path)

    def editor_should_not_be_dirty(self, file_path: str):
        """Verify that an editor has no unsaved changes."""
        return self._lib.editor_should_not_be_dirty(file_path)

    def get_editor_widget(self, title: str, locator: str):
        """Find a widget within an editor."""
        return self._lib.get_editor_widget(title, locator)

    def execute_command(self, command_id: str):
        """Execute an Eclipse command."""
        return self._lib.execute_command(command_id)

    def get_available_commands(self, category: Optional[str] = None):
        """Get available commands."""
        return self._lib.get_available_commands(category)

    def click_toolbar_item(self, tooltip: str):
        """Click a toolbar item."""
        return self._lib.click_toolbar_item(tooltip)

    def open_preferences(self):
        """Open preferences dialog."""
        return self._lib.open_preferences()

    def navigate_to_preference_page(self, path: str):
        """Navigate to a preference page."""
        return self._lib.navigate_to_preference_page(path)

    def select_main_menu(self, path: str):
        """Select main menu item."""
        return self._lib.select_main_menu(path)

    def select_context_menu(self, locator: str, path: str):
        """Select context menu item."""
        return self._lib.select_context_menu(locator, path)

    def wait_for_workbench(self, timeout: Optional[float] = None):
        """Wait for workbench to be ready."""
        return self._lib.wait_for_workbench(timeout)

    def __getattr__(self, name: str):
        """Delegate other attribute access to the underlying Rust library."""
        return getattr(self._lib, name)


# ==========================================================================
# Robot Framework Class Aliases
# ==========================================================================
# These aliases point to the Python wrapper classes (not the Rust classes)
# so that Robot Framework can properly introspect constructor signatures.
#
# Usage in Robot Framework:
#     Library    JavaGui.Swing    timeout=15
#     Library    JavaGui.Swt      timeout=30
#     Library    JavaGui.Rcp      timeout=20

if _RUST_AVAILABLE:
    Swing = SwingLibrary
    Swt = SwtLibrary
    Rcp = RcpLibrary
else:
    Swing = None
    Swt = None
    Rcp = None
