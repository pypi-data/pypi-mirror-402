"""Tests for MCP validation helpers."""

from mcp.types import CallToolResult

from hegelion.core.autocoding_state import AutocodingState
from hegelion.mcp.validation import (
    get_enum_arg,
    get_optional_bool,
    get_optional_int,
    get_optional_number,
    parse_autocoding_state,
    require_str_arg,
)


def test_require_str_arg_invalid():
    result = require_str_arg("tool", {}, "query")

    assert isinstance(result, CallToolResult)
    assert result.isError is True
    assert result.structuredContent["error"] == "Invalid argument: query"
    assert result.structuredContent["expected"] == "non-empty string"


def test_require_str_arg_valid():
    result = require_str_arg("tool", {"query": "hi"}, "query")

    assert result == "hi"


def test_get_enum_arg_invalid():
    result = get_enum_arg("tool", {"format": "bad"}, "format", {"one", "two"}, "one")

    assert isinstance(result, CallToolResult)
    assert result.isError is True
    assert result.structuredContent["expected"] == ["one", "two"]
    assert result.structuredContent["received"] == "bad"


def test_get_optional_bool_invalid():
    result = get_optional_bool("tool", {"use_search": "yes"}, "use_search", False)

    assert isinstance(result, CallToolResult)
    assert result.isError is True
    assert result.structuredContent["expected"] == "boolean"


def test_get_optional_int_rejects_bool():
    result = get_optional_int("tool", {"max_turns": True}, "max_turns", 3, min_value=1)

    assert isinstance(result, CallToolResult)
    assert result.isError is True


def test_get_optional_number_bounds():
    result = get_optional_number("tool", {"score": 2.0}, "score", 0.5, min_value=0.0, max_value=1.0)

    assert isinstance(result, CallToolResult)
    assert result.isError is True


def test_parse_autocoding_state_invalid_type():
    result = parse_autocoding_state("tool", "not-a-dict")

    assert isinstance(result, CallToolResult)
    assert result.isError is True
    assert "Invalid autocoding state" in result.structuredContent["error"]


def test_parse_autocoding_state_valid():
    state = AutocodingState.create(requirements="- [ ] Test\n")

    parsed = parse_autocoding_state("tool", state.to_dict())

    assert isinstance(parsed, AutocodingState)
    assert parsed.session_id == state.session_id
