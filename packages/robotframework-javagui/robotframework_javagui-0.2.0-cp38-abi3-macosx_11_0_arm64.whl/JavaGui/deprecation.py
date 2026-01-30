"""Deprecation utilities for JavaGui library.

This module provides utilities for marking keywords as deprecated and
creating backward-compatible aliases with deprecation warnings.
"""

import functools
import warnings
from typing import Any, Callable, Dict, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


class DeprecatedKeywordWarning(UserWarning):
    """Warning issued when a deprecated keyword is used."""

    pass


def deprecated(
    reason: str,
    replacement: Optional[str] = None,
    version: Optional[str] = None,
    remove_in: Optional[str] = None,
) -> Callable[[F], F]:
    """Decorator to mark a keyword as deprecated.

    Args:
        reason: Reason for deprecation.
        replacement: Name of the replacement keyword.
        version: Version when the keyword was deprecated.
        remove_in: Version when the keyword will be removed.

    Returns:
        Decorated function that issues deprecation warning.

    Example:
        @deprecated(
            reason="Use Get Text instead",
            replacement="Get Text",
            version="3.0.0",
            remove_in="4.0.0"
        )
        def get_label_content(self, locator):
            return self.get_text(locator)
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            message = _build_deprecation_message(
                func.__name__, reason, replacement, version, remove_in
            )
            warnings.warn(message, DeprecatedKeywordWarning, stacklevel=2)
            return func(*args, **kwargs)

        # Mark as deprecated for documentation
        wrapper._deprecated = True
        wrapper._deprecation_reason = reason
        wrapper._deprecation_replacement = replacement
        wrapper._deprecation_version = version
        wrapper._deprecation_remove_in = remove_in
        return wrapper  # type: ignore

    return decorator


def _build_deprecation_message(
    name: str,
    reason: str,
    replacement: Optional[str],
    version: Optional[str],
    remove_in: Optional[str],
) -> str:
    """Build a deprecation warning message."""
    parts = [f"Keyword '{name}' is deprecated"]

    if version:
        parts[0] += f" since version {version}"

    parts.append(f". {reason}")

    if replacement:
        parts.append(f" Use '{replacement}' instead.")

    if remove_in:
        parts.append(f" This keyword will be removed in version {remove_in}.")

    return "".join(parts)


def create_keyword_alias(
    original_method: Callable,
    alias_name: str,
    deprecated_in: Optional[str] = None,
    remove_in: Optional[str] = None,
) -> Callable:
    """Create an alias for a keyword with deprecation warning.

    Args:
        original_method: The original keyword method.
        alias_name: Name of the alias (for warning message).
        deprecated_in: Version when alias was deprecated.
        remove_in: Version when alias will be removed.

    Returns:
        Wrapper function that calls original and warns.
    """
    original_name = getattr(original_method, "__name__", str(original_method))

    @functools.wraps(original_method)
    def alias_wrapper(*args, **kwargs):
        message = _build_deprecation_message(
            alias_name,
            f"This is an alias for '{original_name}'",
            original_name,
            deprecated_in,
            remove_in,
        )
        warnings.warn(message, DeprecatedKeywordWarning, stacklevel=2)
        return original_method(*args, **kwargs)

    alias_wrapper.__name__ = alias_name
    alias_wrapper.__doc__ = (
        f"*DEPRECATED* Alias for `{original_name}`.\n\n"
        f"Use `{original_name}` instead."
    )
    alias_wrapper._deprecated = True
    alias_wrapper._is_alias_for = original_name
    return alias_wrapper


class KeywordAliasRegistry:
    """Registry for managing keyword aliases with deprecation.

    This class helps manage backward-compatible keyword aliases
    that issue deprecation warnings when used.
    """

    def __init__(self):
        self._aliases: Dict[str, Dict[str, Any]] = {}

    def register_alias(
        self,
        alias_name: str,
        original_name: str,
        deprecated_in: Optional[str] = None,
        remove_in: Optional[str] = None,
    ) -> None:
        """Register a keyword alias.

        Args:
            alias_name: The deprecated alias name.
            original_name: The new/current keyword name.
            deprecated_in: Version when alias was deprecated.
            remove_in: Version when alias will be removed.
        """
        self._aliases[alias_name] = {
            "original": original_name,
            "deprecated_in": deprecated_in,
            "remove_in": remove_in,
        }

    def get_original_name(self, alias_name: str) -> Optional[str]:
        """Get the original keyword name for an alias.

        Args:
            alias_name: The alias name to look up.

        Returns:
            Original keyword name or None if not an alias.
        """
        info = self._aliases.get(alias_name)
        return info["original"] if info else None

    def is_deprecated_alias(self, name: str) -> bool:
        """Check if a keyword name is a deprecated alias.

        Args:
            name: Keyword name to check.

        Returns:
            True if name is a deprecated alias.
        """
        return name in self._aliases

    def get_all_aliases(self) -> Dict[str, str]:
        """Get all registered aliases.

        Returns:
            Dict mapping alias names to original names.
        """
        return {name: info["original"] for name, info in self._aliases.items()}

    def apply_to_class(self, cls: type) -> type:
        """Apply all registered aliases to a class.

        Creates alias methods on the class that call the original
        methods with deprecation warnings.

        Args:
            cls: Class to add aliases to.

        Returns:
            Modified class with aliases added.
        """
        for alias_name, info in self._aliases.items():
            original_name = info["original"]
            if hasattr(cls, original_name):
                original_method = getattr(cls, original_name)
                alias_method = create_keyword_alias(
                    original_method,
                    alias_name,
                    info["deprecated_in"],
                    info["remove_in"],
                )
                setattr(cls, alias_name, alias_method)
        return cls


# Global registry for JavaGui library aliases
_javagui_alias_registry = KeywordAliasRegistry()


def register_alias(
    alias_name: str,
    original_name: str,
    deprecated_in: Optional[str] = None,
    remove_in: Optional[str] = None,
) -> None:
    """Register a keyword alias in the global registry.

    Args:
        alias_name: The deprecated alias name.
        original_name: The new/current keyword name.
        deprecated_in: Version when alias was deprecated.
        remove_in: Version when alias will be removed.
    """
    _javagui_alias_registry.register_alias(
        alias_name, original_name, deprecated_in, remove_in
    )


def get_alias_registry() -> KeywordAliasRegistry:
    """Get the global alias registry.

    Returns:
        The global KeywordAliasRegistry instance.
    """
    return _javagui_alias_registry


# Register common aliases for backward compatibility
# These map old keyword names to new AssertionEngine-enabled names

# Getter keyword aliases
register_alias(
    "Get Label Content",
    "Get Text",
    deprecated_in="3.0.0",
    remove_in="4.0.0",
)
register_alias(
    "Get Component Text",
    "Get Text",
    deprecated_in="3.0.0",
    remove_in="4.0.0",
)
register_alias(
    "Get Field Value",
    "Get Value",
    deprecated_in="3.0.0",
    remove_in="4.0.0",
)
register_alias(
    "Get Text Field Value",
    "Get Value",
    deprecated_in="3.0.0",
    remove_in="4.0.0",
)

# Table keyword aliases
register_alias(
    "Get Table Cell Content",
    "Get Table Cell Value",
    deprecated_in="3.0.0",
    remove_in="4.0.0",
)
register_alias(
    "Get Table Cell Text",
    "Get Table Cell Value",
    deprecated_in="3.0.0",
    remove_in="4.0.0",
)
register_alias(
    "Table Cell Should Contain",
    "Get Table Cell Value",
    deprecated_in="3.0.0",
    remove_in="4.0.0",
)
register_alias(
    "Get Number Of Table Rows",
    "Get Table Row Count",
    deprecated_in="3.0.0",
    remove_in="4.0.0",
)
register_alias(
    "Get Number Of Table Columns",
    "Get Table Column Count",
    deprecated_in="3.0.0",
    remove_in="4.0.0",
)

# Tree keyword aliases
register_alias(
    "Get Tree Node Text",
    "Get Tree Node Label",
    deprecated_in="3.0.0",
    remove_in="4.0.0",
)
register_alias(
    "Get Tree Node Count",
    "Get Tree Child Count",
    deprecated_in="3.0.0",
    remove_in="4.0.0",
)

# List keyword aliases
register_alias(
    "Get List Item Text",
    "Get List Item Value",
    deprecated_in="3.0.0",
    remove_in="4.0.0",
)
register_alias(
    "Get Number Of List Items",
    "Get List Item Count",
    deprecated_in="3.0.0",
    remove_in="4.0.0",
)
register_alias(
    "Get Combobox Items",
    "Get ComboBox Items",
    deprecated_in="3.0.0",
    remove_in="4.0.0",
)

# State keyword aliases
register_alias(
    "Component Should Be Visible",
    "Get Element States",
    deprecated_in="3.0.0",
    remove_in="4.0.0",
)
register_alias(
    "Component Should Be Enabled",
    "Get Element States",
    deprecated_in="3.0.0",
    remove_in="4.0.0",
)
