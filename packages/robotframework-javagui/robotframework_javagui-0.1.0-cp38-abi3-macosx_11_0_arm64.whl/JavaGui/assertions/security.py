"""Security controls for assertion expressions.

This module provides secure evaluation of expressions used in the `validate`
operator to prevent code injection attacks while still allowing useful assertions.

The SecureExpressionEvaluator restricts:
- Access to dangerous builtins (exec, eval, compile, open, __import__)
- Access to dunder attributes (__class__, __bases__, etc.)
- Access to os, sys, subprocess modules
- File I/O operations
- Network operations

Allowed operations include:
- String operations (len, str, repr, upper, lower, etc.)
- Numeric operations (int, float, abs, round, min, max, sum)
- Type checking (isinstance, type, bool)
- Collection operations (list, dict, set, tuple, sorted, reversed)
- Comparison operations (all operators)
- Regular expressions via `re` module (search, match, findall)
"""

import ast
import re
from typing import Any, Dict, List, Optional, Set


# Builtins that are safe to use in expressions
SAFE_BUILTINS: Dict[str, Any] = {
    # Type constructors
    "bool": bool,
    "int": int,
    "float": float,
    "str": str,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "frozenset": frozenset,
    # Type checking
    "isinstance": isinstance,
    "type": type,
    "callable": callable,
    # String/sequence operations
    "len": len,
    "repr": repr,
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "sorted": sorted,
    "reversed": reversed,
    "enumerate": enumerate,
    "zip": zip,
    "map": map,
    "filter": filter,
    "range": range,
    # Boolean
    "all": all,
    "any": any,
    # Other safe operations
    "ord": ord,
    "chr": chr,
    "hex": hex,
    "bin": bin,
    "oct": oct,
    "format": format,
    "hash": hash,
    # Constants
    "True": True,
    "False": False,
    "None": None,
}

# Dangerous builtins that should never be accessible
DANGEROUS_BUILTINS: Set[str] = {
    "eval",
    "exec",
    "compile",
    "open",
    "__import__",
    "input",
    "breakpoint",
    "globals",
    "locals",
    "vars",
    "dir",
    "getattr",
    "setattr",
    "delattr",
    "hasattr",
    "memoryview",
    "bytearray",
    "bytes",
}

# Dangerous attribute names that could lead to code execution
DANGEROUS_ATTRIBUTES: Set[str] = {
    "__class__",
    "__bases__",
    "__base__",
    "__mro__",
    "__subclasses__",
    "__init__",
    "__new__",
    "__del__",
    "__dict__",
    "__globals__",
    "__code__",
    "__func__",
    "__self__",
    "__builtins__",
    "__import__",
    "__call__",
    "__getattribute__",
    "__setattr__",
    "__delattr__",
    "__reduce__",
    "__reduce_ex__",
    "__getstate__",
    "__setstate__",
}

# Simple namespace class for module-like access
class _SafeModuleNamespace:
    """A namespace object for safe module functions."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


# Safe modules that can be accessed
SAFE_MODULES: Dict[str, Any] = {
    "re": _SafeModuleNamespace(
        search=re.search,
        match=re.match,
        findall=re.findall,
        sub=re.sub,
        split=re.split,
        compile=re.compile,
        IGNORECASE=re.IGNORECASE,
        MULTILINE=re.MULTILINE,
        DOTALL=re.DOTALL,
        I=re.I,
        M=re.M,
        S=re.S,
    ),
}


class ExpressionSecurityError(Exception):
    """Raised when an expression contains dangerous code."""

    pass


class SafeASTVisitor(ast.NodeVisitor):
    """AST visitor that checks for dangerous constructs."""

    def __init__(self):
        self.errors: List[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        """Block all import statements."""
        self.errors.append("Import statements are not allowed")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Block all from...import statements."""
        self.errors.append("Import statements are not allowed")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Check function calls for dangerous builtins."""
        if isinstance(node.func, ast.Name):
            if node.func.id in DANGEROUS_BUILTINS:
                self.errors.append(f"Dangerous builtin '{node.func.id}' is not allowed")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Check attribute access for dangerous patterns."""
        if node.attr in DANGEROUS_ATTRIBUTES:
            self.errors.append(f"Access to '{node.attr}' attribute is not allowed")
        # Block dunder attributes generically
        if node.attr.startswith("__") and node.attr.endswith("__"):
            if node.attr not in {"__len__", "__str__", "__repr__", "__eq__", "__ne__"}:
                self.errors.append(f"Access to dunder attribute '{node.attr}' is not allowed")
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        """Check subscript access."""
        # Allow normal subscripting
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Check variable names."""
        if node.id in DANGEROUS_BUILTINS:
            self.errors.append(f"Access to dangerous builtin '{node.id}' is not allowed")
        self.generic_visit(node)


class SecureExpressionEvaluator:
    """Secure evaluator for assertion expressions.

    This class provides a restricted evaluation environment for the `validate`
    operator, preventing code injection while allowing useful assertions.

    Example usage:
        evaluator = SecureExpressionEvaluator()

        # Safe expressions
        evaluator.evaluate("value == 'expected'", {"value": "expected"})  # True
        evaluator.evaluate("len(value) > 0", {"value": "hello"})  # True
        evaluator.evaluate("value.startswith('Hello')", {"value": "Hello World"})  # True

        # Dangerous expressions (will raise ExpressionSecurityError)
        evaluator.evaluate("__import__('os').system('ls')", {})  # Error!
        evaluator.evaluate("open('/etc/passwd').read()", {})  # Error!
    """

    def __init__(
        self,
        extra_builtins: Optional[Dict[str, Any]] = None,
        extra_modules: Optional[Dict[str, Dict[str, Any]]] = None,
        strict_mode: bool = True,
    ):
        """Initialize the secure evaluator.

        Args:
            extra_builtins: Additional safe builtins to allow.
            extra_modules: Additional safe modules to allow (module_name -> {func_name: func}).
            strict_mode: If True, perform AST analysis before evaluation.
        """
        self.builtins = dict(SAFE_BUILTINS)
        if extra_builtins:
            # Validate extra builtins don't include dangerous ones
            for name in extra_builtins:
                if name in DANGEROUS_BUILTINS:
                    raise ValueError(f"Cannot add dangerous builtin: {name}")
            self.builtins.update(extra_builtins)

        self.modules = dict(SAFE_MODULES)
        if extra_modules:
            self.modules.update(extra_modules)

        self.strict_mode = strict_mode

    def validate_expression(self, expression: str) -> List[str]:
        """Validate an expression for security issues.

        Args:
            expression: The expression to validate.

        Returns:
            List of security issues found (empty if safe).
        """
        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as e:
            return [f"Syntax error: {e}"]

        visitor = SafeASTVisitor()
        visitor.visit(tree)
        return visitor.errors

    def evaluate(
        self,
        expression: str,
        namespace: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Evaluate an expression in a secure sandbox.

        Args:
            expression: The expression to evaluate.
            namespace: Variables available in the expression (e.g., {"value": ...}).

        Returns:
            The result of evaluating the expression.

        Raises:
            ExpressionSecurityError: If the expression contains dangerous code.
            Exception: Other evaluation errors (TypeError, ValueError, etc.).
        """
        if self.strict_mode:
            errors = self.validate_expression(expression)
            if errors:
                raise ExpressionSecurityError(
                    f"Expression contains dangerous code: {'; '.join(errors)}"
                )

        # Build safe namespace
        safe_namespace = dict(self.builtins)
        safe_namespace.update(self.modules)

        # Add user namespace (value, etc.)
        if namespace:
            safe_namespace.update(namespace)

        # Evaluate with restricted builtins
        try:
            # Note: We use a restricted __builtins__ to prevent access to dangerous functions
            return eval(expression, {"__builtins__": self.builtins}, safe_namespace)
        except NameError as e:
            raise ExpressionSecurityError(f"Access denied: {e}")
        except Exception:
            # Re-raise non-security errors
            raise


# Global secure evaluator instance with default settings
_default_evaluator = SecureExpressionEvaluator()


def secure_evaluate(expression: str, namespace: Optional[Dict[str, Any]] = None) -> Any:
    """Evaluate an expression securely using the default evaluator.

    This is a convenience function for common use cases.

    Args:
        expression: The expression to evaluate.
        namespace: Variables available in the expression.

    Returns:
        The result of evaluating the expression.

    Raises:
        ExpressionSecurityError: If the expression contains dangerous code.
    """
    return _default_evaluator.evaluate(expression, namespace)


def validate_expression(expression: str) -> List[str]:
    """Validate an expression for security issues.

    Args:
        expression: The expression to validate.

    Returns:
        List of security issues found (empty if safe).
    """
    return _default_evaluator.validate_expression(expression)


def is_expression_safe(expression: str) -> bool:
    """Check if an expression is safe to evaluate.

    Args:
        expression: The expression to check.

    Returns:
        True if the expression is safe, False otherwise.
    """
    return len(validate_expression(expression)) == 0
