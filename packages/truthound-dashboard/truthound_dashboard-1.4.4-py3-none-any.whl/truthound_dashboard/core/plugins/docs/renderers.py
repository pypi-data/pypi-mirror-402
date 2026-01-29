"""Documentation Renderers.

This module provides renderers for converting extracted documentation
into various output formats (Markdown, HTML, JSON).
"""

from __future__ import annotations

import html
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from .extractor import (
    ModuleDoc,
    ClassDoc,
    FunctionDoc,
    ParameterDoc,
)

logger = logging.getLogger(__name__)


@dataclass
class RenderOptions:
    """Options for documentation rendering.

    Attributes:
        include_private: Include private members (starting with _).
        include_source: Include source code snippets.
        include_examples: Include usage examples.
        include_deprecation: Include deprecation notices.
        max_depth: Maximum nesting depth for classes/methods.
        toc: Generate table of contents.
        syntax_highlight: Enable syntax highlighting (HTML).
        css_class_prefix: CSS class prefix for HTML output.
    """

    include_private: bool = False
    include_source: bool = True
    include_examples: bool = True
    include_deprecation: bool = True
    max_depth: int = 3
    toc: bool = True
    syntax_highlight: bool = True
    css_class_prefix: str = "plugin-doc"


class DocumentationRenderer(ABC):
    """Abstract base class for documentation renderers."""

    def __init__(self, options: RenderOptions | None = None) -> None:
        """Initialize the renderer.

        Args:
            options: Rendering options.
        """
        self.options = options or RenderOptions()

    @abstractmethod
    def render_module(self, doc: ModuleDoc) -> str:
        """Render module documentation.

        Args:
            doc: Module documentation.

        Returns:
            Rendered documentation string.
        """
        pass

    @abstractmethod
    def render_class(self, doc: ClassDoc, depth: int = 0) -> str:
        """Render class documentation.

        Args:
            doc: Class documentation.
            depth: Current nesting depth.

        Returns:
            Rendered documentation string.
        """
        pass

    @abstractmethod
    def render_function(self, doc: FunctionDoc, depth: int = 0) -> str:
        """Render function documentation.

        Args:
            doc: Function documentation.
            depth: Current nesting depth.

        Returns:
            Rendered documentation string.
        """
        pass

    def _should_include(self, name: str) -> bool:
        """Check if a member should be included.

        Args:
            name: Member name.

        Returns:
            True if should be included.
        """
        if name.startswith("__") and name.endswith("__"):
            # Always include dunder methods
            return True
        if name.startswith("_"):
            return self.options.include_private
        return True


class MarkdownRenderer(DocumentationRenderer):
    """Renders documentation as Markdown."""

    def render_module(self, doc: ModuleDoc) -> str:
        """Render module documentation as Markdown.

        Args:
            doc: Module documentation.

        Returns:
            Markdown string.
        """
        lines: list[str] = []

        # Module header
        lines.append(f"# {doc.name}")
        lines.append("")

        if doc.description:
            lines.append(doc.description)
            lines.append("")

        # Table of contents
        if self.options.toc and (doc.classes or doc.functions):
            lines.append("## Table of Contents")
            lines.append("")

            if doc.classes:
                lines.append("### Classes")
                lines.append("")
                for cls in doc.classes:
                    if self._should_include(cls.name):
                        lines.append(f"- [{cls.name}](#{cls.name.lower()})")
                lines.append("")

            if doc.functions:
                lines.append("### Functions")
                lines.append("")
                for func in doc.functions:
                    if self._should_include(func.name):
                        lines.append(f"- [{func.name}](#{func.name.lower()})")
                lines.append("")

        # Classes
        if doc.classes:
            lines.append("## Classes")
            lines.append("")
            for cls in doc.classes:
                if self._should_include(cls.name):
                    lines.append(self.render_class(cls, depth=0))
                    lines.append("")

        # Functions
        if doc.functions:
            lines.append("## Functions")
            lines.append("")
            for func in doc.functions:
                if self._should_include(func.name):
                    lines.append(self.render_function(func, depth=0))
                    lines.append("")

        return "\n".join(lines)

    def render_class(self, doc: ClassDoc, depth: int = 0) -> str:
        """Render class documentation as Markdown.

        Args:
            doc: Class documentation.
            depth: Current nesting depth.

        Returns:
            Markdown string.
        """
        if depth > self.options.max_depth:
            return ""

        lines: list[str] = []
        header_level = "###" + "#" * depth

        # Class header
        lines.append(f"{header_level} {doc.name}")
        lines.append("")

        # Inheritance
        if doc.bases:
            bases_str = ", ".join(doc.bases)
            lines.append(f"**Inherits from:** `{bases_str}`")
            lines.append("")

        # Description
        if doc.description:
            lines.append(doc.description)
            lines.append("")

        # Deprecation warning
        if self.options.include_deprecation and doc.deprecated:
            lines.append("> **Deprecated:** This class is deprecated.")
            lines.append("")

        # Constructor
        if doc.init_params:
            lines.append(f"{header_level}# Constructor")
            lines.append("")
            lines.append("**Parameters:**")
            lines.append("")
            for param in doc.init_params:
                lines.append(self._render_parameter(param))
            lines.append("")

        # Attributes
        if doc.attributes:
            lines.append(f"{header_level}# Attributes")
            lines.append("")
            for attr_name, attr_info in doc.attributes.items():
                if self._should_include(attr_name):
                    type_str = f": `{attr_info['type']}`" if attr_info.get("type") else ""
                    desc = attr_info.get("description", "")
                    lines.append(f"- **{attr_name}**{type_str} - {desc}")
            lines.append("")

        # Methods
        if doc.methods:
            lines.append(f"{header_level}# Methods")
            lines.append("")
            for method in doc.methods:
                if self._should_include(method.name):
                    lines.append(self.render_function(method, depth=depth + 1))
                    lines.append("")

        # Examples
        if self.options.include_examples and doc.examples:
            lines.append(f"{header_level}# Examples")
            lines.append("")
            for example in doc.examples:
                lines.append("```python")
                lines.append(example)
                lines.append("```")
                lines.append("")

        return "\n".join(lines)

    def render_function(self, doc: FunctionDoc, depth: int = 0) -> str:
        """Render function documentation as Markdown.

        Args:
            doc: Function documentation.
            depth: Current nesting depth.

        Returns:
            Markdown string.
        """
        if depth > self.options.max_depth:
            return ""

        lines: list[str] = []
        header_level = "####" + "#" * depth

        # Function signature
        params_str = ", ".join(
            f"{p.name}: {p.type}" if p.type else p.name
            for p in doc.parameters
        )
        return_str = f" -> {doc.return_type}" if doc.return_type else ""
        async_prefix = "async " if doc.is_async else ""

        lines.append(f"{header_level} `{async_prefix}{doc.name}({params_str}){return_str}`")
        lines.append("")

        # Deprecation warning
        if self.options.include_deprecation and doc.deprecated:
            lines.append("> **Deprecated:** This function is deprecated.")
            lines.append("")

        # Description
        if doc.description:
            lines.append(doc.description)
            lines.append("")

        # Parameters
        if doc.parameters:
            lines.append("**Parameters:**")
            lines.append("")
            for param in doc.parameters:
                lines.append(self._render_parameter(param))
            lines.append("")

        # Returns
        if doc.return_type or doc.return_description:
            lines.append("**Returns:**")
            lines.append("")
            return_type = f"`{doc.return_type}`" if doc.return_type else "Any"
            return_desc = doc.return_description or ""
            lines.append(f"- {return_type} - {return_desc}")
            lines.append("")

        # Raises
        if doc.raises:
            lines.append("**Raises:**")
            lines.append("")
            for exc_type, exc_desc in doc.raises.items():
                lines.append(f"- `{exc_type}` - {exc_desc}")
            lines.append("")

        # Examples
        if self.options.include_examples and doc.examples:
            lines.append("**Examples:**")
            lines.append("")
            for example in doc.examples:
                lines.append("```python")
                lines.append(example)
                lines.append("```")
                lines.append("")

        return "\n".join(lines)

    def _render_parameter(self, param: ParameterDoc) -> str:
        """Render a parameter as Markdown list item.

        Args:
            param: Parameter documentation.

        Returns:
            Markdown list item.
        """
        type_str = f": `{param.type}`" if param.type else ""
        default_str = f" (default: `{param.default}`)" if param.default else ""
        required_str = " **(required)**" if param.required and not param.default else ""
        desc = param.description or ""

        return f"- **{param.name}**{type_str}{required_str}{default_str} - {desc}"


class HTMLRenderer(DocumentationRenderer):
    """Renders documentation as HTML."""

    def render_module(self, doc: ModuleDoc) -> str:
        """Render module documentation as HTML.

        Args:
            doc: Module documentation.

        Returns:
            HTML string.
        """
        prefix = self.options.css_class_prefix
        lines: list[str] = []

        lines.append(f'<div class="{prefix}-module">')

        # Module header
        lines.append(f'<h1 class="{prefix}-module-title">{html.escape(doc.name)}</h1>')

        if doc.description:
            lines.append(f'<div class="{prefix}-description">{html.escape(doc.description)}</div>')

        # Table of contents
        if self.options.toc and (doc.classes or doc.functions):
            lines.append(f'<nav class="{prefix}-toc">')
            lines.append(f'<h2 class="{prefix}-toc-title">Table of Contents</h2>')

            if doc.classes:
                lines.append(f'<div class="{prefix}-toc-section">')
                lines.append("<h3>Classes</h3>")
                lines.append("<ul>")
                for cls in doc.classes:
                    if self._should_include(cls.name):
                        anchor = cls.name.lower().replace("_", "-")
                        lines.append(f'<li><a href="#{anchor}">{html.escape(cls.name)}</a></li>')
                lines.append("</ul>")
                lines.append("</div>")

            if doc.functions:
                lines.append(f'<div class="{prefix}-toc-section">')
                lines.append("<h3>Functions</h3>")
                lines.append("<ul>")
                for func in doc.functions:
                    if self._should_include(func.name):
                        anchor = func.name.lower().replace("_", "-")
                        lines.append(f'<li><a href="#{anchor}">{html.escape(func.name)}</a></li>')
                lines.append("</ul>")
                lines.append("</div>")

            lines.append("</nav>")

        # Classes
        if doc.classes:
            lines.append(f'<section class="{prefix}-classes">')
            lines.append(f'<h2 class="{prefix}-section-title">Classes</h2>')
            for cls in doc.classes:
                if self._should_include(cls.name):
                    lines.append(self.render_class(cls, depth=0))
            lines.append("</section>")

        # Functions
        if doc.functions:
            lines.append(f'<section class="{prefix}-functions">')
            lines.append(f'<h2 class="{prefix}-section-title">Functions</h2>')
            for func in doc.functions:
                if self._should_include(func.name):
                    lines.append(self.render_function(func, depth=0))
            lines.append("</section>")

        lines.append("</div>")

        return "\n".join(lines)

    def render_class(self, doc: ClassDoc, depth: int = 0) -> str:
        """Render class documentation as HTML.

        Args:
            doc: Class documentation.
            depth: Current nesting depth.

        Returns:
            HTML string.
        """
        if depth > self.options.max_depth:
            return ""

        prefix = self.options.css_class_prefix
        anchor = doc.name.lower().replace("_", "-")
        lines: list[str] = []

        lines.append(f'<article class="{prefix}-class" id="{anchor}">')

        # Class header
        header_tag = f"h{min(3 + depth, 6)}"
        lines.append(f'<{header_tag} class="{prefix}-class-title">{html.escape(doc.name)}</{header_tag}>')

        # Inheritance
        if doc.bases:
            bases_str = ", ".join(html.escape(b) for b in doc.bases)
            lines.append(f'<div class="{prefix}-inheritance">Inherits from: <code>{bases_str}</code></div>')

        # Deprecation warning
        if self.options.include_deprecation and doc.deprecated:
            lines.append(f'<div class="{prefix}-deprecated">Deprecated: This class is deprecated.</div>')

        # Description
        if doc.description:
            lines.append(f'<div class="{prefix}-description">{html.escape(doc.description)}</div>')

        # Constructor
        if doc.init_params:
            lines.append(f'<div class="{prefix}-constructor">')
            lines.append("<h4>Constructor</h4>")
            lines.append(self._render_parameters_html(doc.init_params))
            lines.append("</div>")

        # Attributes
        if doc.attributes:
            lines.append(f'<div class="{prefix}-attributes">')
            lines.append("<h4>Attributes</h4>")
            lines.append("<dl>")
            for attr_name, attr_info in doc.attributes.items():
                if self._should_include(attr_name):
                    type_str = f": <code>{html.escape(attr_info.get('type', ''))}</code>" if attr_info.get("type") else ""
                    desc = html.escape(attr_info.get("description", ""))
                    lines.append(f"<dt><strong>{html.escape(attr_name)}</strong>{type_str}</dt>")
                    lines.append(f"<dd>{desc}</dd>")
            lines.append("</dl>")
            lines.append("</div>")

        # Methods
        if doc.methods:
            lines.append(f'<div class="{prefix}-methods">')
            lines.append("<h4>Methods</h4>")
            for method in doc.methods:
                if self._should_include(method.name):
                    lines.append(self.render_function(method, depth=depth + 1))
            lines.append("</div>")

        # Examples
        if self.options.include_examples and doc.examples:
            lines.append(f'<div class="{prefix}-examples">')
            lines.append("<h4>Examples</h4>")
            for example in doc.examples:
                code_class = "language-python" if self.options.syntax_highlight else ""
                lines.append(f'<pre><code class="{code_class}">{html.escape(example)}</code></pre>')
            lines.append("</div>")

        lines.append("</article>")

        return "\n".join(lines)

    def render_function(self, doc: FunctionDoc, depth: int = 0) -> str:
        """Render function documentation as HTML.

        Args:
            doc: Function documentation.
            depth: Current nesting depth.

        Returns:
            HTML string.
        """
        if depth > self.options.max_depth:
            return ""

        prefix = self.options.css_class_prefix
        anchor = doc.name.lower().replace("_", "-")
        lines: list[str] = []

        lines.append(f'<div class="{prefix}-function" id="{anchor}">')

        # Function signature
        params_str = ", ".join(
            f"{html.escape(p.name)}: {html.escape(p.type or '')}" if p.type else html.escape(p.name)
            for p in doc.parameters
        )
        return_str = f" -&gt; {html.escape(doc.return_type)}" if doc.return_type else ""
        async_prefix = "async " if doc.is_async else ""

        header_tag = f"h{min(4 + depth, 6)}"
        lines.append(
            f'<{header_tag} class="{prefix}-function-signature">'
            f'<code>{async_prefix}{html.escape(doc.name)}({params_str}){return_str}</code>'
            f'</{header_tag}>'
        )

        # Deprecation warning
        if self.options.include_deprecation and doc.deprecated:
            lines.append(f'<div class="{prefix}-deprecated">Deprecated: This function is deprecated.</div>')

        # Description
        if doc.description:
            lines.append(f'<div class="{prefix}-description">{html.escape(doc.description)}</div>')

        # Parameters
        if doc.parameters:
            lines.append(f'<div class="{prefix}-params">')
            lines.append("<h5>Parameters</h5>")
            lines.append(self._render_parameters_html(doc.parameters))
            lines.append("</div>")

        # Returns
        if doc.return_type or doc.return_description:
            lines.append(f'<div class="{prefix}-returns">')
            lines.append("<h5>Returns</h5>")
            return_type = html.escape(doc.return_type) if doc.return_type else "Any"
            return_desc = html.escape(doc.return_description or "")
            lines.append(f"<p><code>{return_type}</code> - {return_desc}</p>")
            lines.append("</div>")

        # Raises
        if doc.raises:
            lines.append(f'<div class="{prefix}-raises">')
            lines.append("<h5>Raises</h5>")
            lines.append("<dl>")
            for exc_type, exc_desc in doc.raises.items():
                lines.append(f"<dt><code>{html.escape(exc_type)}</code></dt>")
                lines.append(f"<dd>{html.escape(exc_desc)}</dd>")
            lines.append("</dl>")
            lines.append("</div>")

        # Examples
        if self.options.include_examples and doc.examples:
            lines.append(f'<div class="{prefix}-examples">')
            lines.append("<h5>Examples</h5>")
            for example in doc.examples:
                code_class = "language-python" if self.options.syntax_highlight else ""
                lines.append(f'<pre><code class="{code_class}">{html.escape(example)}</code></pre>')
            lines.append("</div>")

        lines.append("</div>")

        return "\n".join(lines)

    def _render_parameters_html(self, params: list[ParameterDoc]) -> str:
        """Render parameters as HTML definition list.

        Args:
            params: List of parameters.

        Returns:
            HTML string.
        """
        lines: list[str] = ["<dl>"]

        for param in params:
            type_str = f": <code>{html.escape(param.type)}</code>" if param.type else ""
            default_str = f" (default: <code>{html.escape(str(param.default))}</code>)" if param.default else ""
            required_str = " <em>(required)</em>" if param.required and not param.default else ""
            desc = html.escape(param.description or "")

            lines.append(f"<dt><strong>{html.escape(param.name)}</strong>{type_str}{required_str}{default_str}</dt>")
            lines.append(f"<dd>{desc}</dd>")

        lines.append("</dl>")
        return "\n".join(lines)


class JSONRenderer(DocumentationRenderer):
    """Renders documentation as JSON."""

    def render_module(self, doc: ModuleDoc) -> str:
        """Render module documentation as JSON.

        Args:
            doc: Module documentation.

        Returns:
            JSON string.
        """
        data = self._module_to_dict(doc)
        return json.dumps(data, indent=2, ensure_ascii=False)

    def render_class(self, doc: ClassDoc, depth: int = 0) -> str:
        """Render class documentation as JSON.

        Args:
            doc: Class documentation.
            depth: Current nesting depth.

        Returns:
            JSON string.
        """
        data = self._class_to_dict(doc, depth)
        return json.dumps(data, indent=2, ensure_ascii=False)

    def render_function(self, doc: FunctionDoc, depth: int = 0) -> str:
        """Render function documentation as JSON.

        Args:
            doc: Function documentation.
            depth: Current nesting depth.

        Returns:
            JSON string.
        """
        data = self._function_to_dict(doc)
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _module_to_dict(self, doc: ModuleDoc) -> dict[str, Any]:
        """Convert module documentation to dictionary.

        Args:
            doc: Module documentation.

        Returns:
            Dictionary representation.
        """
        return {
            "type": "module",
            "name": doc.name,
            "description": doc.description,
            "file_path": doc.file_path,
            "classes": [
                self._class_to_dict(cls, 0)
                for cls in doc.classes
                if self._should_include(cls.name)
            ],
            "functions": [
                self._function_to_dict(func)
                for func in doc.functions
                if self._should_include(func.name)
            ],
            "constants": doc.constants,
            "metadata": doc.metadata,
        }

    def _class_to_dict(self, doc: ClassDoc, depth: int) -> dict[str, Any]:
        """Convert class documentation to dictionary.

        Args:
            doc: Class documentation.
            depth: Current nesting depth.

        Returns:
            Dictionary representation.
        """
        methods = []
        if depth < self.options.max_depth:
            methods = [
                self._function_to_dict(method)
                for method in doc.methods
                if self._should_include(method.name)
            ]

        return {
            "type": "class",
            "name": doc.name,
            "description": doc.description,
            "bases": doc.bases,
            "deprecated": doc.deprecated,
            "init_params": [self._param_to_dict(p) for p in doc.init_params],
            "attributes": doc.attributes,
            "methods": methods,
            "examples": doc.examples if self.options.include_examples else [],
        }

    def _function_to_dict(self, doc: FunctionDoc) -> dict[str, Any]:
        """Convert function documentation to dictionary.

        Args:
            doc: Function documentation.

        Returns:
            Dictionary representation.
        """
        return {
            "type": "function",
            "name": doc.name,
            "description": doc.description,
            "parameters": [self._param_to_dict(p) for p in doc.parameters],
            "return_type": doc.return_type,
            "return_description": doc.return_description,
            "raises": doc.raises,
            "is_async": doc.is_async,
            "is_generator": doc.is_generator,
            "is_classmethod": doc.is_classmethod,
            "is_staticmethod": doc.is_staticmethod,
            "deprecated": doc.deprecated,
            "examples": doc.examples if self.options.include_examples else [],
        }

    def _param_to_dict(self, param: ParameterDoc) -> dict[str, Any]:
        """Convert parameter documentation to dictionary.

        Args:
            param: Parameter documentation.

        Returns:
            Dictionary representation.
        """
        return {
            "name": param.name,
            "type": param.type,
            "description": param.description,
            "default": param.default,
            "required": param.required,
        }


def render_documentation(
    doc: ModuleDoc | ClassDoc | FunctionDoc,
    format: str = "markdown",
    options: RenderOptions | None = None,
) -> str:
    """Render documentation in the specified format.

    This is a convenience function for rendering documentation
    without creating a renderer instance directly.

    Args:
        doc: Documentation to render.
        format: Output format (markdown, html, json).
        options: Rendering options.

    Returns:
        Rendered documentation string.

    Raises:
        ValueError: If format is not supported.

    Examples:
        >>> from truthound_dashboard.core.plugins.docs import (
        ...     DocumentationExtractor,
        ...     render_documentation,
        ... )
        >>> extractor = DocumentationExtractor()
        >>> module_doc = extractor.extract_module("my_plugin.py")
        >>> markdown = render_documentation(module_doc, "markdown")
        >>> html = render_documentation(module_doc, "html")
    """
    renderers = {
        "markdown": MarkdownRenderer,
        "md": MarkdownRenderer,
        "html": HTMLRenderer,
        "json": JSONRenderer,
    }

    format_lower = format.lower()
    if format_lower not in renderers:
        raise ValueError(
            f"Unsupported format: {format}. "
            f"Supported formats: {', '.join(renderers.keys())}"
        )

    renderer = renderers[format_lower](options)

    if isinstance(doc, ModuleDoc):
        return renderer.render_module(doc)
    elif isinstance(doc, ClassDoc):
        return renderer.render_class(doc)
    elif isinstance(doc, FunctionDoc):
        return renderer.render_function(doc)
    else:
        raise TypeError(f"Unsupported documentation type: {type(doc)}")
