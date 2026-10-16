"""
Unit and integration tests for CodeBlockXBlock runtime, views, handlers, and OLX XML serialization.
"""

import json
import xml.etree.ElementTree as ET
from typing import cast

import webob
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds
from xblock.test.tools import TestRuntime

from code_block_xblock.xblock import CodeBlockXBlock


def create_code_block_xblock() -> CodeBlockXBlock:
    """Helper to instantiate a CodeBlockXBlock inside a TestRuntime."""
    field_data = DictFieldData({})
    scope_ids = ScopeIds(
        user_id="test_student",
        block_type="code_block",
        def_id="def_1",
        usage_id="block-v1:Org+CS101+type@code_block+block@code1",
    )
    runtime = TestRuntime(services={"field-data": field_data})
    block = cast(CodeBlockXBlock, runtime.construct_xblock_from_class(CodeBlockXBlock, scope_ids=scope_ids))
    block.display_name = "Sample Code Block"
    block.title = "main.go"
    block.language = "go"
    block.raw_code = 'package main\n\nimport "fmt"\n\nfunc main() {\n    fmt.Println("Hello")\n}'
    block.theme = "one-dark-pro"
    block.line_numbers = True
    block.line_number_start = 1
    block.highlight_lines_raw = "5"
    block.wrap_code = False
    block.show_copy_button = True
    block.max_height_px = 350
    return block


def make_post_request(data: dict) -> webob.Request:
    """Create a WebOb POST request with JSON body."""
    req = webob.Request.blank("/")
    req.method = "POST"
    req.body = json.dumps(data).encode("utf-8")
    return req


def test_student_view_fragment():
    block = create_code_block_xblock()
    frag = block.student_view()

    assert frag is not None
    assert "cb-card" in frag.content
    assert "main.go" in frag.content
    assert "package main" in frag.content
    assert "cb-copy-btn" in frag.content
    assert "CodeBlockStudentView" in frag.js_init_fn


def test_studio_view_fragment():
    block = create_code_block_xblock()
    frag = block.studio_view()

    assert frag is not None
    assert "cb-studio-wrapper" in frag.content
    assert "cb-language" in frag.content
    assert "cb-theme" in frag.content
    assert "cb-raw-code" in frag.content
    assert "CodeBlockStudioView" in frag.js_init_fn


def test_studio_submit_success():
    block = create_code_block_xblock()
    payload = {
        "display_name": "Updated Server Code",
        "title": "server.rs",
        "language": "rust",
        "raw_code": 'fn main() {\n    println!("Rust Rocks!");\n}',
        "theme": "github-dark",
        "line_numbers": True,
        "line_number_start": 10,
        "highlight_lines_raw": "11-12",
        "wrap_code": True,
        "show_copy_button": True,
        "max_height_px": 500,
    }

    req = make_post_request(payload)
    resp = block.studio_submit(req)

    res_data = json.loads(resp.body) if isinstance(resp, webob.Response) else resp

    assert res_data["result"] == "success"
    assert block.display_name == "Updated Server Code"
    assert block.title == "server.rs"
    assert block.language == "rust"
    assert block.theme == "github-dark"
    assert block.line_number_start == 10
    assert block.highlight_lines_raw == "11-12"
    assert block.wrap_code is True
    assert block.max_height_px == 500


def test_studio_submit_validation_error():
    block = create_code_block_xblock()
    # Invalid negative line number start
    payload = {
        "line_number_start": -5,
    }

    req = make_post_request(payload)
    resp = block.studio_submit(req)

    # Should return WebOb 400 response
    assert isinstance(resp, webob.Response)
    assert resp.status_code == 400
    res_data = json.loads(resp.body)
    assert res_data["result"] == "error"


def test_olx_xml_roundtrip():
    block = create_code_block_xblock()

    # Export to XML node
    node = ET.Element("temp")
    block.add_xml_to_node(node)

    assert node.tag == "code_block_xblock"
    assert node.get("display_name") == "Sample Code Block"
    assert node.get("title") == "main.go"
    assert node.get("language") == "go"
    assert node.get("theme") == "one-dark-pro"
    assert node.get("line_numbers") == "true"
    assert node.get("line_number_start") == "1"
    assert node.get("highlight_lines") == "5"
    assert node.get("wrap_code") == "false"
    assert node.get("show_copy_button") == "true"
    assert node.get("max_height_px") == "350"
    assert "package main" in (node.text or "")

    # Parse back from XML node
    imported_block = block.parse_xml(
        node,
        runtime=block.runtime,
        keys=block.scope_ids,
        id_generator=None,
    )

    assert imported_block.display_name == "Sample Code Block"
    assert imported_block.title == "main.go"
    assert imported_block.language == "go"
    assert imported_block.theme == "one-dark-pro"
    assert imported_block.line_numbers is True
    assert imported_block.line_number_start == 1
    assert imported_block.highlight_lines_raw == "5"
    assert imported_block.wrap_code is False
    assert imported_block.show_copy_button is True
    assert imported_block.max_height_px == 350
    assert "package main" in imported_block.raw_code
