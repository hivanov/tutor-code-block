# Copyright (C) 2024-present Open edX Community
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
CodeBlockXBlock: Open edX XBlock component for interactive, highlighted code snippets.
Supports 500+ languages via data-driven Pygments registry and Pydantic v2 validation contracts.
"""

from __future__ import annotations

import html
import json
import logging
from pathlib import Path
from typing import Any, cast

from web_fragments.fragment import Fragment
from webob import Response
from xblock.core import XBlock
from xblock.fields import Boolean, Integer, Scope, String

from code_block_xblock.engine import get_all_available_languages, render_full_code_block_card
from code_block_xblock.models import (
    CodeBlockSettings,
    CodeTheme,
    StudioSubmitRequest,
    StudioSubmitResponse,
    StudioViewContext,
    get_available_theme_items,
)

log = logging.getLogger(__name__)


class CodeBlockXBlock(XBlock):
    """
    Open edX XBlock component that renders formatted code blocks with syntax
    highlighting, line numbers, line highlighting, and copy button.
    """

    display_name = String(
        display_name="Display Name",
        default="Code Block",
        scope=Scope.settings,
        help="The display name for this component in the course navigation.",
    )

    title = String(
        display_name="File Name / Title",
        default="",
        scope=Scope.content,
        help="Optional title or filename displayed in the code block header (e.g. 'main.go', 'docker-compose.yml').",
    )

    language = String(
        display_name="Language",
        default="python",
        scope=Scope.content,
        help="Programming language or configuration format for syntax highlighting.",
    )

    raw_code = String(
        display_name="Source Code",
        default="def main():\n    print('Hello Open edX!')\n",
        scope=Scope.content,
        help="Raw source code content to display.",
    )

    theme = String(
        display_name="Theme",
        default="one-dark-pro",
        scope=Scope.content,
        help="Color theme for code highlighting.",
    )

    line_numbers = Boolean(
        display_name="Show Line Numbers",
        default=True,
        scope=Scope.content,
        help="Whether to show line numbers in the gutter.",
    )

    line_number_start = Integer(
        display_name="Start Line Number",
        default=1,
        scope=Scope.content,
        help="Starting line number index for line count display.",
    )

    highlight_lines_raw = String(
        display_name="Highlighted Lines",
        default="",
        scope=Scope.content,
        help="Comma-separated lines and ranges to emphasize (e.g. '2, 4-7, 10').",
    )

    wrap_code = Boolean(
        display_name="Soft Wrap Lines",
        default=False,
        scope=Scope.content,
        help="Whether long lines should wrap instead of horizontal scrolling.",
    )

    show_copy_button = Boolean(
        display_name="Show Copy Button",
        default=True,
        scope=Scope.content,
        help="Whether to show the copy to clipboard button in the header.",
    )

    max_height_px = Integer(
        display_name="Max Height (px)",
        default=0,
        scope=Scope.content,
        help="Maximum container height before vertical scrolling (0 for unlimited).",
    )

    # Resource loading helper
    @staticmethod
    def _load_resource(path: str) -> str:
        """Load text from the static directory."""
        static_dir = Path(__file__).parent / "static"
        file_path = static_dir / path
        if file_path.exists():
            return file_path.read_text(encoding="utf-8")
        return ""

    def get_settings_model(self) -> CodeBlockSettings:
        """Construct validated Pydantic CodeBlockSettings from XBlock fields."""
        try:
            thm = CodeTheme(self.theme)
        except ValueError:
            thm = CodeTheme.ONE_DARK_PRO

        return CodeBlockSettings(
            title=self.title or "",
            language=self.language or "python",
            raw_code=self.raw_code or "",
            theme=thm,
            line_numbers=self.line_numbers,
            line_number_start=self.line_number_start or 1,
            highlight_lines_raw=self.highlight_lines_raw or "",
            wrap_code=self.wrap_code,
            show_copy_button=self.show_copy_button,
            max_height_px=self.max_height_px or 0,
        )

    def student_view(self, context: dict[str, Any] | None = None) -> Fragment:
        """Render the student-facing interactive code card."""
        settings = self.get_settings_model()
        element_id = f"cb-card-{self.location.block_id if hasattr(self, 'location') and self.location else 'preview'}"
        card_html = render_full_code_block_card(settings, element_id=element_id)

        frag = Fragment(card_html)
        css_content = self._load_resource("css/code_block_student.css")
        js_content = self._load_resource("js/code_block_student.js")

        if css_content:
            frag.add_css(css_content)
        if js_content:
            frag.add_javascript(js_content)

        frag.initialize_js("CodeBlockStudentView", {"element_id": element_id})
        return frag

    def build_studio_context(self) -> StudioViewContext:
        """Construct strongly typed Studio context model."""
        all_langs = get_all_available_languages()
        popular_langs = [item for item in all_langs if item.is_popular]
        theme_items = get_available_theme_items()

        return StudioViewContext(
            display_name=self.display_name or "Code Block",
            title=self.title or "",
            language=self.language or "python",
            popular_languages=popular_langs,
            all_languages=all_langs,
            raw_code=self.raw_code or "",
            theme=self.theme or "one-dark-pro",
            themes=theme_items,
            line_numbers=self.line_numbers,
            line_number_start=self.line_number_start or 1,
            highlight_lines_raw=self.highlight_lines_raw or "",
            wrap_code=self.wrap_code,
            show_copy_button=self.show_copy_button,
            max_height_px=self.max_height_px or 0,
        )

    def studio_view(self, context: dict[str, Any] | None = None) -> Fragment:
        """Render the Studio editor interface for course authors."""
        ctx = self.build_studio_context()

        # Build Popular Languages group
        popular_opts = []
        popular_ids = set()
        for lang_item in ctx.popular_languages:
            popular_ids.add(lang_item.id)
            selected = " selected" if lang_item.id == ctx.language else ""
            popular_opts.append(f'<option value="{lang_item.id}"{selected}>{html.escape(lang_item.name)}</option>')

        # Build All Languages group
        all_opts = []
        for lang_item in ctx.all_languages:
            if lang_item.id not in popular_ids:
                selected = " selected" if lang_item.id == ctx.language else ""
                all_opts.append(
                    f'<option value="{lang_item.id}"{selected}>{html.escape(lang_item.name)} ({lang_item.id})</option>'
                )

        # If current language is custom / not in list
        custom_opt = ""
        if ctx.language not in popular_ids and not any(litem.id == ctx.language for litem in ctx.all_languages):
            custom_opt = f'<option value="{html.escape(ctx.language)}" selected>{html.escape(ctx.language)} (Custom)</option>'

        pop_str = "\n".join(popular_opts)
        all_str = "\n".join(all_opts)
        lang_select_html = f"""
        <optgroup label="Popular Languages">
            {pop_str}
        </optgroup>
        {custom_opt}
        <optgroup label="All Languages (500+)">
            {all_str}
        </optgroup>
        """

        # Theme dropdown options
        theme_options = [
            f'<option value="{thm.id.value}"{" selected" if thm.id.value == ctx.theme else ""}>{html.escape(thm.name)}</option>'
            for thm in ctx.themes
        ]
        theme_select_html = "\n".join(theme_options)

        escaped_title = html.escape(ctx.title)
        escaped_display_name = html.escape(ctx.display_name)
        escaped_highlight = html.escape(ctx.highlight_lines_raw)
        escaped_code = html.escape(ctx.raw_code)

        studio_html = f"""
<div class="cb-studio-wrapper">
    <div class="cb-studio-header">
        <h3>Edit Code Block</h3>
        <p class="cb-studio-subtitle">Configure language, source code, styling and line emphasis</p>
    </div>

    <form class="cb-studio-form">
        <div class="cb-form-group">
            <label for="cb-display-name">Display Name</label>
            <input type="text" id="cb-display-name" class="cb-input" value="{escaped_display_name}" />
            <span class="cb-help">The name shown in Studio unit lists</span>
        </div>

        <div class="cb-form-row">
            <div class="cb-form-group cb-col">
                <label for="cb-title">File Name / Header Title</label>
                <input type="text" id="cb-title" class="cb-input" value="{escaped_title}" placeholder="e.g. main.go, deployment.yaml" />
                <span class="cb-help">Optional filename displayed at top of block</span>
            </div>

            <div class="cb-form-group cb-col">
                <label for="cb-language">Language (500+ supported)</label>
                <select id="cb-language" class="cb-select">
                    {lang_select_html}
                </select>
                <span class="cb-help">Language syntax highlighting engine</span>
            </div>

            <div class="cb-form-group cb-col">
                <label for="cb-theme">Theme</label>
                <select id="cb-theme" class="cb-select">
                    {theme_select_html}
                </select>
                <span class="cb-help">Color scheme for highlighted tokens</span>
            </div>
        </div>

        <div class="cb-form-group">
            <label for="cb-raw-code">Source Code (paste raw unescaped code)</label>
            <textarea id="cb-raw-code" class="cb-textarea" rows="14" spellcheck="false">{escaped_code}</textarea>
            <span class="cb-help">Tab key indents with 4 spaces. HTML/XML is safely escaped automatically.</span>
        </div>

        <div class="cb-form-row">
            <div class="cb-highlight-container cb-form-group cb-col">
                <label for="cb-highlight-lines">Highlight Lines</label>
                <input type="text" id="cb-highlight-lines" class="cb-input" value="{escaped_highlight}" placeholder="e.g. 2, 4-7, 10" />
                <span class="cb-help">Comma-separated lines or ranges to emphasize</span>
            </div>

            <div class="cb-line-controls cb-form-row">
                <div class="cb-form-group cb-col">
                    <label for="cb-line-start">Starting Line Number</label>
                    <input type="number" id="cb-line-start" class="cb-input" value="{ctx.line_number_start}" min="1" />
                    <span class="cb-help">First number in the gutter (default: 1)</span>
                </div>

                <div class="cb-form-group cb-col">
                    <label for="cb-max-height">Max Viewport Height (px)</label>
                    <input type="number" id="cb-max-height" class="cb-input" value="{ctx.max_height_px}" min="0" step="50" />
                    <span class="cb-help">0 for unlimited height / auto-expand</span>
                </div>
            </div>
        </div>

        <div class="cb-form-row cb-checkbox-row">
            <label class="cb-checkbox-label">
                <input type="checkbox" id="cb-line-numbers" {"checked" if ctx.line_numbers else ""} />
                <span>Show Line Numbers</span>
            </label>

            <label class="cb-checkbox-label">
                <input type="checkbox" id="cb-wrap-code" {"checked" if ctx.wrap_code else ""} />
                <span>Soft Wrap Long Lines</span>
            </label>

            <label class="cb-checkbox-label">
                <input type="checkbox" id="cb-copy-button" {"checked" if ctx.show_copy_button else ""} />
                <span>Show Copy Button</span>
            </label>
        </div>

        <div class="cb-studio-actions">
            <button type="button" class="cb-btn cb-btn-primary cb-save-button">Save Changes</button>
            <button type="button" class="cb-btn cb-btn-secondary cb-cancel-button">Cancel</button>
            <span class="cb-save-status" aria-live="polite"></span>
        </div>
    </form>
</div>
"""
        frag = Fragment(studio_html)
        css_content = self._load_resource("css/code_block_studio.css")
        js_content = self._load_resource("js/code_block_studio.js")

        if css_content:
            frag.add_css(css_content)
        if js_content:
            frag.add_javascript(js_content)

        frag.initialize_js("CodeBlockStudioView")
        return frag

    @XBlock.json_handler
    def studio_submit(self, data: dict[str, Any] | Any, suffix: str = "") -> dict[str, Any] | Response:
        """Handle saving settings from Studio authoring modal via typed Pydantic contract."""
        try:
            # Handle incoming WebOb request or raw dict
            if hasattr(data, "body"):
                body_bytes = data.body
                raw_dict = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
            elif isinstance(data, dict):
                raw_dict = data
            else:
                raw_dict = {}

            # Validate input through Pydantic v2 StudioSubmitRequest model
            req = StudioSubmitRequest.model_validate(raw_dict)

            # Apply settings to XBlock fields
            self.display_name = req.display_name
            self.title = req.title
            self.language = req.language
            self.raw_code = req.raw_code
            self.theme = req.theme.value
            self.line_numbers = req.line_numbers
            self.line_number_start = req.line_number_start
            self.highlight_lines_raw = req.highlight_lines_raw
            self.wrap_code = req.wrap_code
            self.show_copy_button = req.show_copy_button
            self.max_height_px = req.max_height_px

            response_model = StudioSubmitResponse(result="success")
            return response_model.model_dump()

        except Exception as err:
            log.exception("Validation error saving Code Block settings")
            err_response = StudioSubmitResponse(result="error", message=str(err))
            response = Response(
                json_body=err_response.model_dump(),
                status=400,
                content_type="application/json",
            )
            return response

    # OLX Serialization & Deserialization
    def parse_xml(self, node: Any, runtime: Any, keys: Any, id_generator: Any) -> CodeBlockXBlock:
        """Parse XML when importing OLX courses."""
        block: CodeBlockXBlock = cast(
            CodeBlockXBlock,
            runtime.construct_xblock_from_class(CodeBlockXBlock, keys),
        )

        block.display_name = node.get("display_name", "Code Block")
        block.title = node.get("title", "")
        block.language = node.get("language", "python")
        block.theme = node.get("theme", "one-dark-pro")
        block.line_numbers = node.get("line_numbers", "true").lower() == "true"
        block.line_number_start = int(node.get("line_number_start", "1"))
        block.highlight_lines_raw = node.get("highlight_lines", "")
        block.wrap_code = node.get("wrap_code", "false").lower() == "true"
        block.show_copy_button = node.get("show_copy_button", "true").lower() == "true"
        block.max_height_px = int(node.get("max_height_px", "0"))

        # Node text contains the raw code
        if node.text:
            block.raw_code = node.text
        else:
            block.raw_code = ""

        return block

    def add_xml_to_node(self, node: Any) -> None:
        """Export XBlock settings to OLX XML node."""
        node.tag = "code_block_xblock"
        node.set("display_name", self.display_name or "Code Block")
        if self.title:
            node.set("title", self.title)
        node.set("language", self.language or "python")
        node.set("theme", self.theme or "one-dark-pro")
        node.set("line_numbers", "true" if self.line_numbers else "false")
        node.set("line_number_start", str(self.line_number_start or 1))
        if self.highlight_lines_raw:
            node.set("highlight_lines", self.highlight_lines_raw)
        node.set("wrap_code", "true" if self.wrap_code else "false")
        node.set("show_copy_button", "true" if self.show_copy_button else "false")
        node.set("max_height_px", str(self.max_height_px or 0))

        # Store raw source in text node
        node.text = self.raw_code or ""
