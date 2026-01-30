from __future__ import annotations

from typing import Any

from mcp.types import CallToolResult, TextContent

from hegelion.core.autocoding_state import AutocodingState
from hegelion.mcp.constants import MCP_SCHEMA_VERSION


def state_error(tool_name: str, message: str, *, error: str) -> CallToolResult:
    return CallToolResult(
        content=[TextContent(type="text", text=message)],
        structuredContent={
            "schema_version": MCP_SCHEMA_VERSION,
            "tool": tool_name,
            "error": error,
        },
        isError=True,
    )


def arg_error(
    tool_name: str,
    message: str,
    *,
    error: str,
    expected: Any | None = None,
    received: Any | None = None,
) -> CallToolResult:
    structured = {
        "schema_version": MCP_SCHEMA_VERSION,
        "tool": tool_name,
        "error": error,
    }
    if expected is not None:
        structured["expected"] = expected
    if received is not None:
        structured["received"] = received
    return CallToolResult(
        content=[TextContent(type="text", text=message)],
        structuredContent=structured,
        isError=True,
    )


def phase_error(tool_name: str, *, expected: str, received: str, hint: str) -> CallToolResult:
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=(
                    f"Error: Invalid phase for {tool_name}. "
                    f"Expected '{expected}', got '{received}'.\n\nHint: {hint}"
                ),
            )
        ],
        structuredContent={
            "schema_version": MCP_SCHEMA_VERSION,
            "tool": tool_name,
            "error": f"Invalid phase: {received}",
            "expected": expected,
            "received": received,
            "hint": hint,
        },
        isError=True,
    )


def require_str_arg(tool_name: str, arguments: dict[str, Any], key: str) -> str | CallToolResult:
    value = arguments.get(key)
    if not isinstance(value, str) or not value.strip():
        return arg_error(
            tool_name,
            f"Error: '{key}' must be a non-empty string.",
            error=f"Invalid argument: {key}",
            expected="non-empty string",
            received=value,
        )
    return value


def get_enum_arg(
    tool_name: str,
    arguments: dict[str, Any],
    key: str,
    allowed: set[str],
    default: str,
) -> str | CallToolResult:
    value = arguments.get(key, default)
    if value not in allowed:
        return arg_error(
            tool_name,
            f"Error: '{key}' must be one of {sorted(allowed)}.",
            error=f"Invalid argument: {key}",
            expected=sorted(allowed),
            received=value,
        )
    return value


def get_optional_bool(
    tool_name: str, arguments: dict[str, Any], key: str, default: bool
) -> bool | CallToolResult:
    if key not in arguments:
        return default
    value = arguments.get(key)
    if isinstance(value, bool):
        return value
    return arg_error(
        tool_name,
        f"Error: '{key}' must be a boolean.",
        error=f"Invalid argument: {key}",
        expected="boolean",
        received=value,
    )


def get_optional_int(
    tool_name: str, arguments: dict[str, Any], key: str, default: int, *, min_value: int
) -> int | CallToolResult:
    if key not in arguments:
        return default
    value = arguments.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        return arg_error(
            tool_name,
            f"Error: '{key}' must be an integer.",
            error=f"Invalid argument: {key}",
            expected="integer",
            received=value,
        )
    if value < min_value:
        return arg_error(
            tool_name,
            f"Error: '{key}' must be >= {min_value}.",
            error=f"Invalid argument: {key}",
            expected=f">={min_value}",
            received=value,
        )
    return value


def get_optional_number(
    tool_name: str,
    arguments: dict[str, Any],
    key: str,
    default: float,
    *,
    min_value: float,
    max_value: float,
) -> float | CallToolResult:
    if key not in arguments:
        return default
    value = arguments.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return arg_error(
            tool_name,
            f"Error: '{key}' must be a number.",
            error=f"Invalid argument: {key}",
            expected="number",
            received=value,
        )
    if not min_value <= float(value) <= max_value:
        return arg_error(
            tool_name,
            f"Error: '{key}' must be between {min_value} and {max_value}.",
            error=f"Invalid argument: {key}",
            expected=f"{min_value}..{max_value}",
            received=value,
        )
    return float(value)


def get_optional_str(
    tool_name: str,
    arguments: dict[str, Any],
    key: str,
    default: str | None = None,
) -> str | None | CallToolResult:
    if key not in arguments:
        return default
    value = arguments.get(key)
    if not isinstance(value, str) or not value.strip():
        return arg_error(
            tool_name,
            f"Error: '{key}' must be a non-empty string.",
            error=f"Invalid argument: {key}",
            expected="non-empty string",
            received=value,
        )
    return value


def parse_autocoding_state(tool_name: str, state_dict: Any) -> AutocodingState | CallToolResult:
    if not isinstance(state_dict, dict):
        return state_error(
            tool_name,
            "Error: Invalid autocoding state. Expected an object/dict.",
            error="Invalid autocoding state: expected object",
        )
    try:
        return AutocodingState.from_dict(state_dict)
    except (KeyError, TypeError, ValueError) as exc:
        return state_error(
            tool_name,
            f"Error: Invalid autocoding state: {exc}",
            error=f"Invalid autocoding state: {exc}",
        )
