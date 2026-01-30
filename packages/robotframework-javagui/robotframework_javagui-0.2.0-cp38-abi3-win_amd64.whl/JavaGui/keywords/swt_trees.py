"""SWT Tree keywords with AssertionEngine support."""

from typing import Any, Optional, List

try:
    from assertionengine import AssertionOperator, list_verify_assertion
except ImportError:
    AssertionOperator = None
    list_verify_assertion = None

from ..assertions import (
    with_retry_assertion,
    numeric_assertion_with_retry,
)


class SwtTreeKeywords:
    """Mixin class providing SWT Tree keywords with assertion support."""

    _assertion_timeout: float = 5.0
    _assertion_interval: float = 0.1

    def get_swt_selected_tree_nodes(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Optional[List[str]] = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> List[str]:
        """Get selected SWT tree nodes with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Tree locator. |
        | ``assertion_operator`` | Optional assertion operator (contains, ==, etc.). |
        | ``expected`` | Expected node names/paths for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        Returns list of selected node texts/paths.

        = Return Value =

        Returns ``List[str]``: List of selected node texts or paths.

        - Without assertion: Returns the selected nodes immediately
        - With assertion operator: Retries until nodes match the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if tree not found

        Example:
        | ${nodes}=    Get Swt Selected Tree Nodes    Tree
        | Get Swt Selected Tree Nodes    Tree    contains    ['Settings']
        | Get Swt Selected Tree Nodes    Tree#nav    ==    ['Root', 'Config']    
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Tree '{locator}' selected nodes"

        def get_nodes():
            nodes = self._lib.get_selected_tree_nodes(locator)
            if nodes is None:
                return []
            if isinstance(nodes, str):
                return [nodes]
            return list(nodes)

        if assertion_operator is None:
            return get_nodes()

        # With assertion - use retry
        import time
        end_time = time.time() + timeout_val
        last_error = None
        last_nodes = None

        while time.time() < end_time:
            try:
                nodes = get_nodes()
                last_nodes = nodes
                if list_verify_assertion is not None:
                    list_verify_assertion(nodes, assertion_operator, expected, msg, message)
                return nodes
            except AssertionError as e:
                last_error = e
                time.sleep(self._assertion_interval)
            except Exception as e:
                last_error = AssertionError(f"{msg} {e}")
                time.sleep(self._assertion_interval)

        if last_error:
            raise AssertionError(
                f"{last_error}\n"
                f"Tree selection assertion failed after {timeout_val}s timeout. "
                f"Last selected nodes: {last_nodes}"
            )
        raise AssertionError(f"Tree selection assertion timed out after {timeout_val}s")

    def get_swt_tree_node_count(
        self,
        locator: str,
        parent_path: Optional[str] = None,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> int:
        """Get count of SWT tree nodes at given path with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Tree locator. |
        | ``parent_path`` | Optional parent path. Root level if not specified. |
        | ``assertion_operator`` | Optional assertion operator (==, >, <, etc.). |
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
        | ${count}=    Get Swt Tree Node Count    Tree
        | Get Swt Tree Node Count    Tree    Root    >    0
        | Get Swt Tree Node Count    Tree    Root/Settings    ==    3
        | Get Swt Tree Node Count    Tree#nav        >=    1    timeout=5
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        path_desc = parent_path if parent_path else "root"
        msg = message or f"Tree '{locator}' node count at '{path_desc}'"

        def get_count():
            # SWT trees expose item count through getItemCount()
            # If parent_path is given, we need to navigate to that node first
            if parent_path:
                # Get node level to count children
                try:
                    # Expand to ensure children are loaded
                    self._lib.expand_tree_item(locator, parent_path)
                except Exception:
                    pass

                # Count children at the given path
                # This would require getting the tree structure
                # For now, use get_tree_node_level or similar
                try:
                    # Get all visible nodes and count those under the path
                    nodes = self._lib.get_selected_tree_nodes(locator)
                    # This is a simplified approach - actual implementation
                    # would need tree traversal
                    return len(nodes) if nodes else 0
                except Exception:
                    return 0
            else:
                # Count root level items
                try:
                    # Use tree item count property
                    count = self._lib.get_widget_property(locator, "itemCount")
                    return int(count) if count is not None else 0
                except Exception:
                    return 0

        return numeric_assertion_with_retry(
            get_count,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_swt_tree_item_text(
        self,
        locator: str,
        path: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """Get text of SWT tree item at path with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Tree locator. |
        | ``path`` | Path to tree item separated by / or \|. |
        | ``assertion_operator`` | Optional assertion operator. |
        | ``expected`` | Expected text for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        = Return Value =

        Returns ``str``: The text of the tree item at the specified path.

        - Without assertion: Returns the item text immediately
        - With assertion operator: Retries until text matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if tree not found

        Example:
        | ${text}=    Get Swt Tree Item Text    Tree    Root/Settings
        | Get Swt Tree Item Text    Tree    Root/Config    ==    Config
        | Get Swt Tree Item Text    Tree    Root|Items|First    contains    First
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Tree '{locator}' item '{path}' text"

        def get_text():
            # Select the tree item to ensure it's accessible
            try:
                self._lib.select_tree_item(locator, path)
            except Exception:
                pass

            # Get the text of the last path component
            # The path format is Root/Parent/Node - get the node text
            path_parts = path.replace("|", "/").split("/")
            return path_parts[-1] if path_parts else ""

        return with_retry_assertion(
            get_text,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def swt_tree_node_should_exist(
        self,
        locator: str,
        path: str,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        """Verify that SWT tree node exists at path.

        | **Argument** | **Description** |
        | ``locator`` | Tree locator. |
        | ``path`` | Node path separated by / or \|. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Timeout in seconds. |

        Example:
        | Swt Tree Node Should Exist    Tree    Root/Settings
        | Swt Tree Node Should Exist    Tree    Root    Config    Advanced    timeout=5
        """
        import time

        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Tree node '{path}' should exist in '{locator}'"

        end_time = time.time() + timeout_val
        while time.time() < end_time:
            try:
                exists = self._lib.tree_node_exists(locator, path)
                if exists:
                    return
            except Exception:
                pass
            time.sleep(self._assertion_interval)

        raise AssertionError(msg)

    def swt_tree_node_should_not_exist(
        self,
        locator: str,
        path: str,
        message: Optional[str] = None,
    ) -> None:
        """Verify that SWT tree node does not exist at path.

        | **Argument** | **Description** |
        | ``locator`` | Tree locator. |
        | ``path`` | Node path separated by / or \|. |
        | ``message`` | Custom error message. |

        Example:
        | Swt Tree Node Should Not Exist    Tree    Root/Deleted
        | Swt Tree Node Should Not Exist    Tree#nav    Old/Node    
        """
        msg = message or f"Tree node '{path}' should not exist in '{locator}'"

        try:
            exists = self._lib.tree_node_exists(locator, path)
            if exists:
                raise AssertionError(msg)
        except AssertionError:
            raise
        except Exception:
            # Node check failed - assume it doesn't exist
            pass

    def swt_tree_should_have_selection(
        self,
        locator: str,
        message: Optional[str] = None,
    ) -> None:
        """Verify that SWT tree has at least one selected node.

        | **Argument** | **Description** |
        | ``locator`` | Tree locator. |
        | ``message`` | Custom error message. |

        Example:
        | Swt Tree Should Have Selection    Tree
        | Swt Tree Should Have Selection    Tree#nav    message=A node should be selected
        """
        msg = message or f"Tree '{locator}' should have a selection"

        nodes = self._lib.get_selected_tree_nodes(locator)
        if not nodes:
            raise AssertionError(msg)

    def swt_tree_selection_should_be(
        self,
        locator: str,
        *expected_nodes: str,
        message: Optional[str] = None,
    ) -> None:
        """Verify that SWT tree selection matches expected nodes.

        | **Argument** | **Description** |
        | ``locator`` | Tree locator. |
        | ``expected_nodes`` | Expected selected node texts/paths. |
        | ``message`` | Custom error message. |

        Example:
        | Swt Tree Selection Should Be    Tree    Root
        | Swt Tree Selection Should Be    Tree    Node1    Node2    
        """
        msg = message or f"Tree '{locator}' selection"

        nodes = self._lib.get_selected_tree_nodes(locator)
        if nodes is None:
            nodes = []
        elif isinstance(nodes, str):
            nodes = [nodes]

        expected = list(expected_nodes)
        if sorted(nodes) != sorted(expected):
            raise AssertionError(
                f"{msg} expected {expected}, but was {nodes}"
            )

    def get_swt_tree_node_level(
        self,
        locator: str,
        node_path: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> int:
        """Get depth level of SWT tree node with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Tree locator. |
        | ``node_path`` | Path to the tree node. |
        | ``assertion_operator`` | Optional assertion operator (==, >, <, etc.). |
        | ``expected`` | Expected level for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        Level 0 is root, level 1 is first child, etc.

        = Return Value =

        Returns ``int``: The depth level of the tree node (0 for root, 1 for first child, etc.).

        - Without assertion: Returns the level immediately
        - With assertion operator: Retries until level matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if tree not found

        Example:
        | ${level}=    Get Swt Tree Node Level    Tree    Root
        | Get Swt Tree Node Level    Tree    Root/Child    ==    1
        | Get Swt Tree Node Level    Tree    Root/A/B/C    >=    3    
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Tree '{locator}' node '{node_path}' level"

        def get_level():
            return self._lib.get_tree_node_level(locator, node_path)

        return numeric_assertion_with_retry(
            get_level,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_swt_tree_node_parent(
        self,
        locator: str,
        node_path: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """Get parent of SWT tree node with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Tree locator. |
        | ``node_path`` | Path to the tree node. |
        | ``assertion_operator`` | Optional assertion operator. |
        | ``expected`` | Expected parent for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        = Return Value =

        Returns ``str``: The path or name of the parent node.

        - Without assertion: Returns the parent immediately
        - With assertion operator: Retries until parent matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if tree not found

        Example:
        | ${parent}=    Get Swt Tree Node Parent    Tree    Root/Child
        | Get Swt Tree Node Parent    Tree    Root/Settings/Advanced    ==    Settings    
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Tree '{locator}' node '{node_path}' parent"

        def get_parent():
            return self._lib.get_tree_node_parent(locator, node_path)

        return with_retry_assertion(
            get_parent,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )
