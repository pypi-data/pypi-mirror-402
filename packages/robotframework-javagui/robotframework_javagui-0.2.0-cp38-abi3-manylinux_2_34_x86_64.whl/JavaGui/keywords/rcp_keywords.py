"""RCP-specific keywords with AssertionEngine support."""

from typing import Any, Optional, List
from assertionengine import AssertionOperator, list_verify_assertion

from ..assertions import (
    with_retry_assertion,
    numeric_assertion_with_retry,
)


class RcpKeywords:
    """Mixin class providing Eclipse RCP keywords with assertion support.

    These keywords provide RCP-specific functionality with built-in assertions
    following the Browser Library pattern.
    """

    # Configuration (set by main library)
    _assertion_timeout: float = 5.0
    _assertion_interval: float = 0.1

    def get_open_view_count(
        self,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> int:
        """Get count of open views with optional assertion.

        | **Argument** | **Description** |
        | ``assertion_operator`` | Optional assertion operator (==, >, <, etc.). |
        | ``expected`` | Expected count for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        Returns the number of currently open views in the workbench.

        = Return Value =

        Returns ``int``: The count of open views in the workbench.

        - Without assertion: Returns the count immediately
        - With assertion operator: Retries until count matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout

        Example:
        | ${count}=    Get Open View Count
        | Get Open View Count    >    0
        | Get Open View Count    ==    3    timeout=10
        | Get Open View Count    >=    1    message=At least one view should be open
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or "Open view count"

        def get_count():
            views = self._lib.get_open_views()
            return len(views) if views else 0

        return numeric_assertion_with_retry(
            get_count,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_open_editor_count(
        self,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> int:
        """Get count of open editors with optional assertion.

        | **Argument** | **Description** |
        | ``assertion_operator`` | Optional assertion operator (==, >, <, etc.). |
        | ``expected`` | Expected count for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        Returns the number of currently open editors in the workbench.

        = Return Value =

        Returns ``int``: The count of open editors in the workbench.

        - Without assertion: Returns the count immediately
        - With assertion operator: Retries until count matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout

        Example:
        | ${count}=    Get Open Editor Count
        | Get Open Editor Count    >    0
        | Get Open Editor Count    ==    5    timeout=10
        | Get Open Editor Count    ==    0    message=All editors should be closed
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or "Open editor count"

        def get_count():
            editors = self._lib.get_open_editors()
            return len(editors) if editors else 0

        return numeric_assertion_with_retry(
            get_count,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_active_perspective_id(
        self,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """Get the active perspective ID with optional assertion.

        | **Argument** | **Description** |
        | ``assertion_operator`` | Optional assertion operator (==, !=, contains, etc.). |
        | ``expected`` | Expected perspective ID for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        Returns the ID of the currently active perspective.

        = Return Value =

        Returns ``str``: The ID of the currently active perspective.

        - Without assertion: Returns the perspective ID immediately
        - With assertion operator: Retries until ID matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout

        Example:
        | ${perspective}=    Get Active Perspective Id
        | Get Active Perspective Id    ==    org.eclipse.jdt.ui.JavaPerspective
        | Get Active Perspective Id    contains    Java
        | Get Active Perspective Id    !=    org.eclipse.debug.ui.DebugPerspective    
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or "Active perspective"

        def get_perspective():
            return self._lib.get_active_perspective()

        return with_retry_assertion(
            get_perspective,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_editor_dirty_state(
        self,
        title: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> bool:
        """Get editor dirty (unsaved changes) state with optional assertion.

        | **Argument** | **Description** |
        | ``title`` | Editor title or file path. |
        | ``assertion_operator`` | Optional assertion operator (==, !=). |
        | ``expected`` | Expected dirty state (True/False) for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        Returns True if the editor has unsaved changes, False otherwise.

        = Return Value =

        Returns ``bool``: True if editor has unsaved changes, False otherwise.

        - Without assertion: Returns the state immediately
        - With assertion operator: Retries until state matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout

        Example:
        | ${dirty}=    Get Editor Dirty State    MyFile.java
        | Get Editor Dirty State    MyFile.java    ==    ${True}
        | Get Editor Dirty State    MyFile.java    ==    ${False}    message=Editor should have no unsaved changes
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Editor '{title}' dirty state"

        def get_dirty():
            return self._lib.is_editor_dirty(title)

        return with_retry_assertion(
            get_dirty,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_view_title(
        self,
        view_id: str,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """Get view title with optional assertion.

        | **Argument** | **Description** |
        | ``view_id`` | View ID (e.g., org.eclipse.ui.views.ProblemView). |
        | ``assertion_operator`` | Optional assertion operator (==, !=, contains, etc.). |
        | ``expected`` | Expected title for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        Returns the display title of the specified view.

        = Return Value =

        Returns ``str``: The title of the specified view.

        - Without assertion: Returns the title immediately
        - With assertion operator: Retries until title matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ValueError`` if view is not found in open views

        Example:
        | ${title}=    Get View Title    org.eclipse.ui.views.ProblemView
        | Get View Title    org.eclipse.ui.views.ProblemView    ==    Problems
        | Get View Title    org.eclipse.ui.console.ConsoleView    contains    Console    
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"View '{view_id}' title"

        def get_title():
            views = self._lib.get_open_views()
            if views:
                for view in views:
                    if isinstance(view, dict):
                        if view.get("id") == view_id or view.get("viewId") == view_id:
                            return view.get("title", view.get("name", ""))
                    elif hasattr(view, "id") and view.id == view_id:
                        return getattr(view, "title", getattr(view, "name", ""))
            # If view not found in open views, try to get info from view widget
            raise ValueError(f"View '{view_id}' not found in open views")

        return with_retry_assertion(
            get_title,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_open_view_ids(
        self,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Optional[List[str]] = None,
        message: Optional[str] = None,
    ) -> List[str]:
        """Get list of open view IDs with optional assertion.

        | **Argument** | **Description** |
        | ``assertion_operator`` | Optional assertion operator (contains, ==, etc.). |
        | ``expected`` | Expected view IDs for assertion. |
        | ``message`` | Custom error message. |

        Returns list of view IDs that are currently open.

        = Return Value =

        Returns ``List[str]``: List of open view IDs.

        - Without assertion: Returns the view IDs immediately (no retry)
        - With assertion operator: Verifies IDs match the assertion immediately (no retry)
        - Raises ``AssertionError`` if assertion fails

        Example:
        | ${views}=    Get Open View Ids
        | Get Open View Ids    contains    ['org.eclipse.ui.views.ProblemView']
        | Get Open View Ids    not contains    ['org.eclipse.debug.ui.DebugView']    
        """
        msg = message or "Open view IDs"

        views = self._lib.get_open_views()
        view_ids = []
        if views:
            for view in views:
                if isinstance(view, dict):
                    view_id = view.get("id", view.get("viewId", ""))
                    if view_id:
                        view_ids.append(view_id)
                elif hasattr(view, "id"):
                    view_ids.append(view.id)

        if assertion_operator is not None:
            list_verify_assertion(view_ids, assertion_operator, expected, msg, message)

        return view_ids

    def get_open_editor_titles(
        self,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Optional[List[str]] = None,
        message: Optional[str] = None,
    ) -> List[str]:
        """Get list of open editor titles with optional assertion.

        | **Argument** | **Description** |
        | ``assertion_operator`` | Optional assertion operator (contains, ==, etc.). |
        | ``expected`` | Expected editor titles for assertion. |
        | ``message`` | Custom error message. |

        Returns list of titles for all currently open editors.

        = Return Value =

        Returns ``List[str]``: List of open editor titles.

        - Without assertion: Returns the titles immediately (no retry)
        - With assertion operator: Verifies titles match the assertion immediately (no retry)
        - Raises ``AssertionError`` if assertion fails

        Example:
        | ${editors}=    Get Open Editor Titles
        | Get Open Editor Titles    contains    ['MyFile.java']
        | Get Open Editor Titles    not contains    ['DeletedFile.txt']    
        """
        msg = message or "Open editor titles"

        editors = self._lib.get_open_editors()
        titles = []
        if editors:
            for editor in editors:
                if isinstance(editor, dict):
                    title = editor.get("title", editor.get("name", ""))
                    if title:
                        titles.append(title)
                elif hasattr(editor, "title"):
                    titles.append(editor.title)

        if assertion_operator is not None:
            list_verify_assertion(titles, assertion_operator, expected, msg, message)

        return titles

    def get_active_editor_title(
        self,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """Get the title of the active editor with optional assertion.

        | **Argument** | **Description** |
        | ``assertion_operator`` | Optional assertion operator (==, !=, contains, etc.). |
        | ``expected`` | Expected title for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        Returns the title of the currently active editor.

        = Return Value =

        Returns ``str``: The title of the currently active editor.

        - Without assertion: Returns the title immediately
        - With assertion operator: Retries until title matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout
        - Raises ``ValueError`` if no active editor

        Example:
        | ${title}=    Get Active Editor Title
        | Get Active Editor Title    ==    MyFile.java
        | Get Active Editor Title    contains    .java
        | Get Active Editor Title    ends    Test.java    
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or "Active editor title"

        def get_title():
            editor = self._lib.get_active_editor()
            if editor is None:
                raise ValueError("No active editor")
            if isinstance(editor, dict):
                return editor.get("title", editor.get("name", ""))
            return getattr(editor, "title", getattr(editor, "name", ""))

        return with_retry_assertion(
            get_title,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def get_dirty_editor_count(
        self,
        assertion_operator: Optional[AssertionOperator] = None,
        expected: Any = None,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> int:
        """Get count of editors with unsaved changes with optional assertion.

        | **Argument** | **Description** |
        | ``assertion_operator`` | Optional assertion operator (==, >, <, etc.). |
        | ``expected`` | Expected count for assertion. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Assertion timeout in seconds. |

        Returns the number of editors that have unsaved changes.

        = Return Value =

        Returns ``int``: The count of editors with unsaved changes.

        - Without assertion: Returns the count immediately
        - With assertion operator: Retries until count matches the assertion or timeout
        - Raises ``AssertionError`` if assertion fails after timeout

        Example:
        | ${count}=    Get Dirty Editor Count
        | Get Dirty Editor Count    ==    0    message=All editors should be saved
        | Get Dirty Editor Count    >    0    
        """
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or "Dirty editor count"

        def get_count():
            editors = self._lib.get_open_editors()
            if not editors:
                return 0
            count = 0
            for editor in editors:
                if isinstance(editor, dict):
                    if editor.get("dirty", False):
                        count += 1
                elif hasattr(editor, "dirty") and editor.dirty:
                    count += 1
            return count

        return numeric_assertion_with_retry(
            get_count,
            assertion_operator,
            expected,
            msg,
            message,
            timeout_val,
            self._assertion_interval,
        )

    def view_should_be_open(
        self,
        view_id: str,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        """Verify that a view is open.

        | **Argument** | **Description** |
        | ``view_id`` | View ID to check. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Timeout in seconds. |

        Example:
        | View Should Be Open    org.eclipse.ui.views.ProblemView
        | View Should Be Open    org.eclipse.jdt.ui.PackageExplorer    timeout=10
        """
        import time
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"View '{view_id}' should be open"

        end_time = time.time() + timeout_val
        while time.time() < end_time:
            views = self._lib.get_open_views()
            if views:
                for view in views:
                    if isinstance(view, dict):
                        if view.get("id") == view_id or view.get("viewId") == view_id:
                            return
                    elif hasattr(view, "id") and view.id == view_id:
                        return
            time.sleep(self._assertion_interval)

        raise AssertionError(msg)

    def view_should_not_be_open(
        self,
        view_id: str,
        message: Optional[str] = None,
    ) -> None:
        """Verify that a view is not open.

        | **Argument** | **Description** |
        | ``view_id`` | View ID to check. |
        | ``message`` | Custom error message. |

        Example:
        | View Should Not Be Open    org.eclipse.debug.ui.DebugView
        """
        msg = message or f"View '{view_id}' should not be open"

        views = self._lib.get_open_views()
        if views:
            for view in views:
                if isinstance(view, dict):
                    if view.get("id") == view_id or view.get("viewId") == view_id:
                        raise AssertionError(msg)
                elif hasattr(view, "id") and view.id == view_id:
                    raise AssertionError(msg)

    def editor_should_be_open(
        self,
        title: str,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        """Verify that an editor is open.

        | **Argument** | **Description** |
        | ``title`` | Editor title to check. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Timeout in seconds. |

        Example:
        | Editor Should Be Open    MyFile.java
        | Editor Should Be Open    pom.xml    timeout=10
        """
        import time
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Editor '{title}' should be open"

        end_time = time.time() + timeout_val
        while time.time() < end_time:
            editors = self._lib.get_open_editors()
            if editors:
                for editor in editors:
                    if isinstance(editor, dict):
                        if editor.get("title") == title or editor.get("name") == title:
                            return
                    elif hasattr(editor, "title") and editor.title == title:
                        return
            time.sleep(self._assertion_interval)

        raise AssertionError(msg)

    def editor_should_not_be_open(
        self,
        title: str,
        message: Optional[str] = None,
    ) -> None:
        """Verify that an editor is not open.

        | **Argument** | **Description** |
        | ``title`` | Editor title to check. |
        | ``message`` | Custom error message. |

        Example:
        | Editor Should Not Be Open    DeletedFile.java
        """
        msg = message or f"Editor '{title}' should not be open"

        editors = self._lib.get_open_editors()
        if editors:
            for editor in editors:
                if isinstance(editor, dict):
                    if editor.get("title") == title or editor.get("name") == title:
                        raise AssertionError(msg)
                elif hasattr(editor, "title") and editor.title == title:
                    raise AssertionError(msg)

    def perspective_should_be_active(
        self,
        perspective_id: str,
        message: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        """Verify that a specific perspective is active.

        | **Argument** | **Description** |
        | ``perspective_id`` | Expected perspective ID. |
        | ``message`` | Custom error message. |
        | ``timeout`` | Timeout in seconds. |

        Example:
        | Perspective Should Be Active    org.eclipse.jdt.ui.JavaPerspective
        | Perspective Should Be Active    org.eclipse.debug.ui.DebugPerspective    timeout=10
        """
        import time
        timeout_val = timeout if timeout is not None else self._assertion_timeout
        msg = message or f"Perspective '{perspective_id}' should be active"

        end_time = time.time() + timeout_val
        while time.time() < end_time:
            try:
                active = self._lib.get_active_perspective()
                if active == perspective_id:
                    return
            except Exception:
                pass
            time.sleep(self._assertion_interval)

        try:
            actual = self._lib.get_active_perspective()
            raise AssertionError(f"{msg}. Actual: '{actual}'")
        except Exception:
            raise AssertionError(msg)
