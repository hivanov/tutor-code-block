# Copyright (C) 2024-present Open edX Community
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Syntax highlighting engine using Pygments and structured HTML line rendering.
Supports 500+ programming, markup, and configuration languages with data-driven registry.
"""

from __future__ import annotations

import html
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexer import RegexLexer
from pygments.lexers import (
    find_lexer_class,
    get_all_lexers,
    get_lexer_by_name,
)
from pygments.lexers.special import TextLexer
from pygments.token import Comment, Keyword, Name, Number, Operator, String, Text

from code_block_xblock.models import LanguageItem, StudentViewContext

if TYPE_CHECKING:
    from code_block_xblock.models import CodeBlockSettings

log = logging.getLogger(__name__)


class PromQLLexer(RegexLexer):
    """Pygments Lexer for Prometheus PromQL queries and alert rules."""

    name = "PromQL"
    aliases = ["promql"]
    filenames = ["*.promql"]

    tokens = {
        "root": [
            (r"\s+", Text),
            (r"#.*$", Comment.Single),
            (
                r"\b(rate|irate|increase|sum|avg|min|max|count|topk|bottomk|quantile|histogram_quantile|"
                r"histogram_fraction|delta|idelta|deriv|predict_linear|resets|changes|label_replace|"
                r"label_join|abs|ceil|floor|round|clamp|clamp_min|clamp_max|exp|ln|log2|log10|sqrt|"
                r"absent|absent_over_time|stddev|stdvar|count_values|group|sgn|sort|sort_desc|time|"
                r"timestamp|vector|scalar)\b",
                Name.Builtin,
            ),
            (r"\b(by|without|on|ignoring|group_left|group_right|bool|offset|atan2)\b", Keyword),
            (r"\b(and|or|unless)\b", Operator.Word),
            (r"[=~!\^\*\+\-\/%<>]=?", Operator),
            (r"[{}(),\[\]]", Operator),
            (r'"(\\\\|\\"|[^"])*"', String.Double),
            (r"'(\\\\|\\'|[^'])*'", String.Single),
            (r"[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?(?:[smhdwy])?", Number),
            (r"[a-zA-Z_:][a-zA-Z0-9_:]*", Name.Variable),
        ]
    }


# Common alias mappings for fast lookup
COMMON_ALIAS_MAP: dict[str, str] = {
    "py": "python",
    "python3": "python",
    "golang": "go",
    "rs": "rust",
    "js": "javascript",
    "ts": "typescript",
    "sh": "bash",
    "shell": "bash",
    "zsh": "bash",
    "yml": "yaml",
    "jsonc": "json",
    "dockerfile": "docker",
    "containerfile": "docker",
    "c++": "cpp",
    "cs": "csharp",
    "c#": "csharp",
    "kt": "kotlin",
    "rb": "ruby",
    "md": "markdown",
    "gql": "graphql",
    "plain": "text",
    "txt": "text",
}


def load_languages_registry() -> list[LanguageItem]:
    """Load pre-extracted language database or compute dynamically into Pydantic models."""
    data_path = Path(__file__).parent / "data" / "languages.json"
    if data_path.exists():
        try:
            raw_list = json.loads(data_path.read_text(encoding="utf-8"))
            return [LanguageItem.model_validate(item) for item in raw_list]
        except Exception:
            log.warning("Could not read languages.json, falling back to dynamic inspection")

    # Fallback to dynamic Pygments introspection
    registry: list[LanguageItem] = []
    seen = set()
    for name, aliases, filenames, mimetypes in get_all_lexers():
        if aliases:
            prim = aliases[0].lower()
            if prim not in seen:
                seen.add(prim)
                registry.append(
                    LanguageItem(
                        id=prim,
                        name=name,
                        aliases=list(aliases),
                        filenames=list(filenames),
                        mimetypes=list(mimetypes),
                        category="General",
                        is_popular=False,
                    )
                )
    return registry


def get_lexer_for_language(lang_name: str):
    """
    Retrieve the appropriate Pygments lexer for any language name or alias.
    Falls back gracefully to TextLexer if unrecognized.
    """
    norm = lang_name.strip().lower()
    if not norm:
        return TextLexer()

    if norm == "promql":
        return PromQLLexer()

    lookup_name = COMMON_ALIAS_MAP.get(norm, norm)

    try:
        return get_lexer_by_name(lookup_name)
    except Exception:
        pass

    try:
        lexer_cls = find_lexer_class(lookup_name)
        if lexer_cls:
            return lexer_cls()
    except Exception:
        pass

    return TextLexer()


def get_all_available_languages() -> list[LanguageItem]:
    """
    Return a list of all LanguageItem models supported by the system.
    """
    return load_languages_registry()


# Embedded SVG icons
ICON_FILE = (
    '<svg class="cb-icon cb-icon-file" viewBox="0 0 24 24" width="16" height="16" fill="none" '
    'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>'
    '<polyline points="14 2 14 8 20 8"></polyline>'
    '<line x1="16" y1="13" x2="8" y2="13"></line>'
    '<line x1="16" y1="17" x2="8" y2="17"></line>'
    '<polyline points="10 9 9 9 8 9"></polyline>'
    "</svg>"
)

ICON_COPY = (
    '<svg class="cb-icon cb-icon-copy" viewBox="0 0 24 24" width="15" height="15" fill="none" '
    'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>'
    '<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>'
    "</svg>"
)

ICON_CHECK = (
    '<svg class="cb-icon cb-icon-check" viewBox="0 0 24 24" width="15" height="15" fill="none" '
    'stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
    '<polyline points="20 6 9 17 4 12"></polyline>'
    "</svg>"
)


def render_code_html(settings: CodeBlockSettings) -> str:
    """
    Format and highlight raw code into a complete, safe HTML snippet with line numbers and line highlights.
    """
    raw_code = settings.raw_code
    lexer = get_lexer_for_language(settings.language)
    formatter = HtmlFormatter(nowrap=True)

    # Highlight via Pygments
    highlighted_raw = highlight(raw_code, lexer, formatter)

    # Split lines, preserving empty lines
    lines = highlighted_raw.splitlines()
    if not lines and raw_code == "":
        lines = [""]

    highlight_set = set(settings.highlight_lines)
    start_index = settings.line_number_start

    formatted_lines: list[str] = []
    for idx, line_content in enumerate(lines):
        line_num = start_index + idx
        is_highlighted = line_num in highlight_set
        highlight_class = " cb-line-highlighted" if is_highlighted else ""

        # Gutter line number HTML (user-select: none prevents copying numbers)
        if settings.line_numbers:
            gutter_html = f'<span class="cb-lineno" data-line="{line_num}" aria-hidden="true">{line_num}</span>'
        else:
            gutter_html = ""

        # Content HTML (empty line fallback)
        content_html = line_content if line_content else "&nbsp;"

        formatted_lines.append(
            f'<div class="cb-line{highlight_class}">'
            f"{gutter_html}"
            f'<span class="cb-code-line">{content_html}</span>'
            f"</div>"
        )

    return "".join(formatted_lines)


def build_student_view_context(settings: CodeBlockSettings) -> StudentViewContext:
    """Build strongly typed context model for the student view."""
    highlighted = render_code_html(settings)
    lines_count = len(settings.raw_code.splitlines()) if settings.raw_code else 1

    return StudentViewContext(
        title=settings.title,
        language_display=settings.language.upper(),
        language_name=settings.language,
        theme=settings.theme.value if hasattr(settings.theme, "value") else str(settings.theme),
        highlighted_html=highlighted,
        raw_code=settings.raw_code,
        line_numbers=settings.line_numbers,
        line_number_start=settings.line_number_start,
        highlight_lines=settings.highlight_lines,
        wrap_code=settings.wrap_code,
        show_copy_button=settings.show_copy_button,
        max_height_px=settings.max_height_px,
        total_lines=lines_count,
    )


def render_full_code_block_card(settings: CodeBlockSettings, element_id: str = "cb-card") -> str:
    """
    Render complete standalone HTML card for the code block component using validated context.
    """
    ctx = build_student_view_context(settings)
    theme_class = f"cb-theme-{ctx.theme}"
    wrap_class = " cb-wrap-code" if ctx.wrap_code else " cb-nowrap-code"
    gutter_class = " cb-has-gutter" if ctx.line_numbers else " cb-no-gutter"

    # Style attribute for max height
    style_attr = f' style="max-height: {ctx.max_height_px}px;"' if ctx.max_height_px > 0 else ""

    # Header components
    show_header = bool(ctx.title or ctx.show_copy_button or ctx.language_display)
    header_html = ""
    if show_header:
        # Title section
        if ctx.title:
            title_escaped = html.escape(ctx.title)
            title_section = f'<div class="cb-header-title">{ICON_FILE}<span>{title_escaped}</span></div>'
        else:
            title_section = '<div class="cb-header-title"></div>'

        # Action section (Language badge + Copy button)
        action_parts = []
        if ctx.language_display and ctx.language_display != "TEXT":
            action_parts.append(f'<span class="cb-lang-badge">{ctx.language_display}</span>')

        if ctx.show_copy_button:
            action_parts.append(
                f'<button type="button" class="cb-copy-btn" title="Copy code" aria-label="Copy code to clipboard">'
                f"{ICON_COPY}"
                f'<span class="cb-copy-text">Copy</span>'
                f"{ICON_CHECK}"
                f"</button>"
            )

        actions_section = f'<div class="cb-header-actions">{"".join(action_parts)}</div>'
        header_html = f'<div class="cb-header">{title_section}{actions_section}</div>'

    # Raw code encoded safely for copy button extraction
    raw_code_escaped = html.escape(ctx.raw_code)

    return f"""
<div id="{element_id}" class="cb-card {theme_class}{wrap_class}{gutter_class}">
    {header_html}
    <div class="cb-viewport"{style_attr}>
        <pre class="cb-pre"><code>{ctx.highlighted_html}</code></pre>
    </div>
    <textarea class="cb-raw-source" style="display:none;" aria-hidden="true">{raw_code_escaped}</textarea>
</div>
"""
