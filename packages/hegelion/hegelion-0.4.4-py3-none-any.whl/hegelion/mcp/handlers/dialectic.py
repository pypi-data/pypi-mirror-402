from __future__ import annotations

import json
from typing import Any

from mcp.server import Server
from mcp.types import CallToolResult, TextContent

from hegelion.core.prompt_dialectic import PromptDrivenDialectic
from hegelion.core.prompt_dialectic import create_dialectical_workflow
from hegelion.core.prompt_dialectic import create_single_shot_dialectic_prompt
from hegelion.mcp.constants import MCP_SCHEMA_VERSION, RESPONSE_STYLES, ToolName, WORKFLOW_FORMATS
from hegelion.mcp.progress import send_progress
from hegelion.mcp.response import (
    DIALECTIC_PHASE_SCHEMAS,
    phase_schema_for_style,
    response_schema_for_style,
    response_style_summary,
)
from hegelion.mcp.validation import get_enum_arg, get_optional_bool, require_str_arg


def _prompt_structured(prompt_obj: Any, response_style: str) -> dict[str, Any]:
    structured = {
        "schema_version": MCP_SCHEMA_VERSION,
        "phase": prompt_obj.phase,
        "prompt": prompt_obj.prompt,
        "instructions": prompt_obj.instructions,
        "expected_format": prompt_obj.expected_format,
        "response_style": response_style,
    }
    response_schema = phase_schema_for_style(response_style, prompt_obj.phase)
    if response_schema:
        structured["response_schema"] = response_schema
    return structured


def _render_prompt_response(title: str, prompt_obj: Any) -> str:
    return f"""# {title}

{prompt_obj.prompt}

**Instructions:** {prompt_obj.instructions}
**Expected Format:** {prompt_obj.expected_format}"""


async def handle_dialectical_workflow(app: Server, arguments: dict[str, Any]):
    name = ToolName.DIALECTICAL_WORKFLOW.value
    query = require_str_arg(name, arguments, "query")
    if isinstance(query, CallToolResult):
        return query
    use_search = get_optional_bool(name, arguments, "use_search", False)
    if isinstance(use_search, CallToolResult):
        return use_search
    use_council = get_optional_bool(name, arguments, "use_council", False)
    if isinstance(use_council, CallToolResult):
        return use_council
    use_judge = get_optional_bool(name, arguments, "use_judge", False)
    if isinstance(use_judge, CallToolResult):
        return use_judge
    format_type = get_enum_arg(name, arguments, "format", WORKFLOW_FORMATS, "workflow")
    if isinstance(format_type, CallToolResult):
        return format_type
    response_style = get_enum_arg(name, arguments, "response_style", RESPONSE_STYLES, "sections")
    if isinstance(response_style, CallToolResult):
        return response_style

    await send_progress(app, "━━━ Preparing dialectical workflow ━━━", 1.0)

    if format_type == "single_prompt":
        await send_progress(app, "━━━ Generating single-shot prompt ━━━", 2.0)
        prompt = create_single_shot_dialectic_prompt(
            query=query,
            use_search=use_search,
            use_council=use_council,
            response_style=response_style,
        )
        await send_progress(app, "━━━ Prompt ready ━━━", 3.0)
        structured = {
            "schema_version": MCP_SCHEMA_VERSION,
            "query": query,
            "format": "single_prompt",
            "use_search": use_search,
            "use_council": use_council,
            "response_style": response_style,
            "prompt": prompt,
        }
        response_schema = response_schema_for_style(response_style)
        if response_schema:
            structured["response_schema"] = response_schema
        return ([TextContent(type="text", text=prompt)], structured)

    await send_progress(app, "━━━ THESIS prompt ready ━━━", 1.0)
    await send_progress(app, "━━━ ANTITHESIS prompt ready ━━━", 2.0)
    await send_progress(app, "━━━ SYNTHESIS prompt ready ━━━", 3.0)
    workflow = create_dialectical_workflow(
        query=query,
        use_search=use_search,
        use_council=use_council,
        use_judge=use_judge,
        response_style=response_style,
    )
    workflow["schema_version"] = MCP_SCHEMA_VERSION
    workflow.setdefault("instructions", {})
    workflow["instructions"]["response_style"] = response_style
    workflow["instructions"]["response_style_note"] = response_style_summary(response_style)
    response_schema = response_schema_for_style(response_style)
    if response_schema:
        workflow["instructions"]["response_schema"] = response_schema
        workflow["instructions"]["phase_schemas"] = DIALECTIC_PHASE_SCHEMAS

    serialized = json.dumps(workflow, indent=2)
    summary = (
        "Hegelion dialectical workflow ready. Agents should read the structuredContent JSON. "
        f"Human-readable summary: query='{query}', response_style='{response_style}'."
    )
    contents = [
        TextContent(type="text", text=summary),
        TextContent(type="text", text=serialized),
    ]
    return (contents, workflow)


async def handle_dialectical_single_shot(app: Server, arguments: dict[str, Any]):
    name = ToolName.DIALECTICAL_SINGLE_SHOT.value
    query = require_str_arg(name, arguments, "query")
    if isinstance(query, CallToolResult):
        return query
    use_search = get_optional_bool(name, arguments, "use_search", False)
    if isinstance(use_search, CallToolResult):
        return use_search
    use_council = get_optional_bool(name, arguments, "use_council", False)
    if isinstance(use_council, CallToolResult):
        return use_council
    response_style = get_enum_arg(name, arguments, "response_style", RESPONSE_STYLES, "sections")
    if isinstance(response_style, CallToolResult):
        return response_style

    prompt = create_single_shot_dialectic_prompt(
        query=query,
        use_search=use_search,
        use_council=use_council,
        response_style=response_style,
    )

    structured = {
        "schema_version": MCP_SCHEMA_VERSION,
        "query": query,
        "use_search": use_search,
        "use_council": use_council,
        "response_style": response_style,
        "prompt": prompt,
    }
    response_schema = response_schema_for_style(response_style)
    if response_schema:
        structured["response_schema"] = response_schema
    note = response_style_summary(response_style)
    contents = [
        TextContent(type="text", text=f"{note}\n\n{prompt}"),
    ]
    return (contents, structured)


async def handle_thesis_prompt(app: Server, arguments: dict[str, Any]):
    await send_progress(app, "━━━ THESIS ━━━ Generating prompt...", 1.0, 1.0)
    name = ToolName.THESIS_PROMPT.value
    query = require_str_arg(name, arguments, "query")
    if isinstance(query, CallToolResult):
        return query
    response_style = get_enum_arg(name, arguments, "response_style", RESPONSE_STYLES, "sections")
    if isinstance(response_style, CallToolResult):
        return response_style

    dialectic = PromptDrivenDialectic()
    prompt_obj = dialectic.generate_thesis_prompt(query, response_style=response_style)

    structured = _prompt_structured(prompt_obj, response_style)
    response = _render_prompt_response("THESIS PROMPT", prompt_obj)

    return ([TextContent(type="text", text=response)], structured)


async def handle_antithesis_prompt(app: Server, arguments: dict[str, Any]):
    await send_progress(app, "━━━ ANTITHESIS ━━━ Generating prompt...", 1.0, 1.0)
    name = ToolName.ANTITHESIS_PROMPT.value
    query = require_str_arg(name, arguments, "query")
    if isinstance(query, CallToolResult):
        return query
    thesis = require_str_arg(name, arguments, "thesis")
    if isinstance(thesis, CallToolResult):
        return thesis
    use_search = get_optional_bool(name, arguments, "use_search", False)
    if isinstance(use_search, CallToolResult):
        return use_search
    use_council = get_optional_bool(name, arguments, "use_council", False)
    if isinstance(use_council, CallToolResult):
        return use_council
    response_style = get_enum_arg(name, arguments, "response_style", RESPONSE_STYLES, "sections")
    if isinstance(response_style, CallToolResult):
        return response_style

    dialectic = PromptDrivenDialectic()

    if use_council:
        council_prompts = dialectic.generate_council_prompts(
            query, thesis, response_style=response_style
        )
        response_parts = ["# COUNCIL ANTITHESIS PROMPTS\n"]
        structured_prompts = []

        for prompt_obj in council_prompts:
            response_parts.append(f"## {prompt_obj.phase.replace('_', ' ').title()}")
            response_parts.append(prompt_obj.prompt)
            response_parts.append(f"**Instructions:** {prompt_obj.instructions}")
            response_parts.append("")
            structured_prompts.append(_prompt_structured(prompt_obj, response_style))

        structured = {
            "schema_version": MCP_SCHEMA_VERSION,
            "prompts": structured_prompts,
            "phase": "antithesis_council",
            "response_style": response_style,
        }
        response = "\n".join(response_parts)
    else:
        prompt_obj = dialectic.generate_antithesis_prompt(
            query, thesis, use_search, response_style=response_style
        )
        structured = _prompt_structured(prompt_obj, response_style)
        response = _render_prompt_response("ANTITHESIS PROMPT", prompt_obj)

    return ([TextContent(type="text", text=response)], structured)


async def handle_synthesis_prompt(app: Server, arguments: dict[str, Any]):
    await send_progress(app, "━━━ SYNTHESIS ━━━ Generating prompt...", 1.0, 1.0)
    name = ToolName.SYNTHESIS_PROMPT.value
    query = require_str_arg(name, arguments, "query")
    if isinstance(query, CallToolResult):
        return query
    thesis = require_str_arg(name, arguments, "thesis")
    if isinstance(thesis, CallToolResult):
        return thesis
    antithesis = require_str_arg(name, arguments, "antithesis")
    if isinstance(antithesis, CallToolResult):
        return antithesis
    response_style = get_enum_arg(name, arguments, "response_style", RESPONSE_STYLES, "sections")
    if isinstance(response_style, CallToolResult):
        return response_style

    dialectic = PromptDrivenDialectic()
    prompt_obj = dialectic.generate_synthesis_prompt(
        query, thesis, antithesis, response_style=response_style
    )

    structured = _prompt_structured(prompt_obj, response_style)
    response = _render_prompt_response("SYNTHESIS PROMPT", prompt_obj)

    return ([TextContent(type="text", text=response)], structured)
