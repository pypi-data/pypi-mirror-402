from __future__ import annotations

from hegelion.mcp.handlers.autocoding import (
    handle_autocoding_advance,
    handle_autocoding_init,
    handle_autocoding_load,
    handle_autocoding_save,
    handle_autocoding_single_shot,
    handle_autocoding_workflow,
    handle_coach_prompt,
    handle_hegelion_entrypoint,
    handle_player_prompt,
)
from hegelion.mcp.handlers.dialectic import (
    handle_antithesis_prompt,
    handle_dialectical_single_shot,
    handle_dialectical_workflow,
    handle_synthesis_prompt,
    handle_thesis_prompt,
)

__all__ = [
    "handle_autocoding_advance",
    "handle_autocoding_init",
    "handle_autocoding_load",
    "handle_autocoding_save",
    "handle_autocoding_single_shot",
    "handle_autocoding_workflow",
    "handle_coach_prompt",
    "handle_hegelion_entrypoint",
    "handle_player_prompt",
    "handle_antithesis_prompt",
    "handle_dialectical_single_shot",
    "handle_dialectical_workflow",
    "handle_synthesis_prompt",
    "handle_thesis_prompt",
]
