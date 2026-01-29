"""Plugin Documentation System.

This module provides:
- AST-based documentation extraction
- Multiple renderers (Markdown, HTML, JSON)
- Auto-generated API documentation
"""

from __future__ import annotations

from .extractor import (
    DocumentationExtractor,
    ModuleDoc,
    ClassDoc,
    FunctionDoc,
    ParameterDoc,
)
from .renderers import (
    DocumentationRenderer,
    MarkdownRenderer,
    HTMLRenderer,
    JSONRenderer,
    render_documentation,
)

__all__ = [
    # Extractor
    "DocumentationExtractor",
    "ModuleDoc",
    "ClassDoc",
    "FunctionDoc",
    "ParameterDoc",
    # Renderers
    "DocumentationRenderer",
    "MarkdownRenderer",
    "HTMLRenderer",
    "JSONRenderer",
    "render_documentation",
]
