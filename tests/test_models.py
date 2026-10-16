"""
Tests for Pydantic v2 models and line range parser in code_block_xblock.models.
"""

import pytest
from pydantic import ValidationError

from code_block_xblock.models import (
    CodeBlockSettings,
    CodeTheme,
    LanguageItem,
    StudentViewContext,
    StudioSubmitRequest,
    StudioSubmitResponse,
    StudioViewContext,
    ThemeItem,
    get_available_theme_items,
    parse_highlight_lines,
)


@pytest.mark.parametrize(
    "raw_input,expected",
    [
        ("", []),
        ("   ", []),
        ("5", [5]),
        ("1, 3, 5", [1, 3, 5]),
        ("5-8", [5, 6, 7, 8]),
        ("8-5", [5, 6, 7, 8]),  # Inverted range
        ("5..8", [5, 6, 7, 8]),  # Dot range notation
        ("1, 3, 5-7, 10, 12-14", [1, 3, 5, 6, 7, 10, 12, 13, 14]),
        ("3, 3, 3, 4, 4-6", [3, 4, 5, 6]),  # Deduplication
        ("0, -5, abc, 4", [4]),  # Ignore non-positive & non-digit
        ("100-103", [100, 101, 102, 103]),
    ],
)
def test_parse_highlight_lines(raw_input: str, expected: list[int]):
    result = parse_highlight_lines(raw_input)
    assert result == expected


def test_code_block_settings_defaults():
    settings = CodeBlockSettings()
    assert settings.title == ""
    assert settings.language == "python"
    assert settings.raw_code == ""
    assert settings.theme == CodeTheme.ONE_DARK_PRO
    assert settings.line_numbers is True
    assert settings.line_number_start == 1
    assert settings.highlight_lines_raw == ""
    assert settings.highlight_lines == []
    assert settings.wrap_code is False
    assert settings.show_copy_button is True
    assert settings.max_height_px == 0


def test_code_block_settings_sanitization():
    settings = CodeBlockSettings(
        title="   my_script.py   ",
        language="  GoLang  ",
        raw_code="package main\n\nfunc main() {}",
        highlight_lines_raw="  2, 4-6  ",
        theme=CodeTheme.GITHUB_DARK,
        line_number_start=10,
        max_height_px=450,
    )

    assert settings.title == "my_script.py"
    assert settings.language == "golang"
    assert settings.highlight_lines == [2, 4, 5, 6]
    assert settings.line_number_start == 10
    assert settings.max_height_px == 450


def test_code_block_settings_bounds_validation():
    with pytest.raises(ValidationError):
        CodeBlockSettings(line_number_start=0)

    with pytest.raises(ValidationError):
        CodeBlockSettings(max_height_px=-50)


def test_language_item_and_theme_item_models():
    lang = LanguageItem(
        id="  PyThOn  ",
        name=" Python 3 ",
        aliases=["py", "python3"],
        filenames=["*.py"],
        mimetypes=["text/x-python"],
        category="Backend / Data",
        is_popular=True,
    )
    assert lang.id == "python"
    assert lang.name == "Python 3"
    assert lang.is_popular is True

    themes = get_available_theme_items()
    assert len(themes) >= 6
    assert any(t.id == CodeTheme.ONE_DARK_PRO for t in themes)


def test_studio_submit_contracts():
    req = StudioSubmitRequest(
        display_name="HTTP Handler",
        title="server.go",
        language="go",
        theme=CodeTheme.GITHUB_DARK,
        raw_code="func Handle() {}",
        highlight_lines_raw="1",
        line_number_start=1,
        max_height_px=400,
        line_numbers=True,
        wrap_code=False,
        show_copy_button=True,
    )
    assert req.display_name == "HTTP Handler"
    assert req.language == "go"

    res = StudioSubmitResponse(result="success")
    assert res.result == "success"
    assert res.message is None


def test_student_and_studio_context_models():
    student_ctx = StudentViewContext(
        title="server.go",
        language_display="GO",
        language_name="go",
        theme="one-dark-pro",
        highlighted_html="<div>code</div>",
        raw_code="package main",
        line_numbers=True,
        line_number_start=1,
        highlight_lines=[1],
        wrap_code=False,
        show_copy_button=True,
        max_height_px=300,
        total_lines=1,
    )
    assert student_ctx.title == "server.go"
    assert student_ctx.total_lines == 1

    lang_item = LanguageItem(id="python", name="Python")
    theme_item = ThemeItem(id=CodeTheme.ONE_DARK_PRO, name="One Dark Pro")

    studio_ctx = StudioViewContext(
        display_name="Code Block",
        title="main.py",
        language="python",
        popular_languages=[lang_item],
        all_languages=[lang_item],
        raw_code="print('hi')",
        theme="one-dark-pro",
        themes=[theme_item],
        line_numbers=True,
        line_number_start=1,
        highlight_lines_raw="1",
        wrap_code=False,
        show_copy_button=True,
        max_height_px=0,
    )
    assert studio_ctx.language == "python"
