"""Expression engine for flexible routing rules.

This module provides a safe, AST-based expression evaluator for creating
dynamic routing rules using Python-like expressions.

Features:
    - Safe evaluation using AST parsing (no exec/eval)
    - Support for standard comparison and logical operators
    - Attribute access for context fields
    - Basic built-in functions (len, any, all, sum, min, max, abs)
    - Timeout protection against infinite loops
    - Whitelist-based security model

Example:
    # Create context from validation result
    context = ExpressionContext(
        checkpoint_name="orders_validation",
        action_type="check",
        severity="critical",
        issues=["null_values", "schema_mismatch"],
        pass_rate=0.75,
        timestamp=datetime.now(),
        metadata={"environment": "production"},
    )

    # Evaluate expressions
    evaluator = SafeExpressionEvaluator()
    evaluator.evaluate("severity == 'critical'", context)  # True
    evaluator.evaluate("pass_rate < 0.8 and len(issues) > 0", context)  # True
    evaluator.evaluate("'production' in metadata.values()", context)  # True

Security:
    The evaluator uses a strict whitelist approach:
    - Only allowed AST node types are processed
    - No access to __builtins__, __import__, or dunder attributes
    - Timeout protection against resource exhaustion
    - No code execution (exec/eval) - only expression evaluation
"""

from __future__ import annotations

import ast
import operator
import signal
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable

from .rules import BaseRule, RuleRegistry

if TYPE_CHECKING:
    from .engine import RouteContext


class ExpressionError(Exception):
    """Raised when expression evaluation fails.

    Attributes:
        expression: The expression that failed.
        reason: Description of why the evaluation failed.
    """

    def __init__(self, expression: str, reason: str) -> None:
        self.expression = expression
        self.reason = reason
        super().__init__(f"Expression error: {reason} in '{expression}'")


class ExpressionTimeout(ExpressionError):
    """Raised when expression evaluation times out."""

    def __init__(self, expression: str, timeout_seconds: float) -> None:
        super().__init__(
            expression,
            f"Evaluation timed out after {timeout_seconds}s",
        )


class ExpressionSecurityError(ExpressionError):
    """Raised when expression contains unsafe operations."""

    def __init__(self, expression: str, unsafe_element: str) -> None:
        super().__init__(
            expression,
            f"Unsafe element detected: {unsafe_element}",
        )


@dataclass
class ExpressionContext:
    """Context for expression evaluation.

    This dataclass holds all the fields that can be accessed within
    routing expressions. It provides a structured way to pass validation
    results and metadata to the expression evaluator.

    Attributes:
        checkpoint_name: Name of the validation checkpoint.
        action_type: Type of action (check, learn, profile, compare, scan, mask).
        severity: Highest severity level (critical, high, medium, low, info).
        issues: List of issue identifiers or descriptions.
        pass_rate: Validation pass rate (0.0 to 1.0).
        timestamp: When the validation occurred.
        metadata: Custom fields for additional context.

    Example:
        context = ExpressionContext(
            checkpoint_name="orders_validation",
            action_type="check",
            severity="critical",
            issues=["null_values", "type_mismatch"],
            pass_rate=0.85,
            timestamp=datetime.now(),
            metadata={
                "environment": "production",
                "table": "orders",
                "row_count": 50000,
            },
        )

        # Access in expressions:
        # - context.severity == "critical"
        # - context.pass_rate < 0.9
        # - "null_values" in context.issues
        # - context.metadata.get("environment") == "production"
    """

    checkpoint_name: str = ""
    action_type: str = ""
    severity: str = "info"
    issues: list[str] = field(default_factory=list)
    pass_rate: float = 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary.

        Returns:
            Dictionary containing all context fields.

        Example:
            context.to_dict()
            # {
            #     "checkpoint_name": "orders_validation",
            #     "action_type": "check",
            #     "severity": "critical",
            #     ...
            # }
        """
        return {
            "checkpoint_name": self.checkpoint_name,
            "action_type": self.action_type,
            "severity": self.severity,
            "issues": list(self.issues),
            "pass_rate": self.pass_rate,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_validation_result(
        cls,
        result: dict[str, Any],
        checkpoint_name: str = "",
        action_type: str = "check",
    ) -> "ExpressionContext":
        """Create context from a validation result dictionary.

        Args:
            result: Validation result containing summary, issues, etc.
            checkpoint_name: Name of the checkpoint (optional).
            action_type: Type of action performed (default: "check").

        Returns:
            ExpressionContext populated from the validation result.

        Example:
            result = {
                "summary": {
                    "total_issues": 5,
                    "passed": 45,
                    "failed": 5,
                    "pass_rate": 0.9,
                    "has_critical": True,
                },
                "issues": [
                    {"validator": "null_check", "severity": "critical"},
                    {"validator": "range_check", "severity": "high"},
                ],
            }
            context = ExpressionContext.from_validation_result(result)
        """
        summary = result.get("summary", {})
        issues = result.get("issues", [])

        # Extract severity from summary or issues
        severity = "info"
        if summary.get("has_critical"):
            severity = "critical"
        elif summary.get("has_high"):
            severity = "high"
        elif summary.get("has_medium"):
            severity = "medium"
        elif summary.get("has_low"):
            severity = "low"

        # Extract issue identifiers
        issue_list = []
        for issue in issues:
            if isinstance(issue, dict):
                validator = issue.get("validator", "")
                if validator:
                    issue_list.append(validator)
                message = issue.get("message", "")
                if message and message not in issue_list:
                    issue_list.append(message)
            elif isinstance(issue, str):
                issue_list.append(issue)

        # Calculate pass rate
        pass_rate = summary.get("pass_rate", 1.0)
        if pass_rate is None:
            passed = summary.get("passed", 0)
            total = passed + summary.get("failed", 0)
            pass_rate = passed / total if total > 0 else 1.0

        # Build metadata from remaining fields
        metadata: dict[str, Any] = {}
        for key, value in result.items():
            if key not in ("summary", "issues"):
                metadata[key] = value

        # Add summary fields to metadata for additional access
        metadata["total_issues"] = summary.get("total_issues", len(issues))
        metadata["passed"] = summary.get("passed", 0)
        metadata["failed"] = summary.get("failed", 0)

        return cls(
            checkpoint_name=checkpoint_name,
            action_type=action_type,
            severity=severity,
            issues=issue_list,
            pass_rate=pass_rate,
            timestamp=datetime.utcnow(),
            metadata=metadata,
        )


class SafeExpressionEvaluator:
    """Safe expression evaluator using AST-based parsing.

    This evaluator provides a secure way to evaluate Python-like expressions
    without using exec() or eval(). It uses Python's AST module to parse
    expressions and then walks the AST tree to evaluate nodes.

    Security Features:
        - Whitelist of allowed AST node types
        - Blocked access to dunder attributes (__builtins__, etc.)
        - Timeout protection against infinite loops
        - No code execution - only expression evaluation
        - Limited built-in functions (len, any, all, sum, min, max, abs)

    Supported Operations:
        - Comparisons: ==, !=, <, >, <=, >=
        - Logical: and, or, not
        - Membership: in, not in
        - Arithmetic: +, -, *, /, //, %, **
        - Attribute access: context.severity, context.metadata.get("key")
        - Subscript access: context.issues[0], context.metadata["key"]
        - Function calls: len(context.issues), any(x > 0 for x in items)
        - List comprehensions: [x for x in items if x > 0]

    Example:
        evaluator = SafeExpressionEvaluator(timeout_seconds=1.0)

        context = ExpressionContext(
            severity="critical",
            issues=["null_values", "duplicates"],
            pass_rate=0.75,
        )

        # Simple comparisons
        evaluator.evaluate("severity == 'critical'", context)  # True
        evaluator.evaluate("pass_rate < 0.8", context)  # True

        # Logical operators
        evaluator.evaluate("severity == 'critical' and pass_rate < 0.9", context)

        # Built-in functions
        evaluator.evaluate("len(issues) > 1", context)  # True
        evaluator.evaluate("any(i.startswith('null') for i in issues)", context)

        # Membership
        evaluator.evaluate("'null_values' in issues", context)  # True

    Attributes:
        timeout_seconds: Maximum evaluation time (default: 1.0).
        max_iterations: Maximum loop iterations (default: 10000).
    """

    # Allowed AST node types for expression evaluation
    ALLOWED_NODES: set[type[ast.AST]] = {
        # Literals
        ast.Constant,
        ast.Num,  # Python 3.7 compatibility
        ast.Str,  # Python 3.7 compatibility
        ast.List,
        ast.Tuple,
        ast.Set,
        ast.Dict,
        # Variables and attributes
        ast.Name,
        ast.Attribute,
        ast.Subscript,
        ast.Index,  # Python 3.8 compatibility
        ast.Slice,
        # Operators
        ast.BinOp,
        ast.UnaryOp,
        ast.BoolOp,
        ast.Compare,
        # Comprehensions
        ast.ListComp,
        ast.SetComp,
        ast.DictComp,
        ast.GeneratorExp,
        ast.comprehension,
        # Function calls
        ast.Call,
        # Context
        ast.Load,
        ast.Store,
        # Conditionals
        ast.IfExp,
    }

    # Binary operators
    BINARY_OPS: dict[type[ast.operator], Callable[[Any, Any], Any]] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.LShift: operator.lshift,
        ast.RShift: operator.rshift,
        ast.BitOr: operator.or_,
        ast.BitXor: operator.xor,
        ast.BitAnd: operator.and_,
    }

    # Unary operators
    UNARY_OPS: dict[type[ast.unaryop], Callable[[Any], Any]] = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
        ast.Not: operator.not_,
        ast.Invert: operator.invert,
    }

    # Comparison operators
    COMPARE_OPS: dict[type[ast.cmpop], Callable[[Any, Any], bool]] = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Is: operator.is_,
        ast.IsNot: operator.is_not,
        ast.In: lambda x, y: x in y,
        ast.NotIn: lambda x, y: x not in y,
    }

    # Allowed built-in functions
    ALLOWED_FUNCTIONS: dict[str, Callable[..., Any]] = {
        "len": len,
        "any": any,
        "all": all,
        "sum": sum,
        "min": min,
        "max": max,
        "abs": abs,
        "round": round,
        "bool": bool,
        "int": int,
        "float": float,
        "str": str,
        "list": list,
        "tuple": tuple,
        "set": set,
        "dict": dict,
        "sorted": sorted,
        "reversed": lambda x: list(reversed(list(x))),
        "enumerate": enumerate,
        "zip": zip,
        "range": range,
        "filter": filter,
        "map": map,
        "isinstance": isinstance,
        "hasattr": hasattr,
        "getattr": getattr,
    }

    # Blocked attribute names (security)
    BLOCKED_ATTRIBUTES: set[str] = {
        "__builtins__",
        "__import__",
        "__class__",
        "__bases__",
        "__mro__",
        "__subclasses__",
        "__code__",
        "__globals__",
        "__locals__",
        "__dict__",
        "__module__",
        "__name__",
        "__qualname__",
        "__annotations__",
        "__func__",
        "__self__",
        "__call__",
        "__getattribute__",
        "__setattr__",
        "__delattr__",
        "__init__",
        "__new__",
        "__del__",
        "__reduce__",
        "__reduce_ex__",
        "__getstate__",
        "__setstate__",
    }

    def __init__(
        self,
        timeout_seconds: float = 1.0,
        max_iterations: int = 10000,
    ) -> None:
        """Initialize the evaluator.

        Args:
            timeout_seconds: Maximum time allowed for evaluation.
            max_iterations: Maximum iterations in comprehensions/loops.
        """
        self.timeout_seconds = timeout_seconds
        self.max_iterations = max_iterations
        self._iteration_count = 0
        self._timed_out = False

    def evaluate(
        self,
        expression: str,
        context: ExpressionContext,
    ) -> bool:
        """Evaluate an expression against the given context.

        Args:
            expression: Python-like expression to evaluate.
            context: Context containing values for the expression.

        Returns:
            Boolean result of the expression evaluation.

        Raises:
            ExpressionError: If expression is invalid or evaluation fails.
            ExpressionTimeout: If evaluation exceeds timeout.
            ExpressionSecurityError: If expression contains unsafe operations.

        Example:
            result = evaluator.evaluate(
                "severity == 'critical' and pass_rate < 0.9",
                context,
            )
        """
        if not expression or not expression.strip():
            raise ExpressionError(expression, "Empty expression")

        # Reset iteration counter
        self._iteration_count = 0
        self._timed_out = False

        try:
            # Parse the expression
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as e:
            raise ExpressionError(expression, f"Syntax error: {e}") from e

        # Validate AST nodes
        self._validate_ast(tree, expression)

        # Build evaluation namespace
        namespace = self._build_namespace(context)

        # Evaluate with timeout
        result = self._evaluate_with_timeout(tree.body, namespace, expression)

        # Convert to boolean
        return bool(result)

    def _validate_ast(self, tree: ast.AST, expression: str) -> None:
        """Validate that all AST nodes are allowed.

        Args:
            tree: AST tree to validate.
            expression: Original expression (for error messages).

        Raises:
            ExpressionSecurityError: If disallowed nodes are found.
        """
        for node in ast.walk(tree):
            # Check node type
            if type(node) not in self.ALLOWED_NODES and not isinstance(
                node, ast.Expression
            ):
                raise ExpressionSecurityError(
                    expression,
                    f"Disallowed node type: {type(node).__name__}",
                )

            # Check for blocked attribute access
            if isinstance(node, ast.Attribute):
                if node.attr in self.BLOCKED_ATTRIBUTES:
                    raise ExpressionSecurityError(
                        expression,
                        f"Access to '{node.attr}' is not allowed",
                    )

            # Check for blocked function names
            if isinstance(node, ast.Name):
                if node.id.startswith("__") and node.id.endswith("__"):
                    raise ExpressionSecurityError(
                        expression,
                        f"Access to '{node.id}' is not allowed",
                    )

    def _build_namespace(self, context: ExpressionContext) -> dict[str, Any]:
        """Build the namespace for expression evaluation.

        Args:
            context: Expression context.

        Returns:
            Dictionary with all available names.
        """
        # Start with allowed functions
        namespace = dict(self.ALLOWED_FUNCTIONS)

        # Add constants
        namespace["True"] = True
        namespace["False"] = False
        namespace["None"] = None

        # Add context as a named variable
        namespace["context"] = context

        # Also expose context fields directly for convenience
        namespace["checkpoint_name"] = context.checkpoint_name
        namespace["action_type"] = context.action_type
        namespace["severity"] = context.severity
        namespace["issues"] = context.issues
        namespace["pass_rate"] = context.pass_rate
        namespace["timestamp"] = context.timestamp
        namespace["metadata"] = context.metadata

        return namespace

    def _evaluate_with_timeout(
        self,
        node: ast.AST,
        namespace: dict[str, Any],
        expression: str,
    ) -> Any:
        """Evaluate AST node with timeout protection.

        Args:
            node: AST node to evaluate.
            namespace: Evaluation namespace.
            expression: Original expression (for error messages).

        Returns:
            Evaluation result.

        Raises:
            ExpressionTimeout: If evaluation times out.
        """
        result: Any = None
        error: Exception | None = None

        def evaluate():
            nonlocal result, error
            try:
                result = self._eval_node(node, namespace, expression)
            except Exception as e:
                error = e

        # Use threading for timeout on all platforms
        thread = threading.Thread(target=evaluate)
        thread.start()
        thread.join(timeout=self.timeout_seconds)

        if thread.is_alive():
            self._timed_out = True
            raise ExpressionTimeout(expression, self.timeout_seconds)

        if error is not None:
            raise error

        return result

    def _check_iteration_limit(self, expression: str) -> None:
        """Check if iteration limit has been exceeded.

        Args:
            expression: Original expression (for error messages).

        Raises:
            ExpressionError: If iteration limit exceeded.
        """
        self._iteration_count += 1
        if self._iteration_count > self.max_iterations:
            raise ExpressionError(
                expression,
                f"Iteration limit exceeded ({self.max_iterations})",
            )

    def _eval_node(
        self,
        node: ast.AST,
        namespace: dict[str, Any],
        expression: str,
    ) -> Any:
        """Evaluate a single AST node.

        Args:
            node: AST node to evaluate.
            namespace: Evaluation namespace.
            expression: Original expression (for error messages).

        Returns:
            Evaluation result.

        Raises:
            ExpressionError: If evaluation fails.
        """
        self._check_iteration_limit(expression)

        # Constant values
        if isinstance(node, ast.Constant):
            return node.value

        # Legacy numeric/string literals (Python 3.7)
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.Str):
            return node.s

        # Variable lookup
        if isinstance(node, ast.Name):
            if node.id not in namespace:
                raise ExpressionError(expression, f"Unknown name: {node.id}")
            return namespace[node.id]

        # Attribute access
        if isinstance(node, ast.Attribute):
            obj = self._eval_node(node.value, namespace, expression)
            if node.attr in self.BLOCKED_ATTRIBUTES:
                raise ExpressionSecurityError(
                    expression,
                    f"Access to '{node.attr}' is not allowed",
                )
            try:
                return getattr(obj, node.attr)
            except AttributeError:
                raise ExpressionError(
                    expression,
                    f"'{type(obj).__name__}' has no attribute '{node.attr}'",
                ) from None

        # Subscript access (indexing)
        if isinstance(node, ast.Subscript):
            obj = self._eval_node(node.value, namespace, expression)
            # Handle Python 3.8 vs 3.9+ differences
            if isinstance(node.slice, ast.Index):
                index = self._eval_node(node.slice.value, namespace, expression)
            elif isinstance(node.slice, ast.Slice):
                lower = (
                    self._eval_node(node.slice.lower, namespace, expression)
                    if node.slice.lower
                    else None
                )
                upper = (
                    self._eval_node(node.slice.upper, namespace, expression)
                    if node.slice.upper
                    else None
                )
                step = (
                    self._eval_node(node.slice.step, namespace, expression)
                    if node.slice.step
                    else None
                )
                index = slice(lower, upper, step)
            else:
                index = self._eval_node(node.slice, namespace, expression)
            try:
                return obj[index]
            except (KeyError, IndexError, TypeError) as e:
                raise ExpressionError(
                    expression,
                    f"Subscript error: {e}",
                ) from None

        # Binary operations
        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, namespace, expression)
            right = self._eval_node(node.right, namespace, expression)
            op_func = self.BINARY_OPS.get(type(node.op))
            if op_func is None:
                raise ExpressionError(
                    expression,
                    f"Unsupported binary operator: {type(node.op).__name__}",
                )
            try:
                return op_func(left, right)
            except Exception as e:
                raise ExpressionError(
                    expression,
                    f"Binary operation error: {e}",
                ) from None

        # Unary operations
        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, namespace, expression)
            op_func = self.UNARY_OPS.get(type(node.op))
            if op_func is None:
                raise ExpressionError(
                    expression,
                    f"Unsupported unary operator: {type(node.op).__name__}",
                )
            return op_func(operand)

        # Boolean operations (and, or)
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                result = True
                for value in node.values:
                    result = self._eval_node(value, namespace, expression)
                    if not result:
                        return False
                return result
            elif isinstance(node.op, ast.Or):
                for value in node.values:
                    result = self._eval_node(value, namespace, expression)
                    if result:
                        return result
                return False
            else:
                raise ExpressionError(
                    expression,
                    f"Unsupported boolean operator: {type(node.op).__name__}",
                )

        # Comparisons
        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left, namespace, expression)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator, namespace, expression)
                op_func = self.COMPARE_OPS.get(type(op))
                if op_func is None:
                    raise ExpressionError(
                        expression,
                        f"Unsupported comparison operator: {type(op).__name__}",
                    )
                if not op_func(left, right):
                    return False
                left = right
            return True

        # Function calls
        if isinstance(node, ast.Call):
            func = self._eval_node(node.func, namespace, expression)
            args = [self._eval_node(arg, namespace, expression) for arg in node.args]
            kwargs = {
                kw.arg: self._eval_node(kw.value, namespace, expression)
                for kw in node.keywords
                if kw.arg is not None
            }
            try:
                return func(*args, **kwargs)
            except Exception as e:
                raise ExpressionError(
                    expression,
                    f"Function call error: {e}",
                ) from None

        # List literal
        if isinstance(node, ast.List):
            return [self._eval_node(elt, namespace, expression) for elt in node.elts]

        # Tuple literal
        if isinstance(node, ast.Tuple):
            return tuple(
                self._eval_node(elt, namespace, expression) for elt in node.elts
            )

        # Set literal
        if isinstance(node, ast.Set):
            return {self._eval_node(elt, namespace, expression) for elt in node.elts}

        # Dict literal
        if isinstance(node, ast.Dict):
            return {
                self._eval_node(k, namespace, expression)
                if k is not None
                else None: self._eval_node(v, namespace, expression)
                for k, v in zip(node.keys, node.values)
            }

        # List comprehension
        if isinstance(node, ast.ListComp):
            return self._eval_comprehension(
                node.elt,
                node.generators,
                namespace,
                expression,
                list,
            )

        # Set comprehension
        if isinstance(node, ast.SetComp):
            return self._eval_comprehension(
                node.elt,
                node.generators,
                namespace,
                expression,
                set,
            )

        # Dict comprehension
        if isinstance(node, ast.DictComp):
            return self._eval_dict_comprehension(
                node.key,
                node.value,
                node.generators,
                namespace,
                expression,
            )

        # Generator expression
        if isinstance(node, ast.GeneratorExp):
            return self._eval_generator(
                node.elt,
                node.generators,
                namespace,
                expression,
            )

        # Conditional expression (ternary)
        if isinstance(node, ast.IfExp):
            test = self._eval_node(node.test, namespace, expression)
            if test:
                return self._eval_node(node.body, namespace, expression)
            else:
                return self._eval_node(node.orelse, namespace, expression)

        raise ExpressionError(
            expression,
            f"Unsupported AST node type: {type(node).__name__}",
        )

    def _eval_comprehension(
        self,
        elt: ast.AST,
        generators: list[ast.comprehension],
        namespace: dict[str, Any],
        expression: str,
        result_type: type,
    ) -> Any:
        """Evaluate a list/set comprehension.

        Args:
            elt: Element expression.
            generators: Comprehension generators.
            namespace: Evaluation namespace.
            expression: Original expression.
            result_type: Result container type (list or set).

        Returns:
            Comprehension result.
        """
        if not generators:
            return result_type()

        return self._eval_comprehension_recursive(
            elt,
            generators,
            0,
            namespace.copy(),
            expression,
            result_type,
        )

    def _eval_comprehension_recursive(
        self,
        elt: ast.AST,
        generators: list[ast.comprehension],
        gen_index: int,
        namespace: dict[str, Any],
        expression: str,
        result_type: type,
    ) -> Any:
        """Recursively evaluate nested comprehension generators."""
        if gen_index >= len(generators):
            # Base case: evaluate element
            value = self._eval_node(elt, namespace, expression)
            return [value] if result_type == list else {value}

        gen = generators[gen_index]
        iterable = self._eval_node(gen.iter, namespace, expression)
        result = [] if result_type == list else set()

        for item in iterable:
            self._check_iteration_limit(expression)

            # Bind target variable
            local_ns = namespace.copy()
            self._assign_target(gen.target, item, local_ns, expression)

            # Check conditions
            if gen.ifs:
                all_pass = True
                for if_clause in gen.ifs:
                    if not self._eval_node(if_clause, local_ns, expression):
                        all_pass = False
                        break
                if not all_pass:
                    continue

            # Recurse to next generator or evaluate element
            inner_result = self._eval_comprehension_recursive(
                elt,
                generators,
                gen_index + 1,
                local_ns,
                expression,
                result_type,
            )

            if result_type == list:
                result.extend(inner_result)
            else:
                result.update(inner_result)

        return result

    def _eval_dict_comprehension(
        self,
        key: ast.AST,
        value: ast.AST,
        generators: list[ast.comprehension],
        namespace: dict[str, Any],
        expression: str,
    ) -> dict[Any, Any]:
        """Evaluate a dictionary comprehension."""
        result: dict[Any, Any] = {}
        self._eval_dict_comp_recursive(
            key,
            value,
            generators,
            0,
            namespace.copy(),
            expression,
            result,
        )
        return result

    def _eval_dict_comp_recursive(
        self,
        key_node: ast.AST,
        value_node: ast.AST,
        generators: list[ast.comprehension],
        gen_index: int,
        namespace: dict[str, Any],
        expression: str,
        result: dict[Any, Any],
    ) -> None:
        """Recursively evaluate nested dict comprehension generators."""
        if gen_index >= len(generators):
            # Base case: evaluate key and value
            k = self._eval_node(key_node, namespace, expression)
            v = self._eval_node(value_node, namespace, expression)
            result[k] = v
            return

        gen = generators[gen_index]
        iterable = self._eval_node(gen.iter, namespace, expression)

        for item in iterable:
            self._check_iteration_limit(expression)

            # Bind target variable
            local_ns = namespace.copy()
            self._assign_target(gen.target, item, local_ns, expression)

            # Check conditions
            if gen.ifs:
                all_pass = True
                for if_clause in gen.ifs:
                    if not self._eval_node(if_clause, local_ns, expression):
                        all_pass = False
                        break
                if not all_pass:
                    continue

            # Recurse
            self._eval_dict_comp_recursive(
                key_node,
                value_node,
                generators,
                gen_index + 1,
                local_ns,
                expression,
                result,
            )

    def _eval_generator(
        self,
        elt: ast.AST,
        generators: list[ast.comprehension],
        namespace: dict[str, Any],
        expression: str,
    ) -> Any:
        """Evaluate a generator expression.

        Returns a generator object that can be consumed by functions like any(), all().
        """

        def gen():
            yield from self._eval_comprehension_recursive(
                elt,
                generators,
                0,
                namespace.copy(),
                expression,
                list,
            )

        return gen()

    def _assign_target(
        self,
        target: ast.AST,
        value: Any,
        namespace: dict[str, Any],
        expression: str,
    ) -> None:
        """Assign a value to a target (handles tuple unpacking).

        Args:
            target: Assignment target AST node.
            value: Value to assign.
            namespace: Namespace to update.
            expression: Original expression.
        """
        if isinstance(target, ast.Name):
            namespace[target.id] = value
        elif isinstance(target, ast.Tuple):
            if not hasattr(value, "__iter__"):
                raise ExpressionError(
                    expression,
                    f"Cannot unpack non-iterable: {type(value).__name__}",
                )
            values = list(value)
            if len(values) != len(target.elts):
                raise ExpressionError(
                    expression,
                    f"Cannot unpack {len(values)} values into {len(target.elts)} targets",
                )
            for t, v in zip(target.elts, values):
                self._assign_target(t, v, namespace, expression)
        else:
            raise ExpressionError(
                expression,
                f"Unsupported assignment target: {type(target).__name__}",
            )


@RuleRegistry.register("expression")
@dataclass
class ExpressionRule(BaseRule):
    """Rule that evaluates a Python-like expression.

    This rule allows complex routing conditions using a safe expression
    language. Expressions can reference context fields and use standard
    operators.

    Attributes:
        expression: Python-like expression to evaluate.
        timeout_seconds: Maximum evaluation time (default: 1.0).

    Example:
        rule = ExpressionRule(
            expression="severity == 'critical' and pass_rate < 0.8"
        )

        # Or for complex conditions:
        rule = ExpressionRule(
            expression='''
                (severity == 'critical' or len(issues) > 10)
                and 'production' in metadata.get('environment', '')
            '''
        )

    Available Context Fields:
        - checkpoint_name: Name of the validation checkpoint
        - action_type: Type of action (check, learn, profile, etc.)
        - severity: Highest issue severity (critical, high, medium, low, info)
        - issues: List of issue identifiers
        - pass_rate: Validation pass rate (0.0 to 1.0)
        - timestamp: When validation occurred
        - metadata: Dictionary of custom fields
        - context: Full ExpressionContext object

    Supported Operators:
        - Comparison: ==, !=, <, >, <=, >=, in, not in
        - Logical: and, or, not
        - Arithmetic: +, -, *, /, //, %, **

    Supported Functions:
        - len, any, all, sum, min, max, abs, round
        - bool, int, float, str, list, tuple, set, dict
        - sorted, reversed, enumerate, zip, range
        - isinstance, hasattr, getattr
    """

    expression: str = ""
    timeout_seconds: float = 1.0

    _evaluator: SafeExpressionEvaluator = field(
        default_factory=SafeExpressionEvaluator,
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        """Initialize the evaluator with configured timeout."""
        self._evaluator = SafeExpressionEvaluator(
            timeout_seconds=self.timeout_seconds,
        )

    @classmethod
    def get_param_schema(cls) -> dict[str, Any]:
        """Get parameter schema for this rule type."""
        return {
            "expression": {
                "type": "string",
                "required": True,
                "description": "Python-like expression to evaluate against the context",
            },
            "timeout_seconds": {
                "type": "number",
                "required": False,
                "description": "Maximum evaluation time in seconds",
                "default": 1.0,
                "minimum": 0.1,
                "maximum": 10.0,
            },
        }

    async def matches(self, context: "RouteContext") -> bool:
        """Check if the expression matches the context.

        Args:
            context: The routing context to evaluate against.

        Returns:
            True if the expression evaluates to True.
        """
        if not self.expression or not self.expression.strip():
            return False

        # Build expression context from route context
        expr_context = self._build_expression_context(context)

        try:
            return self._evaluator.evaluate(self.expression, expr_context)
        except (ExpressionError, ExpressionTimeout, ExpressionSecurityError):
            # Log error but return False for safety
            return False

    def _build_expression_context(
        self,
        route_context: "RouteContext",
    ) -> ExpressionContext:
        """Build ExpressionContext from RouteContext.

        Args:
            route_context: The routing context.

        Returns:
            ExpressionContext for expression evaluation.
        """
        # Extract severity
        severity = route_context.get_severity() or "info"

        # Extract issues from event data
        issues: list[str] = []
        if hasattr(route_context.event, "data"):
            event_issues = route_context.event.data.get("issues", [])
            for issue in event_issues:
                if isinstance(issue, dict):
                    validator = issue.get("validator", "")
                    if validator:
                        issues.append(validator)
                elif isinstance(issue, str):
                    issues.append(issue)

        # Get pass rate
        pass_rate = route_context.get_pass_rate() or 1.0

        # Get checkpoint name
        checkpoint_name = route_context.get_data_asset() or ""

        # Get action type from event
        action_type = "check"
        if hasattr(route_context.event, "event_type"):
            event_type = route_context.event.event_type
            if "learn" in event_type:
                action_type = "learn"
            elif "profile" in event_type:
                action_type = "profile"
            elif "compare" in event_type or "drift" in event_type:
                action_type = "compare"
            elif "scan" in event_type:
                action_type = "scan"
            elif "mask" in event_type:
                action_type = "mask"

        # Build metadata
        metadata = dict(route_context.metadata)
        if hasattr(route_context.event, "data"):
            metadata.update(route_context.event.data)

        # Add additional context fields
        metadata["tags"] = route_context.get_tags()
        metadata["status"] = route_context.get_status()
        metadata["error_message"] = route_context.get_error_message()
        metadata["issue_count"] = route_context.get_issue_count()

        return ExpressionContext(
            checkpoint_name=checkpoint_name,
            action_type=action_type,
            severity=severity,
            issues=issues,
            pass_rate=pass_rate,
            timestamp=route_context.timestamp,
            metadata=metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize rule to dictionary."""
        return {
            "type": self.rule_type,
            "expression": self.expression,
            "timeout_seconds": self.timeout_seconds,
        }
