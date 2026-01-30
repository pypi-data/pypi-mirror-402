from __future__ import annotations

import json
from typing import Any

from mcp.server import Server
from mcp.types import CallToolResult, TextContent

from hegelion.core.autocoding_state import AutocodingState, load_session, save_session
from hegelion.core.constants import AutocodingPhase
from hegelion.core.prompt_autocoding import PromptDrivenAutocoding, create_autocoding_workflow
from hegelion.mcp.constants import AUTOCODING_SKILL_MODES, MCP_SCHEMA_VERSION, ToolName
from hegelion.mcp.progress import send_progress
from hegelion.mcp.validation import (
    arg_error,
    get_enum_arg,
    get_optional_int,
    get_optional_number,
    get_optional_str,
    parse_autocoding_state,
    phase_error,
    require_str_arg,
)


def _session_label(state: AutocodingState) -> str:
    if state.session_name:
        return f"{state.session_name} ({state.session_id[:8]}...)"
    return f"{state.session_id[:8]}..."


async def handle_hegelion_entrypoint(app: Server, arguments: dict[str, Any]):
    await send_progress(app, "Preparing Hegelion autocoding entrypoint...", 1.0, 2.0)

    name = ToolName.HEGELION.value
    requirements = require_str_arg(name, arguments, "requirements")
    if isinstance(requirements, CallToolResult):
        return requirements
    mode = get_enum_arg(name, arguments, "mode", AUTOCODING_SKILL_MODES, "workflow")
    if isinstance(mode, CallToolResult):
        return mode
    max_turns = get_optional_int(name, arguments, "max_turns", 10, min_value=1)
    if isinstance(max_turns, CallToolResult):
        return max_turns
    approval_threshold = get_optional_number(
        name,
        arguments,
        "approval_threshold",
        0.9,
        min_value=0.0,
        max_value=1.0,
    )
    if isinstance(approval_threshold, CallToolResult):
        return approval_threshold
    session_name = get_optional_str(name, arguments, "session_name", None)
    if isinstance(session_name, CallToolResult):
        return session_name

    if mode == "init":
        state = AutocodingState.create(
            requirements=requirements,
            max_turns=max_turns,
            approval_threshold=approval_threshold,
            session_name=session_name,
        )

        await send_progress(app, "Autocoding session initialized", 2.0, 2.0)

        structured = {
            **state.to_dict(),
            "entrypoint": ToolName.HEGELION.value,
            "mode": mode,
        }
        response = f"""# HEGELION AUTOCODING SESSION INITIALIZED

**Session:** {_session_label(state)}
**Max Turns:** {max_turns}
**Approval Threshold:** {approval_threshold:.0%}

Next step: call `player_prompt` with the returned state."""

        return ([TextContent(type="text", text=response)], structured)

    if mode == "workflow":
        workflow = create_autocoding_workflow(requirements=requirements, max_turns=max_turns)
        workflow["schema_version"] = MCP_SCHEMA_VERSION
        workflow["entrypoint"] = ToolName.HEGELION.value
        workflow["mode"] = mode

        serialized = json.dumps(workflow, indent=2)
        summary = (
            "Hegelion autocoding workflow ready. Agents should read the structuredContent JSON "
            f"(mode='{mode}')."
        )
        contents = [
            TextContent(type="text", text=summary),
            TextContent(type="text", text=serialized),
        ]
        return (contents, workflow)

    await send_progress(app, "Generating single-shot autocoding prompt...", 2.0, 2.0)

    autocoding = PromptDrivenAutocoding()
    prompt_obj = autocoding.generate_single_shot_prompt(
        requirements=requirements,
        max_turns=max_turns,
    )

    structured = {
        "schema_version": MCP_SCHEMA_VERSION,
        **prompt_obj.to_dict(),
        "requirements": requirements,
        "max_turns": max_turns,
        "entrypoint": ToolName.HEGELION.value,
        "mode": mode,
    }

    response = f"""# HEGELION SINGLE-SHOT AUTOCODING PROMPT

{prompt_obj.prompt}

---
**Instructions:** {prompt_obj.instructions}
**Expected Format:** {prompt_obj.expected_format}"""

    return ([TextContent(type="text", text=response)], structured)


async def handle_autocoding_init(app: Server, arguments: dict[str, Any]):
    await send_progress(app, "Initializing autocoding session...", 1.0, 2.0)

    name = ToolName.AUTOCODING_INIT.value
    requirements = require_str_arg(name, arguments, "requirements")
    if isinstance(requirements, CallToolResult):
        return requirements
    max_turns = get_optional_int(name, arguments, "max_turns", 10, min_value=1)
    if isinstance(max_turns, CallToolResult):
        return max_turns
    approval_threshold = get_optional_number(
        name,
        arguments,
        "approval_threshold",
        0.9,
        min_value=0.0,
        max_value=1.0,
    )
    if isinstance(approval_threshold, CallToolResult):
        return approval_threshold
    session_name = get_optional_str(name, arguments, "session_name", None)
    if isinstance(session_name, CallToolResult):
        return session_name

    state = AutocodingState.create(
        requirements=requirements,
        max_turns=max_turns,
        approval_threshold=approval_threshold,
        session_name=session_name,
    )

    await send_progress(app, "Session initialized", 2.0, 2.0)

    structured = state.to_dict()
    response = f"""# AUTOCODING SESSION INITIALIZED

**Session:** {_session_label(state)}
**Max Turns:** {max_turns}
**Approval Threshold:** {approval_threshold:.0%}

The session is ready. Next step: call `player_prompt` with the returned state.

**Workflow:**
1. Call `player_prompt` with state -> Execute returned prompt
2. Call `coach_prompt` with state -> Execute returned prompt
3. Call `autocoding_advance` with coach feedback
4. Repeat until COACH APPROVED or timeout"""

    return ([TextContent(type="text", text=response)], structured)


async def handle_autocoding_workflow(app: Server, arguments: dict[str, Any]):
    name = ToolName.AUTOCODING_WORKFLOW.value
    requirements = require_str_arg(name, arguments, "requirements")
    if isinstance(requirements, CallToolResult):
        return requirements
    max_turns = get_optional_int(name, arguments, "max_turns", 10, min_value=1)
    if isinstance(max_turns, CallToolResult):
        return max_turns

    workflow = create_autocoding_workflow(requirements=requirements, max_turns=max_turns)
    workflow["schema_version"] = MCP_SCHEMA_VERSION

    serialized = json.dumps(workflow, indent=2)
    summary = (
        "Hegelion autocoding workflow ready. Agents should read the structuredContent JSON "
        f"for step sequencing (max_turns={max_turns})."
    )
    contents = [
        TextContent(type="text", text=summary),
        TextContent(type="text", text=serialized),
    ]
    return (contents, workflow)


async def handle_player_prompt(app: Server, arguments: dict[str, Any]):
    await send_progress(app, "Generating player prompt...", 1.0, 1.0)

    name = ToolName.PLAYER_PROMPT.value
    parsed_state = parse_autocoding_state(name, arguments.get("state"))
    if isinstance(parsed_state, CallToolResult):
        return parsed_state
    state = parsed_state

    if state.phase != AutocodingPhase.PLAYER.value:
        return phase_error(
            name,
            expected=AutocodingPhase.PLAYER.value,
            received=state.phase,
            hint=(
                "If you just called autocoding_init or autocoding_advance, pass that returned state "
                "into player_prompt."
            ),
        )

    autocoding = PromptDrivenAutocoding()
    prompt_obj = autocoding.generate_player_prompt(
        requirements=state.requirements,
        coach_feedback=state.last_coach_feedback,
        turn_number=state.current_turn + 1,
        max_turns=state.max_turns,
    )

    new_state = state.advance_to_coach()

    structured = {
        "schema_version": MCP_SCHEMA_VERSION,
        **prompt_obj.to_dict(),
        "current_phase": AutocodingPhase.PLAYER.value,
        "next_phase": new_state.phase,
        "state": new_state.to_dict(),
    }

    response = f"""# PLAYER PROMPT (Turn {state.current_turn + 1}/{state.max_turns})

{prompt_obj.prompt}

---
**Instructions:** {prompt_obj.instructions}
**Next Step:** After executing this prompt, call `coach_prompt` with the updated state."""

    return ([TextContent(type="text", text=response)], structured)


async def handle_coach_prompt(app: Server, arguments: dict[str, Any]):
    await send_progress(app, "Generating coach prompt...", 1.0, 1.0)

    name = ToolName.COACH_PROMPT.value
    parsed_state = parse_autocoding_state(name, arguments.get("state"))
    if isinstance(parsed_state, CallToolResult):
        return parsed_state
    state = parsed_state

    if state.phase != AutocodingPhase.COACH.value:
        return phase_error(
            name,
            expected=AutocodingPhase.COACH.value,
            received=state.phase,
            hint=(
                "Call player_prompt first; then pass the returned state (state.phase should be 'coach') "
                "into coach_prompt."
            ),
        )

    autocoding = PromptDrivenAutocoding()
    prompt_obj = autocoding.generate_coach_prompt(
        requirements=state.requirements,
        turn_number=state.current_turn + 1,
        max_turns=state.max_turns,
    )

    structured = {
        "schema_version": MCP_SCHEMA_VERSION,
        **prompt_obj.to_dict(),
        "current_phase": AutocodingPhase.COACH.value,
        "next_phase": state.phase,
        "state": state.to_dict(),
    }

    response = f"""# COACH PROMPT (Turn {state.current_turn + 1}/{state.max_turns})

{prompt_obj.prompt}

---
**Instructions:** {prompt_obj.instructions}
**Next Step:** After executing this prompt, call `autocoding_advance` with the coach's feedback."""

    return ([TextContent(type="text", text=response)], structured)


async def handle_autocoding_advance(app: Server, arguments: dict[str, Any]):
    await send_progress(app, "Advancing autocoding state...", 1.0, 2.0)

    name = ToolName.AUTOCODING_ADVANCE.value
    state_dict = arguments.get("state")
    coach_feedback = require_str_arg(name, arguments, "coach_feedback")
    if isinstance(coach_feedback, CallToolResult):
        return coach_feedback
    approved = arguments.get("approved")
    if not isinstance(approved, bool):
        return arg_error(
            name,
            "Error: 'approved' is required and must be a boolean.",
            error="Invalid argument: approved",
            expected="boolean",
            received=approved,
        )
    compliance_score = arguments.get("compliance_score")
    if compliance_score is not None:
        compliance_score = get_optional_number(
            name,
            arguments,
            "compliance_score",
            0.0,
            min_value=0.0,
            max_value=1.0,
        )
        if isinstance(compliance_score, CallToolResult):
            return compliance_score

    parsed_state = parse_autocoding_state(name, state_dict)
    if isinstance(parsed_state, CallToolResult):
        return parsed_state
    state = parsed_state

    if state.phase != AutocodingPhase.COACH.value:
        return phase_error(
            name,
            expected=AutocodingPhase.COACH.value,
            received=state.phase,
            hint="Call coach_prompt first and pass its returned state into autocoding_advance.",
        )

    new_state = state.advance_turn(
        coach_feedback=coach_feedback,
        approved=approved,
        compliance_score=compliance_score,
    )

    await send_progress(app, "State advanced", 2.0, 2.0)

    structured = new_state.to_dict()

    if new_state.status == "approved":
        response = f"""# AUTOCODING COMPLETE - APPROVED

**Session:** {new_state.session_id[:8]}...
**Turns Used:** {new_state.current_turn}/{new_state.max_turns}
**Final Status:** APPROVED

The implementation has been verified by the coach and meets all requirements."""

    elif new_state.status == "timeout":
        response = f"""# AUTOCODING COMPLETE - TIMEOUT

**Session:** {new_state.session_id[:8]}...
**Turns Used:** {new_state.current_turn}/{new_state.max_turns}
**Final Status:** TIMEOUT

Maximum turns reached without approval. Review the turn history for progress made."""

    else:
        response = f"""# AUTOCODING - CONTINUING

**Session:** {new_state.session_id[:8]}...
**Turn:** {new_state.current_turn + 1}/{new_state.max_turns}
**Status:** {new_state.status}

**Next Step:** Call `player_prompt` with the updated state to continue implementation."""

    return ([TextContent(type="text", text=response)], structured)


async def handle_autocoding_single_shot(app: Server, arguments: dict[str, Any]):
    await send_progress(app, "Generating single-shot autocoding prompt...", 1.0, 1.0)

    name = ToolName.AUTOCODING_SINGLE_SHOT.value
    requirements = require_str_arg(name, arguments, "requirements")
    if isinstance(requirements, CallToolResult):
        return requirements
    max_turns = get_optional_int(name, arguments, "max_turns", 10, min_value=1)
    if isinstance(max_turns, CallToolResult):
        return max_turns

    autocoding = PromptDrivenAutocoding()
    prompt_obj = autocoding.generate_single_shot_prompt(
        requirements=requirements,
        max_turns=max_turns,
    )

    structured = {
        "schema_version": MCP_SCHEMA_VERSION,
        **prompt_obj.to_dict(),
        "requirements": requirements,
        "max_turns": max_turns,
    }

    response = f"""# SINGLE-SHOT AUTOCODING PROMPT

{prompt_obj.prompt}

---
**Instructions:** {prompt_obj.instructions}
**Expected Format:** {prompt_obj.expected_format}"""

    return ([TextContent(type="text", text=response)], structured)


async def handle_autocoding_save(app: Server, arguments: dict[str, Any]):
    name = ToolName.AUTOCODING_SAVE.value
    state_dict = arguments.get("state")
    filepath = require_str_arg(name, arguments, "filepath")
    if isinstance(filepath, CallToolResult):
        return filepath

    parsed_state = parse_autocoding_state(name, state_dict)
    if isinstance(parsed_state, CallToolResult):
        return parsed_state
    state = parsed_state
    save_session(state, filepath)

    structured = {
        "schema_version": MCP_SCHEMA_VERSION,
        "session_id": state.session_id,
        "filepath": filepath,
        "saved": True,
    }
    response = f"""# SESSION SAVED

**Session ID:** {state.session_id[:8]}...
**Saved to:** {filepath}
**Phase:** {state.phase}
**Turn:** {state.current_turn + 1}/{state.max_turns}

Session saved successfully. Use `autocoding_load` with the filepath to restore."""

    return ([TextContent(type="text", text=response)], structured)


async def handle_autocoding_load(app: Server, arguments: dict[str, Any]):
    name = ToolName.AUTOCODING_LOAD.value
    filepath = require_str_arg(name, arguments, "filepath")
    if isinstance(filepath, CallToolResult):
        return filepath

    try:
        state = load_session(filepath)
    except FileNotFoundError:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: Session file not found: {filepath}")],
            structuredContent={
                "schema_version": MCP_SCHEMA_VERSION,
                "error": f"File not found: {filepath}",
            },
            isError=True,
        )
    except json.JSONDecodeError as exc:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: Invalid JSON in session file: {exc}")],
            structuredContent={
                "schema_version": MCP_SCHEMA_VERSION,
                "error": f"Invalid JSON: {str(exc)}",
            },
            isError=True,
        )

    structured = state.to_dict()
    response = f"""# SESSION LOADED

**Session ID:** {state.session_id[:8]}...
**Loaded from:** {filepath}
**Phase:** {state.phase}
**Status:** {state.status}
**Turn:** {state.current_turn + 1}/{state.max_turns}

Session restored. Continue with the appropriate tool based on phase:
- If phase is "player": call `player_prompt`
- If phase is "coach": call `coach_prompt`"""

    return ([TextContent(type="text", text=response)], structured)
