from __future__ import annotations

from enum import Enum

MCP_SCHEMA_VERSION = 1


class ToolName(str, Enum):
    DIALECTICAL_WORKFLOW = "dialectical_workflow"
    DIALECTICAL_SINGLE_SHOT = "dialectical_single_shot"
    THESIS_PROMPT = "thesis_prompt"
    ANTITHESIS_PROMPT = "antithesis_prompt"
    SYNTHESIS_PROMPT = "synthesis_prompt"
    HEGELION = "hegelion"
    AUTOCODING_INIT = "autocoding_init"
    AUTOCODING_WORKFLOW = "autocoding_workflow"
    PLAYER_PROMPT = "player_prompt"
    COACH_PROMPT = "coach_prompt"
    AUTOCODING_ADVANCE = "autocoding_advance"
    AUTOCODING_SINGLE_SHOT = "autocoding_single_shot"
    AUTOCODING_SAVE = "autocoding_save"
    AUTOCODING_LOAD = "autocoding_load"


RESPONSE_STYLE_ENUM = (
    "sections",
    "synthesis_only",
    "json",
    "conversational",
    "bullet_points",
)
RESPONSE_STYLES = set(RESPONSE_STYLE_ENUM)

WORKFLOW_FORMAT_ENUM = ("workflow", "single_prompt")
WORKFLOW_FORMATS = set(WORKFLOW_FORMAT_ENUM)

AUTOCODING_SKILL_MODES_ENUM = ("init", "workflow", "single_shot")
AUTOCODING_SKILL_MODES = set(AUTOCODING_SKILL_MODES_ENUM)
