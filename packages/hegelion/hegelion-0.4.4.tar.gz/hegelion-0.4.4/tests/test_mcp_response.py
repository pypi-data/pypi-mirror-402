"""Tests for MCP response helpers."""

from hegelion.core.constants import DialecticPhase
from hegelion.mcp.response import (
    DIALECTIC_PHASE_SCHEMAS,
    DIALECTIC_RESULT_SCHEMA,
    phase_schema_for_style,
    response_schema_for_style,
    response_style_summary,
)


def test_response_style_summary_json():
    summary = response_style_summary("json")

    assert "JSON object" in summary


def test_response_schema_for_style():
    assert response_schema_for_style("sections") is None
    assert response_schema_for_style("json") == DIALECTIC_RESULT_SCHEMA


def test_phase_schema_for_style_json():
    thesis_schema = phase_schema_for_style("json", DialecticPhase.THESIS.value)
    council_schema = phase_schema_for_style("json", "council_the_logician")

    assert thesis_schema is not None
    assert council_schema is not None
    assert "thesis" in thesis_schema["required"]
    assert "antithesis" in council_schema["required"]


def test_phase_schema_for_style_non_json():
    assert phase_schema_for_style("sections", DialecticPhase.THESIS.value) is None


def test_phase_schema_keys_align_with_phases():
    assert set(DIALECTIC_PHASE_SCHEMAS.keys()) == DialecticPhase.values()
