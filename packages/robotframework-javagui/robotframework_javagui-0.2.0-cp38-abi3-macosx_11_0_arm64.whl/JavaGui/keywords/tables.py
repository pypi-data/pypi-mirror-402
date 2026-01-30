"""Table, Tree, and List keywords with AssertionEngine support."""

from typing import Any, Optional, List, Dict, Union
from assertionengine import AssertionOperator, list_verify_assertion

from ..assertions import (
    with_retry_assertion,
    numeric_assertion_with_retry,
)


class TableKeywords:
    """Mixin class providing Table keywords with assertion support."""

    _assertion_timeout: float = 5.0
    _assertion_interval: float = 0.1

    def get_table_cell_value(
        self,
        locator: str,
        row: int,
        column: Union[int, str],
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """Get table cell value with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Table locator. |
        | ``row`` | Row index (0-based). |
        | ``column`` | Column index (0-based) or column name. |
        | ``assertion_operator`` | Optional assertion operator. |
        | ``expected`` | Expected value for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        = Return Value =

        Returns ``str``: The value of the table cell.

        - Without assertion: Returns the cell value immediately
        - With assertion operator: Retries until value matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if table not found

        Example:
        | ${value}=    Get Table Cell Value    JTable    0    1
        | Get Table Cell Value    JTable    0    Name    ==    John
        | Get Table Cell Value    JTable#users    2    Status    contains    Active
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Table '{locator}' cell [{row}, {column}]"

        def get_cell():
            return self._lib.get_table_cell_value(locator, row, str(column))

        return with_retry_assertion(
            get_cell,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_table_row_count(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> int:
        """Get table row count with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Table locator. |
        | ``assertion_operator`` | Optional assertion operator (==, >, <, etc.). |
        | ``expected`` | Expected count for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        = Return Value =

        Returns ``int``: The number of rows in the table.

        - Without assertion: Returns the row count immediately
        - With assertion operator: Retries until count matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if table not found

        Example:
        | ${count}=    Get Table Row Count    JTable
        | Get Table Row Count    JTable    ==    10
        | Get Table Row Count    JTable#users    >    0
        | Get Table Row Count    JTable    >=    5    timeout=10
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Table '{locator}' row count"

        def get_count():
            return self._lib.get_table_row_count(locator)

        return numeric_assertion_with_retry(
            get_count,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_table_column_count(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> int:
        """Get table column count with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Table locator. |
        | ``assertion_operator`` | Optional assertion operator (==, >, <, etc.). |
        | ``expected`` | Expected count for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        = Return Value =

        Returns ``int``: The number of columns in the table.

        - Without assertion: Returns the column count immediately
        - With assertion operator: Retries until count matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if table not found

        Example:
        | ${count}=    Get Table Column Count    JTable
        | Get Table Column Count    JTable    ==    5
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Table '{locator}' column count"

        def get_count():
            return self._lib.get_table_column_count(locator)

        return numeric_assertion_with_retry(
            get_count,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_table_row_values(
        self,
        locator: str,
        row: int,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Optional[List[str]] = None,
        message: Optional[str] = None,
    ) -> List[str]:
        """Get all values from a table row with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Table locator. |
        | ``row`` | Row index (0-based). |
        | ``assertion_operator`` | Optional assertion operator (==, contains, etc.). |
        | ``expected`` | Expected values list for assertion. |
        | ``message`` | Custom error message. |

        = Return Value =

        Returns ``List[str]``: List of values from all cells in the row.

        - Without assertion: Returns the row values immediately (no retry)
        - With assertion operator: Verifies values match the assertion immediately (no retry)
        - Raises ``AssertionError`` if assertion fails
        - Raises ``ElementNotFoundError`` if table not found

        Example:
        | ${values}=    Get Table Row Values    JTable    0
        | Get Table Row Values    JTable    0    ==    ['John', 'Doe', '30']
        | Get Table Row Values    JTable    1    contains    ['Active']    
        """
        msg = message or f"Table '{locator}' row {row} values"

        col_count = self._lib.get_table_column_count(locator)
        values = []
        for col in range(col_count):
            value = self._lib.get_table_cell_value(locator, row, str(col))
            values.append(value)

        if assertion_operator is not None:
            list_verify_assertion(values, assertion_operator, expected, msg, message)

        return values

    def get_table_column_values(
        self,
        locator: str,
        column: Union[int, str],
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Optional[List[str]] = None,
        message: Optional[str] = None,
    ) -> List[str]:
        """Get all values from a table column with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Table locator. |
        | ``column`` | Column index (0-based) or column name. |
        | ``assertion_operator`` | Optional assertion operator (==, contains, etc.). |
        | ``expected`` | Expected values list for assertion. |
        | ``message`` | Custom error message. |

        = Return Value =

        Returns ``List[str]``: List of values from all cells in the column.

        - Without assertion: Returns the column values immediately (no retry)
        - With assertion operator: Verifies values match the assertion immediately (no retry)
        - Raises ``AssertionError`` if assertion fails
        - Raises ``ElementNotFoundError`` if table not found

        Example:
        | ${values}=    Get Table Column Values    JTable    0
        | Get Table Column Values    JTable    Name    contains    ['John']    
        """
        msg = message or f"Table '{locator}' column {column} values"

        row_count = self._lib.get_table_row_count(locator)
        values = []
        for row in range(row_count):
            value = self._lib.get_table_cell_value(locator, row, str(column))
            values.append(value)

        if assertion_operator is not None:
            list_verify_assertion(values, assertion_operator, expected, msg, message)

        return values

    def get_selected_table_rows(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Optional[List[int]] = None,
        message: Optional[str] = None,
    ) -> List[int]:
        """Get selected table row indices with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Table locator. |
        | ``assertion_operator`` | Optional assertion operator. |
        | ``expected`` | Expected row indices for assertion. |
        | ``message`` | Custom error message. |

        = Return Value =

        Returns ``List[int]``: List of selected row indices (0-based).

        - Without assertion: Returns the selected row indices immediately (no retry)
        - With assertion operator: Verifies indices match the assertion immediately (no retry)
        - Raises ``AssertionError`` if assertion fails
        - Raises ``ElementNotFoundError`` if table not found

        Example:
        | ${rows}=    Get Selected Table Rows    JTable
        | Get Selected Table Rows    JTable    contains    [0, 2]
        """
        msg = message or f"Table '{locator}' selected rows"

        # Get selected rows via property
        try:
            selected = self._lib.get_element_property(locator, "selectedRows")
            if selected is None:
                selected = []
            elif isinstance(selected, int):
                selected = [selected]
        except Exception:
            selected = []

        if assertion_operator is not None:
            list_verify_assertion(selected, assertion_operator, expected, msg, message)

        return selected


class TreeKeywords:
    """Mixin class providing Tree keywords with assertion support."""

    _assertion_timeout: float = 5.0
    _assertion_interval: float = 0.1

    def get_selected_tree_node(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Optional[str]:
        """Get selected tree node path with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Tree locator. |
        | ``assertion_operator`` | Optional assertion operator. |
        | ``expected`` | Expected path for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        = Return Value =

        Returns ``Optional[str]``: Path to the selected tree node, or None if no selection.

        - Without assertion: Returns the selected node path immediately
        - With assertion operator: Retries until path matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if tree not found

        Example:
        | ${path}=    Get Selected Tree Node    JTree
        | Get Selected Tree Node    JTree    ==    Root/Settings
        | Get Selected Tree Node    JTree#nav    contains    Config    
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Tree '{locator}' selected node"

        def get_node():
            return self._lib.get_selected_tree_node(locator)

        return with_retry_assertion(
            get_node,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_tree_node_count(
        self,
        locator: str,
        path: Optional[str] = None,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> int:
        """Get count of child nodes at path with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Tree locator. |
        | ``path`` | Optional path to parent node. Root if not specified. |
        | ``assertion_operator`` | Optional assertion operator. |
        | ``expected`` | Expected count for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        = Return Value =

        Returns ``int``: The count of child nodes at the specified path.

        - Without assertion: Returns the node count immediately
        - With assertion operator: Retries until count matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if tree not found

        Example:
        | ${count}=    Get Tree Node Count    JTree    Root
        | Get Tree Node Count    JTree    Root/Settings    >    0
        | Get Tree Node Count    JTree        ==    3    
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Tree '{locator}' node count at '{path or 'root'}'"

        def get_count():
            # Get tree data and count children at path
            tree_data = self._lib.get_tree_data(locator)
            if not tree_data:
                return 0
            if path:
                # Navigate to path and count children
                node = self._navigate_tree_path(tree_data, path)
                if node:
                    return len(node.get("children", []))
                return 0
            return len(tree_data.get("children", []))

        return numeric_assertion_with_retry(
            get_count,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_tree_node_children(
        self,
        locator: str,
        path: Optional[str] = None,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Optional[List[str]] = None,
        message: Optional[str] = None,
    ) -> List[str]:
        """Get child node names at path with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Tree locator. |
        | ``path`` | Optional path to parent node. Root if not specified. |
        | ``assertion_operator`` | Optional assertion operator. |
        | ``expected`` | Expected child names for assertion. |
        | ``message`` | Custom error message. |

        = Return Value =

        Returns ``List[str]``: List of child node names at the specified path.

        - Without assertion: Returns the child names immediately (no retry)
        - With assertion operator: Verifies names match the assertion immediately (no retry)
        - Raises ``AssertionError`` if assertion fails
        - Raises ``ElementNotFoundError`` if tree not found

        Example:
        | ${children}=    Get Tree Node Children    JTree    Root
        | Get Tree Node Children    JTree    Root    contains    ['Settings']    
        """
        msg = message or f"Tree '{locator}' children at '{path or 'root'}'"

        tree_data = self._lib.get_tree_data(locator)
        if not tree_data:
            children = []
        elif path:
            node = self._navigate_tree_path(tree_data, path)
            if node:
                children = [child.get("text", "") for child in node.get("children", [])]
            else:
                children = []
        else:
            children = [child.get("text", "") for child in tree_data.get("children", [])]

        if assertion_operator is not None:
            list_verify_assertion(children, assertion_operator, expected, msg, message)

        return children

    def tree_node_should_exist(
        self,
        locator: str,
        path: str,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        """Verify that a tree node exists at path.

        | **Argument** | **Description** |
        | ``locator`` | Tree locator. |
        | ``path`` | Node path separated by / or \|. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Timeout in seconds. |

        Example:
        | Tree Node Should Exist    JTree    Root/Settings
        | Tree Node Should Exist    JTree    Root    Config    Advanced    timeout=5
        """
        import time
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Tree node '{path}' should exist in '{locator}'"

        end_time = time.time() + timeout_val
        while time.time() < end_time:
            tree_data = self._lib.get_tree_data(locator)
            if tree_data:
                node = self._navigate_tree_path(tree_data, path)
                if node is not None:
                    return
            time.sleep(self._assertion_interval)

        raise AssertionError(msg)

    def tree_node_should_not_exist(
        self,
        locator: str,
        path: str,
        message: Optional[str] = None,
    ) -> None:
        """Verify that a tree node does not exist at path.

        | **Argument** | **Description** |
        | ``locator`` | Tree locator. |
        | ``path`` | Node path separated by / or \|. |
        | ``message`` | Custom error message. |

        Example:
        | Tree Node Should Not Exist    JTree    Root/Deleted    
        """
        msg = message or f"Tree node '{path}' should not exist in '{locator}'"

        tree_data = self._lib.get_tree_data(locator)
        if tree_data:
            node = self._navigate_tree_path(tree_data, path)
            if node is not None:
                raise AssertionError(msg)

    def _navigate_tree_path(self, node: dict, path: str) -> Optional[dict]:
        """Navigate to a node by path."""
        parts = path.replace("|", "/").split("/")
        current = node

        for part in parts:
            if not part:
                continue
            if current.get("text") == part:
                continue
            found = False
            for child in current.get("children", []):
                if child.get("text") == part:
                    current = child
                    found = True
                    break
            if not found:
                return None
        return current


class ListKeywords:
    """Mixin class providing List/ComboBox keywords with assertion support."""

    _assertion_timeout: float = 5.0
    _assertion_interval: float = 0.1

    def get_selected_list_item(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """Get selected list item with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | List or ComboBox locator. |
        | ``assertion_operator`` | Optional assertion operator. |
        | ``expected`` | Expected value for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        = Return Value =

        Returns ``str``: The text of the selected list item.

        - Without assertion: Returns the selected item immediately
        - With assertion operator: Retries until item matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if list not found

        Example:
        | ${item}=    Get Selected List Item    JList#items
        | Get Selected List Item    JList    ==    Option A
        | Get Selected List Item    JComboBox#country    ==    USA    
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"List '{locator}' selected item"

        def get_item():
            return self._lib.get_element_property(locator, "selectedValue")

        return with_retry_assertion(
            get_item,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_selected_list_items(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Optional[List[str]] = None,
        message: Optional[str] = None,
    ) -> List[str]:
        """Get all selected list items with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | List locator (supports multi-selection). |
        | ``assertion_operator`` | Optional assertion operator. |
        | ``expected`` | Expected values for assertion. |
        | ``message`` | Custom error message. |

        = Return Value =

        Returns ``List[str]``: List of all selected list item texts.

        - Without assertion: Returns the selected items immediately (no retry)
        - With assertion operator: Verifies items match the assertion immediately (no retry)
        - Raises ``AssertionError`` if assertion fails
        - Raises ``ElementNotFoundError`` if list not found

        Example:
        | ${items}=    Get Selected List Items    JList#items
        | Get Selected List Items    JList    contains    ['A', 'B']
        """
        msg = message or f"List '{locator}' selected items"

        try:
            selected = self._lib.get_element_property(locator, "selectedValues")
            if selected is None:
                selected = []
            elif isinstance(selected, str):
                selected = [selected]
        except Exception:
            # Fallback to single selection
            try:
                item = self._lib.get_element_property(locator, "selectedValue")
                selected = [item] if item else []
            except Exception:
                selected = []

        if assertion_operator is not None:
            list_verify_assertion(selected, assertion_operator, expected, msg, message)

        return selected

    def get_list_items(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Optional[List[str]] = None,
        message: Optional[str] = None,
    ) -> List[str]:
        """Get all list items with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | List or ComboBox locator. |
        | ``assertion_operator`` | Optional assertion operator. |
        | ``expected`` | Expected items for assertion. |
        | ``message`` | Custom error message. |

        = Return Value =

        Returns ``List[str]``: List of all item texts in the list.

        - Without assertion: Returns the items immediately (no retry)
        - With assertion operator: Verifies items match the assertion immediately (no retry)
        - Raises ``AssertionError`` if assertion fails
        - Raises ``ElementNotFoundError`` if list not found

        Example:
        | ${items}=    Get List Items    JList#options
        | Get List Items    JList    ==    ['A', 'B', 'C']
        | Get List Items    JList    contains    ['A']    
        """
        msg = message or f"List '{locator}' items"

        items = self._lib.get_list_items(locator)

        if assertion_operator is not None:
            list_verify_assertion(items, assertion_operator, expected, msg, message)

        return items

    def get_list_item_count(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> int:
        """Get list item count with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | List or ComboBox locator. |
        | ``assertion_operator`` | Optional assertion operator. |
        | ``expected`` | Expected count for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        = Return Value =

        Returns ``int``: The count of items in the list.

        - Without assertion: Returns the count immediately
        - With assertion operator: Retries until count matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if list not found

        Example:
        | ${count}=    Get List Item Count    JList
        | Get List Item Count    JList    >    0
        | Get List Item Count    JComboBox    ==    5    
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"List '{locator}' item count"

        def get_count():
            items = self._lib.get_list_items(locator)
            return len(items)

        return numeric_assertion_with_retry(
            get_count,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_selected_list_index(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> int:
        """Get selected list item index with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | List or ComboBox locator. |
        | ``assertion_operator`` | Optional assertion operator. |
        | ``expected`` | Expected index for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        = Return Value =

        Returns ``int``: The index of the selected item (0-based), or -1 if no selection.

        - Without assertion: Returns the index immediately
        - With assertion operator: Retries until index matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if list not found

        Example:
        | ${index}=    Get Selected List Index    JList
        | Get Selected List Index    JList    ==    0
        | Get Selected List Index    JComboBox    >=    0    
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"List '{locator}' selected index"

        def get_index():
            try:
                return self._lib.get_element_property(locator, "selectedIndex")
            except Exception:
                return -1

        return numeric_assertion_with_retry(
            get_index,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def list_should_contain(
        self,
        locator: str,
        value: str,
        message: Optional[str] = None,
    ) -> None:
        """Verify that list contains a specific item.

        | **Argument** | **Description** |
        | ``locator`` | List or ComboBox locator. |
        | ``value`` | Value that should be in the list. |
        | ``message`` | Custom error message. |

        Example:
        | List Should Contain    JList#options    Option A
        | List Should Contain    JComboBox#country    USA    
        """
        msg = message or f"List '{locator}' should contain '{value}'"

        items = self._lib.get_list_items(locator)
        if value not in items:
            raise AssertionError(f"{msg}. Available items: {items}")

    def list_should_not_contain(
        self,
        locator: str,
        value: str,
        message: Optional[str] = None,
    ) -> None:
        """Verify that list does not contain a specific item.

        | **Argument** | **Description** |
        | ``locator`` | List or ComboBox locator. |
        | ``value`` | Value that should not be in the list. |
        | ``message`` | Custom error message. |

        Example:
        | List Should Not Contain    JList#options    Deleted    
        """
        msg = message or f"List '{locator}' should not contain '{value}'"

        items = self._lib.get_list_items(locator)
        if value in items:
            raise AssertionError(msg)

    def list_selection_should_be(
        self,
        locator: str,
        *expected_values: str,
        message: Optional[str] = None,
    ) -> None:
        """Verify the list selection matches expected values.

        | **Argument** | **Description** |
        | ``locator`` | List locator. |
        | ``expected_values`` | Expected selected values. |
        | ``message`` | Custom error message. |

        Example:
        | List Selection Should Be    JList    Item A
        | List Selection Should Be    JList    Item A    Item B    
        """
        msg = message or f"List '{locator}' selection"

        selected = self.get_selected_list_items(locator)
        expected = list(expected_values)

        if sorted(selected) != sorted(expected):
            raise AssertionError(
                f"{msg} expected {expected}, but was {selected}"
            )
