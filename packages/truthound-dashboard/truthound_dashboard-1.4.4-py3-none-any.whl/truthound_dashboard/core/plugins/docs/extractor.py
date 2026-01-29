"""Documentation Extractor.

This module provides AST-based documentation extraction
for Python source code.
"""

from __future__ import annotations

import ast
import inspect
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ParameterDoc:
    """Documentation for a function parameter.

    Attributes:
        name: Parameter name.
        type_hint: Type annotation.
        default: Default value.
        description: Parameter description from docstring.
        required: Whether parameter is required.
    """

    name: str
    type_hint: str = ""
    default: str | None = None
    description: str = ""
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type_hint": self.type_hint,
            "default": self.default,
            "description": self.description,
            "required": self.required,
        }


@dataclass
class FunctionDoc:
    """Documentation for a function or method.

    Attributes:
        name: Function name.
        signature: Full function signature.
        docstring: Docstring content.
        description: Short description (first line).
        long_description: Full description.
        parameters: List of parameters.
        returns: Return type and description.
        raises: Exceptions that may be raised.
        examples: Usage examples.
        decorators: Applied decorators.
        is_async: Whether function is async.
        is_classmethod: Whether it's a classmethod.
        is_staticmethod: Whether it's a staticmethod.
        line_number: Line number in source.
    """

    name: str
    signature: str = ""
    docstring: str = ""
    description: str = ""
    long_description: str = ""
    parameters: list[ParameterDoc] = field(default_factory=list)
    returns: dict[str, str] = field(default_factory=dict)
    raises: list[dict[str, str]] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    is_async: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False
    line_number: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "signature": self.signature,
            "docstring": self.docstring,
            "description": self.description,
            "long_description": self.long_description,
            "parameters": [p.to_dict() for p in self.parameters],
            "returns": self.returns,
            "raises": self.raises,
            "examples": self.examples,
            "decorators": self.decorators,
            "is_async": self.is_async,
            "is_classmethod": self.is_classmethod,
            "is_staticmethod": self.is_staticmethod,
            "line_number": self.line_number,
        }


@dataclass
class ClassDoc:
    """Documentation for a class.

    Attributes:
        name: Class name.
        docstring: Class docstring.
        description: Short description.
        long_description: Full description.
        bases: Base classes.
        methods: List of method documentation.
        attributes: Class attributes.
        class_attributes: Class-level attributes.
        decorators: Applied decorators.
        is_dataclass: Whether it's a dataclass.
        line_number: Line number in source.
    """

    name: str
    docstring: str = ""
    description: str = ""
    long_description: str = ""
    bases: list[str] = field(default_factory=list)
    methods: list[FunctionDoc] = field(default_factory=list)
    attributes: list[dict[str, Any]] = field(default_factory=list)
    class_attributes: list[dict[str, Any]] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    is_dataclass: bool = False
    line_number: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "docstring": self.docstring,
            "description": self.description,
            "long_description": self.long_description,
            "bases": self.bases,
            "methods": [m.to_dict() for m in self.methods],
            "attributes": self.attributes,
            "class_attributes": self.class_attributes,
            "decorators": self.decorators,
            "is_dataclass": self.is_dataclass,
            "line_number": self.line_number,
        }


@dataclass
class ModuleDoc:
    """Documentation for a module.

    Attributes:
        name: Module name.
        path: File path.
        docstring: Module docstring.
        description: Short description.
        long_description: Full description.
        classes: List of class documentation.
        functions: List of function documentation.
        constants: Module-level constants.
        imports: Import statements.
    """

    name: str
    path: str = ""
    docstring: str = ""
    description: str = ""
    long_description: str = ""
    classes: list[ClassDoc] = field(default_factory=list)
    functions: list[FunctionDoc] = field(default_factory=list)
    constants: list[dict[str, Any]] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "path": self.path,
            "docstring": self.docstring,
            "description": self.description,
            "long_description": self.long_description,
            "classes": [c.to_dict() for c in self.classes],
            "functions": [f.to_dict() for f in self.functions],
            "constants": self.constants,
            "imports": self.imports,
        }


class DocstringParser:
    """Parses docstrings in various formats (Google, NumPy, reStructuredText)."""

    # Patterns for Google-style docstrings
    GOOGLE_SECTIONS = {
        "args": r"Args?:\s*\n",
        "arguments": r"Arguments?:\s*\n",
        "parameters": r"Parameters?:\s*\n",
        "returns": r"Returns?:\s*\n",
        "yields": r"Yields?:\s*\n",
        "raises": r"Raises?:\s*\n",
        "examples": r"Examples?:\s*\n",
        "attributes": r"Attributes?:\s*\n",
        "note": r"Note:\s*\n",
        "notes": r"Notes?:\s*\n",
        "warning": r"Warning:\s*\n",
        "see also": r"See Also:\s*\n",
    }

    @classmethod
    def parse(cls, docstring: str) -> dict[str, Any]:
        """Parse a docstring.

        Args:
            docstring: Docstring to parse.

        Returns:
            Parsed docstring sections.
        """
        if not docstring:
            return {}

        result: dict[str, Any] = {
            "description": "",
            "long_description": "",
            "params": [],
            "returns": {},
            "raises": [],
            "examples": [],
            "attributes": [],
        }

        lines = docstring.strip().split("\n")
        if not lines:
            return result

        # First non-empty line is short description
        for i, line in enumerate(lines):
            line = line.strip()
            if line:
                result["description"] = line
                lines = lines[i + 1:]
                break

        # Parse remaining content
        content = "\n".join(lines)

        # Extract sections
        sections = cls._split_sections(content)

        if "description" in sections:
            result["long_description"] = sections["description"].strip()

        if "args" in sections or "arguments" in sections or "parameters" in sections:
            section = sections.get("args") or sections.get("arguments") or sections.get("parameters", "")
            result["params"] = cls._parse_params(section)

        if "returns" in sections:
            result["returns"] = cls._parse_returns(sections["returns"])

        if "raises" in sections:
            result["raises"] = cls._parse_raises(sections["raises"])

        if "examples" in sections:
            result["examples"] = cls._parse_examples(sections["examples"])

        if "attributes" in sections:
            result["attributes"] = cls._parse_params(sections["attributes"])

        return result

    @classmethod
    def _split_sections(cls, content: str) -> dict[str, str]:
        """Split docstring into sections."""
        sections: dict[str, str] = {"description": ""}

        # Find all section headers
        section_pattern = r"^(Args?|Arguments?|Parameters?|Returns?|Yields?|Raises?|Examples?|Attributes?|Notes?|Warning|See Also):\s*$"
        current_section = "description"
        current_content: list[str] = []

        for line in content.split("\n"):
            match = re.match(section_pattern, line.strip(), re.IGNORECASE)
            if match:
                # Save previous section
                sections[current_section] = "\n".join(current_content)
                # Start new section
                current_section = match.group(1).lower()
                if current_section.endswith("s") and current_section not in ["notes", "yields", "raises"]:
                    current_section = current_section[:-1]
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        sections[current_section] = "\n".join(current_content)

        return sections

    @classmethod
    def _parse_params(cls, section: str) -> list[dict[str, str]]:
        """Parse parameter section."""
        params = []
        current_param: dict[str, str] | None = None

        for line in section.split("\n"):
            # Match parameter line: "name (type): description" or "name: description"
            match = re.match(r"^\s*(\w+)(?:\s*\(([^)]+)\))?:\s*(.*)$", line)
            if match:
                if current_param:
                    params.append(current_param)
                current_param = {
                    "name": match.group(1),
                    "type": match.group(2) or "",
                    "description": match.group(3),
                }
            elif current_param and line.strip():
                # Continuation of description
                current_param["description"] += " " + line.strip()

        if current_param:
            params.append(current_param)

        return params

    @classmethod
    def _parse_returns(cls, section: str) -> dict[str, str]:
        """Parse returns section."""
        lines = [l.strip() for l in section.split("\n") if l.strip()]
        if not lines:
            return {}

        # Try to parse "type: description" format
        match = re.match(r"^([^:]+):\s*(.*)$", lines[0])
        if match:
            return {
                "type": match.group(1).strip(),
                "description": match.group(2) + " ".join(lines[1:]),
            }

        return {"description": " ".join(lines)}

    @classmethod
    def _parse_raises(cls, section: str) -> list[dict[str, str]]:
        """Parse raises section."""
        raises = []
        current: dict[str, str] | None = None

        for line in section.split("\n"):
            match = re.match(r"^\s*(\w+):\s*(.*)$", line)
            if match:
                if current:
                    raises.append(current)
                current = {
                    "exception": match.group(1),
                    "description": match.group(2),
                }
            elif current and line.strip():
                current["description"] += " " + line.strip()

        if current:
            raises.append(current)

        return raises

    @classmethod
    def _parse_examples(cls, section: str) -> list[str]:
        """Parse examples section."""
        examples = []
        current: list[str] = []
        in_code_block = False

        for line in section.split("\n"):
            if line.strip().startswith(">>>") or in_code_block:
                in_code_block = True
                current.append(line)
                if not line.strip() and current:
                    examples.append("\n".join(current))
                    current = []
                    in_code_block = False
            elif current:
                examples.append("\n".join(current))
                current = []
                in_code_block = False

        if current:
            examples.append("\n".join(current))

        return examples


class DocumentationExtractor:
    """Extracts documentation from Python source code using AST."""

    def __init__(self, include_private: bool = False) -> None:
        """Initialize the extractor.

        Args:
            include_private: Whether to include private members.
        """
        self.include_private = include_private

    def extract_from_source(self, source: str, module_name: str = "") -> ModuleDoc:
        """Extract documentation from source code.

        Args:
            source: Python source code.
            module_name: Module name.

        Returns:
            ModuleDoc with extracted documentation.
        """
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return ModuleDoc(name=module_name)

        return self._extract_module(tree, module_name)

    def extract_from_file(self, path: str | Path) -> ModuleDoc:
        """Extract documentation from a file.

        Args:
            path: Path to Python file.

        Returns:
            ModuleDoc with extracted documentation.
        """
        path = Path(path)
        source = path.read_text(encoding="utf-8")
        module_name = path.stem
        doc = self.extract_from_source(source, module_name)
        doc.path = str(path)
        return doc

    def extract_from_path(self, path: str | Path) -> list[ModuleDoc]:
        """Extract documentation from all Python files in a path.

        Args:
            path: Directory or file path.

        Returns:
            List of ModuleDoc for each file.
        """
        path = Path(path)
        docs: list[ModuleDoc] = []

        if path.is_file():
            docs.append(self.extract_from_file(path))
        elif path.is_dir():
            for py_file in path.rglob("*.py"):
                if py_file.name.startswith("_") and not self.include_private:
                    continue
                docs.append(self.extract_from_file(py_file))

        return docs

    def _extract_module(self, tree: ast.Module, name: str) -> ModuleDoc:
        """Extract module documentation from AST."""
        doc = ModuleDoc(name=name)

        # Get module docstring
        if (
            tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)
        ):
            doc.docstring = tree.body[0].value.value
            parsed = DocstringParser.parse(doc.docstring)
            doc.description = parsed.get("description", "")
            doc.long_description = parsed.get("long_description", "")

        # Extract imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    doc.imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    doc.imports.append(f"from {node.module}")

        # Extract classes and functions at module level
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                if self._should_include(node.name):
                    doc.classes.append(self._extract_class(node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if self._should_include(node.name):
                    doc.functions.append(self._extract_function(node))
            elif isinstance(node, ast.Assign):
                # Module-level constants
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        doc.constants.append({
                            "name": target.id,
                            "value": ast.unparse(node.value) if hasattr(ast, "unparse") else "",
                        })

        return doc

    def _extract_class(self, node: ast.ClassDef) -> ClassDoc:
        """Extract class documentation from AST."""
        doc = ClassDoc(
            name=node.name,
            line_number=node.lineno,
        )

        # Get base classes
        for base in node.bases:
            if isinstance(base, ast.Name):
                doc.bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                doc.bases.append(f"{ast.unparse(base)}" if hasattr(ast, "unparse") else base.attr)

        # Get decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                doc.decorators.append(decorator.id)
                if decorator.id == "dataclass":
                    doc.is_dataclass = True
            elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                doc.decorators.append(decorator.func.id)
                if decorator.func.id == "dataclass":
                    doc.is_dataclass = True

        # Get docstring
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            doc.docstring = node.body[0].value.value
            parsed = DocstringParser.parse(doc.docstring)
            doc.description = parsed.get("description", "")
            doc.long_description = parsed.get("long_description", "")
            doc.attributes = parsed.get("attributes", [])

        # Extract methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if self._should_include(item.name):
                    doc.methods.append(self._extract_function(item))
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                # Class attribute with type annotation
                doc.class_attributes.append({
                    "name": item.target.id,
                    "type": ast.unparse(item.annotation) if hasattr(ast, "unparse") else "",
                    "value": ast.unparse(item.value) if item.value and hasattr(ast, "unparse") else None,
                })

        return doc

    def _extract_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionDoc:
        """Extract function documentation from AST."""
        doc = FunctionDoc(
            name=node.name,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            line_number=node.lineno,
        )

        # Get decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                doc.decorators.append(decorator.id)
                if decorator.id == "classmethod":
                    doc.is_classmethod = True
                elif decorator.id == "staticmethod":
                    doc.is_staticmethod = True
            elif isinstance(decorator, ast.Attribute):
                doc.decorators.append(decorator.attr)

        # Build signature
        doc.signature = self._build_signature(node)

        # Get docstring
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            doc.docstring = node.body[0].value.value
            parsed = DocstringParser.parse(doc.docstring)
            doc.description = parsed.get("description", "")
            doc.long_description = parsed.get("long_description", "")
            doc.returns = parsed.get("returns", {})
            doc.raises = parsed.get("raises", [])
            doc.examples = parsed.get("examples", [])

            # Match docstring params to function params
            docstring_params = {p["name"]: p for p in parsed.get("params", [])}
            doc.parameters = self._extract_parameters(node.args, docstring_params)
        else:
            doc.parameters = self._extract_parameters(node.args, {})

        return doc

    def _extract_parameters(
        self,
        args: ast.arguments,
        docstring_params: dict[str, dict[str, str]],
    ) -> list[ParameterDoc]:
        """Extract function parameters from AST."""
        params: list[ParameterDoc] = []

        # Calculate defaults offset
        num_defaults = len(args.defaults)
        num_args = len(args.args)
        defaults_offset = num_args - num_defaults

        for i, arg in enumerate(args.args):
            if arg.arg == "self" or arg.arg == "cls":
                continue

            param = ParameterDoc(name=arg.arg)

            # Type hint
            if arg.annotation:
                param.type_hint = ast.unparse(arg.annotation) if hasattr(ast, "unparse") else ""

            # Default value
            default_index = i - defaults_offset
            if default_index >= 0:
                param.default = ast.unparse(args.defaults[default_index]) if hasattr(ast, "unparse") else "..."
                param.required = False

            # Description from docstring
            if arg.arg in docstring_params:
                param.description = docstring_params[arg.arg].get("description", "")
                if not param.type_hint:
                    param.type_hint = docstring_params[arg.arg].get("type", "")

            params.append(param)

        # Handle *args and **kwargs
        if args.vararg:
            params.append(ParameterDoc(
                name=f"*{args.vararg.arg}",
                type_hint=ast.unparse(args.vararg.annotation) if args.vararg.annotation and hasattr(ast, "unparse") else "",
                required=False,
            ))

        if args.kwarg:
            params.append(ParameterDoc(
                name=f"**{args.kwarg.arg}",
                type_hint=ast.unparse(args.kwarg.annotation) if args.kwarg.annotation and hasattr(ast, "unparse") else "",
                required=False,
            ))

        return params

    def _build_signature(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        """Build function signature string."""
        parts = []

        if isinstance(node, ast.AsyncFunctionDef):
            parts.append("async ")

        parts.append(f"def {node.name}(")

        # Parameters
        param_strs = []
        args = node.args

        for i, arg in enumerate(args.args):
            param = arg.arg
            if arg.annotation:
                param += f": {ast.unparse(arg.annotation)}" if hasattr(ast, "unparse") else ""

            # Default
            default_index = i - (len(args.args) - len(args.defaults))
            if default_index >= 0:
                param += f" = {ast.unparse(args.defaults[default_index])}" if hasattr(ast, "unparse") else " = ..."

            param_strs.append(param)

        if args.vararg:
            param = f"*{args.vararg.arg}"
            if args.vararg.annotation:
                param += f": {ast.unparse(args.vararg.annotation)}" if hasattr(ast, "unparse") else ""
            param_strs.append(param)

        if args.kwarg:
            param = f"**{args.kwarg.arg}"
            if args.kwarg.annotation:
                param += f": {ast.unparse(args.kwarg.annotation)}" if hasattr(ast, "unparse") else ""
            param_strs.append(param)

        parts.append(", ".join(param_strs))
        parts.append(")")

        # Return type
        if node.returns:
            parts.append(f" -> {ast.unparse(node.returns)}" if hasattr(ast, "unparse") else "")

        return "".join(parts)

    def _should_include(self, name: str) -> bool:
        """Check if member should be included."""
        if name.startswith("_") and not self.include_private:
            return False
        return True
