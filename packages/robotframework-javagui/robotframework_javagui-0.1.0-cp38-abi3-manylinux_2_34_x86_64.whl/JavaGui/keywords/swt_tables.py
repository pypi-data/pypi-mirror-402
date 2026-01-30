"""SWT Table keywords with AssertionEngine support."""

from typing import Any, Optional, List, Union

try:
    from assertionengine import AssertionOperator, list_verify_assertion
except ImportError:
    AssertionOperator = None
    list_verify_assertion = None

from ..assertions import (
    with_retry_assertion,
    numeric_assertion_with_retry,
)


class SwtTableKeywords:
    """Mixin class providing SWT Table keywords with assertion support."""

    _assertion_timeout: float = 5.0
    _assertion_interval: float = 0.1

    def get_swt_table_row_count(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> int:
        """Get SWT table row count with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Table locator. |
        | ``assertion_operator`` | Optional assertion operator (==, >, <, etc.). |
        | ``expected`` | Expected count for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        = Return Value =

        Returns ``int``: The number of rows in the SWT table.

        - Without assertion: Returns the row count immediately
        - With assertion operator: Retries until count matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if table not found

        Example:
        | ${count}=    Get Swt Table Row Count    Table
        | Get Swt Table Row Count    Table    ==    10
        | Get Swt Table Row Count    Table#users    >    0
        | Get Swt Table Row Count    Table    >=    5    timeout=10
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

    def get_swt_table_cell(
        self,
        locator: str,
        row: int,
        column: Union[int, str],
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """Get SWT table cell value with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Table locator. |
        | ``row`` | Row index (0-based). |
        | ``column`` | Column index (0-based). |
        | ``assertion_operator`` | Optional assertion operator. |
        | ``expected`` | Expected value for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        = Return Value =

        Returns ``str``: The value of the SWT table cell.

        - Without assertion: Returns the cell value immediately
        - With assertion operator: Retries until value matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if table not found

        Example:
        | ${value}=    Get Swt Table Cell    Table    0    1
        | Get Swt Table Cell    Table    0    0    ==    John
        | Get Swt Table Cell    Table#users    2    1    contains    Active
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        col_index = int(column) if isinstance(column, str) and column.isdigit() else column
        msg = message or f"Table '{locator}' cell [{row}, {col_index}]"

        def get_cell():
            return self._lib.get_table_cell(locator, row, col_index)

        return with_retry_assertion(
            get_cell,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_swt_table_row_values(
        self,
        locator: str,
        row: int,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Optional[List[str]] = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> List[str]:
        """Get all values from an SWT table row with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Table locator. |
        | ``row`` | Row index (0-based). |
        | ``assertion_operator`` | Optional assertion operator (==, contains, etc.). |
        | ``expected`` | Expected values list for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        = Return Value =

        Returns ``List[str]``: List of values from all cells in the SWT table row.

        - Without assertion: Returns the row values immediately
        - With assertion operator: Retries until values match the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if table not found

        Example:
        | ${values}=    Get Swt Table Row Values    Table    0
        | Get Swt Table Row Values    Table    0    ==    ['John', 'Doe', '30']
        | Get Swt Table Row Values    Table    1    contains    ['Active']    
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Table '{locator}' row {row} values"

        def get_values():
            return self._lib.get_table_row_values(locator, row)

        if assertion_operator is None:
            return get_values()

        # With assertion - use retry
        import time
        end_time = time.time() + timeout_val
        last_error = None
        last_values = None

        while time.time() < end_time:
            try:
                values = get_values()
                last_values = values
                if list_verify_assertion is not None:
                    list_verify_assertion(values, assertion_operator, expected, msg, message)
                return values
            except AssertionError as e:
                last_error = e
                time.sleep(self._assertion_interval)
            except Exception as e:
                last_error = AssertionError(f"{msg} {e}")
                time.sleep(self._assertion_interval)

        if last_error:
            raise AssertionError(
                f"{last_error}\n"
                f"Table row assertion failed after {timeout_val}s timeout. "
                f"Last values: {last_values}"
            )
        raise AssertionError(f"Table row assertion timed out after {timeout_val}s")

    def get_swt_table_column_count(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> int:
        """Get SWT table column count with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Table locator. |
        | ``assertion_operator`` | Optional assertion operator (==, >, <, etc.). |
        | ``expected`` | Expected count for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        = Return Value =

        Returns ``int``: The number of columns in the SWT table.

        - Without assertion: Returns the column count immediately
        - With assertion operator: Retries until count matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ElementNotFoundError`` if table not found

        Example:
        | ${count}=    Get Swt Table Column Count    Table
        | Get Swt Table Column Count    Table    ==    5
        | Get Swt Table Column Count    Table#data    >    0    
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Table '{locator}' column count"

        def get_count():
            columns = self._lib.get_table_columns(locator)
            return len(columns) if columns else 0

        return numeric_assertion_with_retry(
            get_count,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_swt_table_column_headers(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Optional[List[str]] = None,
        message: Optional[str] = None,
    ) -> List[str]:
        """Get SWT table column headers with optional assertion.

        | **Argument** | **Description** |
        | ``locator`` | Table locator. |
        | ``assertion_operator`` | Optional assertion operator (==, contains, etc.). |
        | ``expected`` | Expected header names for assertion. |
        | ``message`` | Custom error message. |

        = Return Value =

        Returns ``List[str]``: List of column header names.

        - Without assertion: Returns the headers immediately (no retry)
        - With assertion operator: Verifies headers match the assertion immediately (no retry)
        - Raises ``AssertionError`` if assertion fails
        - Raises ``ElementNotFoundError`` if table not found

        Example:
        | ${headers}=    Get Swt Table Column Headers    Table
        | Get Swt Table Column Headers    Table    ==    ['Name', 'Age', 'Status']
        | Get Swt Table Column Headers    Table    contains    ['Name']    
        """
        msg = message or f"Table '{locator}' column headers"

        headers = self._lib.get_table_columns(locator)
        if headers is None:
            headers = []

        if assertion_operator is not None and list_verify_assertion is not None:
            list_verify_assertion(headers, assertion_operator, expected, msg, message)

        return headers

    def get_swt_selected_table_rows(
        self,
        locator: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Optional[List[int]] = None,
        message: Optional[str] = None,
    ) -> List[int]:
        """Get selected SWT table row indices with optional assertion.

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
        | ${rows}=    Get Swt Selected Table Rows    Table
        | Get Swt Selected Table Rows    Table    contains    [0, 2]
        | Get Swt Selected Table Rows    Table    ==    [1]    
        """
        msg = message or f"Table '{locator}' selected rows"

        # Get selected rows via the SWT table API
        try:
            # SWT tables use getSelectionIndices() which returns int[]
            selected = self._lib.get_widget_property(locator, "selectionIndices")
            if selected is None:
                selected = []
            elif isinstance(selected, int):
                selected = [selected]
            elif not isinstance(selected, list):
                selected = list(selected)
        except Exception:
            selected = []

        if assertion_operator is not None and list_verify_assertion is not None:
            list_verify_assertion(selected, assertion_operator, expected, msg, message)

        return selected

    def swt_table_cell_should_contain(
        self,
        locator: str,
        row: int,
        column: int,
        expected: str,
        message: Optional[str] = None,
    ) -> None:
        """Verify that an SWT table cell contains expected text.

        | **Argument** | **Description** |
        | ``locator`` | Table locator. |
        | ``row`` | Row index (0-based). |
        | ``column`` | Column index (0-based). |
        | ``expected`` | Text that should be in the cell. |
        | ``message`` | Custom error message. |

        Example:
        | Swt Table Cell Should Contain    Table    0    1    John
        | Swt Table Cell Should Contain    Table#users    2    0    Active    
        """
        msg = message or f"Table '{locator}' cell [{row}, {column}] should contain '{expected}'"

        cell_value = self._lib.get_table_cell(locator, row, column)
        if expected not in str(cell_value):
            raise AssertionError(f"{msg}. Actual value: '{cell_value}'")

    def swt_table_row_count_should_be(
        self,
        locator: str,
        expected: int,
        message: Optional[str] = None,
    ) -> None:
        """Verify that SWT table has expected row count.

        | **Argument** | **Description** |
        | ``locator`` | Table locator. |
        | ``expected`` | Expected row count. |
        | ``message`` | Custom error message. |

        Example:
        | Swt Table Row Count Should Be    Table    10
        | Swt Table Row Count Should Be    Table#users    0    message=Table should be empty
        """
        msg = message or f"Table '{locator}' row count should be {expected}"

        actual = self._lib.get_table_row_count(locator)
        if actual != expected:
            raise AssertionError(f"{msg}. Actual count: {actual}")

    def swt_table_should_have_rows(
        self,
        locator: str,
        message: Optional[str] = None,
    ) -> None:
        """Verify that SWT table has at least one row.

        | **Argument** | **Description** |
        | ``locator`` | Table locator. |
        | ``message`` | Custom error message. |

        Example:
        | Swt Table Should Have Rows    Table
        | Swt Table Should Have Rows    Table#results    message=Search should return results
        """
        msg = message or f"Table '{locator}' should have at least one row"

        actual = self._lib.get_table_row_count(locator)
        if actual == 0:
            raise AssertionError(msg)

    def swt_table_should_be_empty(
        self,
        locator: str,
        message: Optional[str] = None,
    ) -> None:
        """Verify that SWT table has no rows.

        | **Argument** | **Description** |
        | ``locator`` | Table locator. |
        | ``message`` | Custom error message. |

        Example:
        | Swt Table Should Be Empty    Table
        | Swt Table Should Be Empty    Table#errors    message=No errors expected
        """
        msg = message or f"Table '{locator}' should be empty"

        actual = self._lib.get_table_row_count(locator)
        if actual != 0:
            raise AssertionError(f"{msg}. Actual row count: {actual}")
