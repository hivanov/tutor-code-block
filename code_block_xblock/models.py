# Copyright (C) 2024-present Open edX Community
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Pydantic v2 data models, enums, and validators for Code Block XBlock.
All data contracts are strictly typed with comprehensive field metadata and validation rules.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CodeTheme(StrEnum):
    """Available visual themes for code block display."""

    ONE_DARK_PRO = "one-dark-pro"
    GITHUB_DARK = "github-dark"
    GITHUB_LIGHT = "github-light"
    MONOKAI = "monokai"
    DRACULA = "dracula"
    NORD = "nord"
    SOLARIZED_DARK = "solarized-dark"
    SOLARIZED_LIGHT = "solarized-light"


class LanguageItem(BaseModel):
    """Metadata schema representing a supported programming language or syntax format."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(
        description="Primary language alias/identifier (e.g. 'python', 'go', 'promql')",
        examples=["python", "go", "rust"],
    )
    name: str = Field(
        description="Human-readable language display name",
        examples=["Python", "Go (Golang)", "Rust"],
    )
    aliases: list[str] = Field(
        default_factory=list,
        description="All recognized aliases for this language",
        examples=[["py", "python", "python3"]],
    )
    filenames: list[str] = Field(
        default_factory=list,
        description="Associated filename glob patterns",
        examples=[["*.py", "*.pyw"]],
    )
    mimetypes: list[str] = Field(
        default_factory=list,
        description="MIME types associated with this syntax",
        examples=[["text/x-python"]],
    )
    category: str = Field(
        default="General",
        description="Functional category for grouped display in authoring UI",
        examples=["Backend / Data", "Systems", "Monitoring / Observability"],
    )
    is_popular: bool = Field(
        default=False,
        description="Flag indicating inclusion in the quick-access top section in Studio",
        examples=[True, False],
    )

    @field_validator("id", mode="before")
    @classmethod
    def normalize_id(cls, v: object) -> str:
        return str(v).strip().lower()

    @field_validator("name", mode="before")
    @classmethod
    def sanitize_name(cls, v: object) -> str:
        return str(v).strip()


class ThemeItem(BaseModel):
    """Metadata schema representing a selectable editor theme."""

    model_config = ConfigDict(extra="ignore")

    id: CodeTheme = Field(
        description="Theme enum identifier",
        examples=[CodeTheme.ONE_DARK_PRO, CodeTheme.GITHUB_DARK],
    )
    name: str = Field(
        description="Display name of the theme",
        examples=["One Dark Pro", "GitHub Dark", "GitHub Light"],
    )
    is_dark: bool = Field(
        default=True,
        description="Whether the theme is dark background",
        examples=[True, False],
    )


def get_available_theme_items() -> list[ThemeItem]:
    """Return strongly typed list of all available themes."""
    return [
        ThemeItem(id=CodeTheme.ONE_DARK_PRO, name="One Dark Pro (Default)", is_dark=True),
        ThemeItem(id=CodeTheme.GITHUB_DARK, name="GitHub Dark", is_dark=True),
        ThemeItem(id=CodeTheme.GITHUB_LIGHT, name="GitHub Light", is_dark=False),
        ThemeItem(id=CodeTheme.DRACULA, name="Dracula", is_dark=True),
        ThemeItem(id=CodeTheme.MONOKAI, name="Monokai", is_dark=True),
        ThemeItem(id=CodeTheme.NORD, name="Nord", is_dark=True),
        ThemeItem(id=CodeTheme.SOLARIZED_DARK, name="Solarized Dark", is_dark=True),
        ThemeItem(id=CodeTheme.SOLARIZED_LIGHT, name="Solarized Light", is_dark=False),
    ]


def parse_highlight_lines(raw: str) -> list[int]:
    """
    Parse a comma-separated string containing line numbers and ranges into a sorted list of unique ints.

    Examples:
        "1, 3, 5-8, 12" -> [1, 3, 5, 6, 7, 8, 12]
        "   " -> []
        "10-12, 10" -> [10, 11, 12]
    """
    if not raw or not raw.strip():
        return []

    lines_set: set[int] = set()
    tokens = [t.strip() for t in raw.split(",") if t.strip()]

    for token in tokens:
        range_match = re.match(r"^(\d+)\s*(?:-|(?:\.\.))\s*(\d+)$", token)
        if range_match:
            start, end = int(range_match.group(1)), int(range_match.group(2))
            if start > end:
                start, end = end, start
            for i in range(max(1, start), min(end + 1, 10000)):
                lines_set.add(i)
            continue

        if token.isdigit():
            val = int(token)
            if val >= 1:
                lines_set.add(val)

    return sorted(lines_set)


class CodeBlockSettings(BaseModel):
    """Comprehensive configuration schema for a Code Block component."""

    model_config = ConfigDict(extra="ignore")

    title: str = Field(
        default="",
        description="Filename or descriptive header for the snippet (e.g., 'main.go', 'nginx.conf')",
        examples=["main.go", "config.yaml", "Dockerfile"],
    )
    language: str = Field(
        default="python",
        description="Programming or configuration language identifier (supports all 500+ Pygments languages)",
        examples=["python", "go", "rust", "yaml", "promql", "solidity"],
    )
    raw_code: str = Field(
        default="",
        description="Raw, unescaped source code text to be formatted and highlighted",
        examples=["def hello():\n    print('Hello World!')"],
    )
    theme: CodeTheme = Field(
        default=CodeTheme.ONE_DARK_PRO,
        description="Syntax highlighting color theme",
        examples=[CodeTheme.ONE_DARK_PRO, CodeTheme.GITHUB_DARK],
    )
    line_numbers: bool = Field(
        default=True,
        description="Whether line numbers are displayed in the left gutter",
        examples=[True, False],
    )
    line_number_start: int = Field(
        default=1,
        ge=1,
        description="Starting line number index for line count display",
        examples=[1, 100],
    )
    highlight_lines_raw: str = Field(
        default="",
        description="Raw specification of line numbers/ranges to highlight (e.g. '2, 4-7, 10')",
        examples=["2, 4-7, 10"],
    )
    highlight_lines: list[int] = Field(
        default_factory=list,
        description="Parsed list of 1-based line numbers to visually emphasize",
        examples=[[2, 4, 5, 6, 7, 10]],
    )
    wrap_code: bool = Field(
        default=False,
        description="Whether code lines should soft wrap or enable horizontal scrolling",
        examples=[False, True],
    )
    show_copy_button: bool = Field(
        default=True,
        description="Whether to display the copy code button in the header",
        examples=[True, False],
    )
    max_height_px: int = Field(
        default=0,
        ge=0,
        description="Maximum viewport height in pixels before vertical scrolling (0 for unlimited)",
        examples=[0, 400],
    )

    @field_validator("title", mode="before")
    @classmethod
    def sanitize_title(cls, v: object) -> str:
        if v is None:
            return ""
        return str(v).strip()

    @field_validator("language", mode="before")
    @classmethod
    def sanitize_language(cls, v: object) -> str:
        if v is None:
            return "python"
        lang_str = str(v).strip().lower()
        return lang_str or "text"

    @field_validator("raw_code", mode="before")
    @classmethod
    def sanitize_code(cls, v: object) -> str:
        if v is None:
            return ""
        return str(v)

    @field_validator("highlight_lines_raw", mode="before")
    @classmethod
    def sanitize_highlight_raw(cls, v: object) -> str:
        if v is None:
            return ""
        return str(v).strip()

    @model_validator(mode="after")
    def sync_highlight_lines(self) -> CodeBlockSettings:
        parsed = parse_highlight_lines(self.highlight_lines_raw)
        object.__setattr__(self, "highlight_lines", parsed)
        return self


class StudioSubmitRequest(BaseModel):
    """Payload contract received when author saves changes in Studio editor modal."""

    model_config = ConfigDict(extra="ignore")

    display_name: str = Field(
        default="Code Block",
        description="Component display name in course outline",
        examples=["Go HTTP Server Snippet"],
    )
    title: str = Field(
        default="",
        description="Header title or filename",
        examples=["main.go"],
    )
    language: str = Field(
        default="python",
        description="Language identifier for syntax highlighting",
        examples=["go", "python", "yaml"],
    )
    theme: CodeTheme = Field(
        default=CodeTheme.ONE_DARK_PRO,
        description="Selected color scheme",
        examples=[CodeTheme.ONE_DARK_PRO, CodeTheme.GITHUB_DARK],
    )
    raw_code: str = Field(
        default="",
        description="Raw source code content",
        examples=["package main\n\nfunc main() {}"],
    )
    highlight_lines_raw: str = Field(
        default="",
        description="Line numbers or ranges to highlight",
        examples=["2, 4-6"],
    )
    line_number_start: int = Field(
        default=1,
        ge=1,
        description="First line number in gutter",
        examples=[1],
    )
    max_height_px: int = Field(
        default=0,
        ge=0,
        description="Max container height in pixels",
        examples=[0, 450],
    )
    line_numbers: bool = Field(
        default=True,
        description="Whether line numbers are displayed",
        examples=[True, False],
    )
    wrap_code: bool = Field(
        default=False,
        description="Whether lines soft-wrap",
        examples=[False, True],
    )
    show_copy_button: bool = Field(
        default=True,
        description="Whether to show copy button",
        examples=[True, False],
    )

    @field_validator("display_name", mode="before")
    @classmethod
    def sanitize_display_name(cls, v: object) -> str:
        if not v or not str(v).strip():
            return "Code Block"
        return str(v).strip()


class StudioSubmitResponse(BaseModel):
    """Response contract returned to Studio client after saving settings."""

    result: str = Field(
        description="Status flag: 'success' or 'error'",
        examples=["success", "error"],
    )
    message: str | None = Field(
        default=None,
        description="Human-readable outcome or validation failure explanation",
        examples=[None, "Line number start must be greater than or equal to 1"],
    )


class StudentViewContext(BaseModel):
    """Structured data context passed to the student view renderer."""

    title: str = Field(description="Snippet filename or header title", examples=["main.go"])
    language_display: str = Field(description="Uppercase display badge text", examples=["GO"])
    language_name: str = Field(description="Language identifier", examples=["go"])
    theme: str = Field(description="Active theme name", examples=["one-dark-pro"])
    highlighted_html: str = Field(description="Tokenized HTML string", examples=["<span>code</span>"])
    raw_code: str = Field(description="Raw source code", examples=["package main"])
    line_numbers: bool = Field(description="Line numbers visibility flag", examples=[True])
    line_number_start: int = Field(description="Initial line number", examples=[1])
    highlight_lines: list[int] = Field(description="Lines with active highlight", examples=[[1, 2]])
    wrap_code: bool = Field(description="Soft wrap flag", examples=[False])
    show_copy_button: bool = Field(description="Copy button visibility flag", examples=[True])
    max_height_px: int = Field(description="Max container height in pixels", examples=[0])
    total_lines: int = Field(description="Total line count", examples=[10])


class StudioViewContext(BaseModel):
    """Structured data context for rendering the Studio authoring editor."""

    display_name: str = Field(description="XBlock display name", examples=["Code Block"])
    title: str = Field(description="Header filename/title", examples=["main.go"])
    language: str = Field(description="Current language code", examples=["go"])
    popular_languages: Sequence[LanguageItem] = Field(description="List of popular languages for quick selection")
    all_languages: Sequence[LanguageItem] = Field(description="Complete list of 500+ available languages")
    raw_code: str = Field(description="Raw source code", examples=["package main"])
    theme: str = Field(description="Current theme", examples=["one-dark-pro"])
    themes: Sequence[ThemeItem] = Field(description="List of available themes")
    line_numbers: bool = Field(description="Line numbers toggle", examples=[True])
    line_number_start: int = Field(description="Line number starting index", examples=[1])
    highlight_lines_raw: str = Field(description="Line highlight ranges string", examples=["2, 4-6"])
    wrap_code: bool = Field(description="Wrap code toggle", examples=[False])
    show_copy_button: bool = Field(description="Show copy button toggle", examples=[True])
    max_height_px: int = Field(description="Max viewport height", examples=[0])
