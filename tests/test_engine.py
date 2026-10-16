# Copyright (C) 2024-present Open edX Community
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for syntax highlighting engine and HTML rendering.
"""

import pytest

from code_block_xblock.engine import (
    get_all_available_languages,
    get_lexer_for_language,
    render_code_html,
    render_full_code_block_card,
)
from code_block_xblock.models import CodeBlockSettings, CodeTheme


@pytest.mark.parametrize(
    "lang,snippet,expected_token_sub",
    [
        ("python", "def calculate(x: int) -> int:\n    return x * 2", "calculate"),
        ("go", "package main\n\nfunc main() {\n    println(42)\n}", "func"),
        ("rust", 'fn main() {\n    println!("hello");\n}', "fn"),
        ("bash", 'echo "Deploying..." && exit 0', "echo"),
        ("yaml", "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: app", "Deployment"),
        ("json", '{"name": "tutor-code-block", "version": 1}', "version"),
        ("promql", "histogram_quantile(0.99, sum(rate(http_requests_total[5m])) by (le))", "histogram_quantile"),
        ("dockerfile", "FROM golang:1.22-alpine\nWORKDIR /app\nCOPY . .\nCMD [\"./server\"]", "FROM"),
        ("sql", "SELECT id, name, COUNT(*) FROM users GROUP BY id;", "SELECT"),
        ("typescript", "interface User { id: string; active: boolean; }", "interface"),
        ("html", '<div class="container"><span>Hello</span></div>', "container"),
        ("markdown", "# Title\n\n**Bold Text** and `code`", "Title"),
    ],
)
def test_syntax_highlighting_tokens(lang: str, snippet: str, expected_token_sub: str):
    settings = CodeBlockSettings(
        language=lang,
        raw_code=snippet,
        title="example",
        line_numbers=True,
    )
    html_output = render_code_html(settings)
    assert expected_token_sub in html_output
    assert 'class="cb-line' in html_output
    assert 'class="cb-lineno"' in html_output


def test_html_entity_escaping_safety():
    dangerous_code = '<script>alert("XSS")</script> & "quotes" \'single\''
    settings = CodeBlockSettings(
        language="html",
        raw_code=dangerous_code,
        title="<script>alert(1)</script>",
    )
    card_html = render_full_code_block_card(settings)

    # Ensure dangerous tags are not rendered as raw executable HTML tags
    assert "<script>alert" not in card_html
    assert "&lt;script&gt;alert" in card_html or "&lt;span" in card_html


def test_line_highlighting_rendering():
    code = "line 1\nline 2\nline 3\nline 4\nline 5"
    settings = CodeBlockSettings(
        language="text",
        raw_code=code,
        line_numbers=True,
        line_number_start=1,
        highlight_lines_raw="2, 4-5",
    )
    html_output = render_code_html(settings)

    lines = [line_div for line_div in html_output.split("</div>") if '<div class="cb-line' in line_div]
    assert len(lines) == 5

    # Line 1: normal
    assert "cb-line-highlighted" not in lines[0]
    # Line 2: highlighted
    assert "cb-line-highlighted" in lines[1]
    # Line 3: normal
    assert "cb-line-highlighted" not in lines[2]
    # Line 4: highlighted
    assert "cb-line-highlighted" in lines[3]
    # Line 5: highlighted
    assert "cb-line-highlighted" in lines[4]


def test_custom_line_number_start():
    code = "first\nsecond\nthird"
    settings = CodeBlockSettings(
        language="text",
        raw_code=code,
        line_numbers=True,
        line_number_start=50,
        highlight_lines_raw="51",
    )
    html_output = render_code_html(settings)
    assert 'data-line="50"' in html_output
    assert 'data-line="51"' in html_output
    assert 'data-line="52"' in html_output
    assert "cb-line-highlighted" in html_output


def test_line_numbers_disabled():
    code = "line A\nline B"
    settings = CodeBlockSettings(
        language="text",
        raw_code=code,
        line_numbers=False,
    )
    html_output = render_code_html(settings)
    assert 'class="cb-lineno"' not in html_output
    assert "line A" in html_output


def test_render_full_code_block_card():
    settings = CodeBlockSettings(
        title="main.py",
        language="python",
        raw_code="print('Hello World')",
        theme=CodeTheme.GITHUB_DARK,
        line_numbers=True,
        show_copy_button=True,
        max_height_px=400,
        wrap_code=True,
    )
    card_html = render_full_code_block_card(settings, element_id="test-card-1")

    assert 'id="test-card-1"' in card_html
    assert "cb-theme-github-dark" in card_html
    assert "cb-wrap-code" in card_html
    assert 'style="max-height: 400px;"' in card_html
    assert "main.py" in card_html
    assert "PYTHON" in card_html
    assert "cb-copy-btn" in card_html
    assert "cb-raw-source" in card_html


def test_language_fallback_and_all_languages_registry():
    # Unknown language string should fall back cleanly without crashing
    unknown_lexer = get_lexer_for_language("totally_unknown_lang_12345")
    assert unknown_lexer is not None

    all_langs = get_all_available_languages()
    assert len(all_langs) >= 100
    assert any(lang.id == "python" for lang in all_langs)
    assert any(lang.id == "go" for lang in all_langs)
    assert any(lang.id == "rust" for lang in all_langs)
    assert any(lang.id == "promql" for lang in all_langs)
