"""Tests for the new response styles in Hegelion."""

import pytest
from hegelion.core.prompt_dialectic import create_single_shot_dialectic_prompt


class TestResponseStyles:
    """Test suite for response styles functionality."""

    def test_conversational_style_format(self):
        """Test that conversational style includes proper formatting instructions."""
        prompt = create_single_shot_dialectic_prompt(
            query="Test query for conversational style", response_style="conversational"
        )

        # Check for conversational-specific instructions
        assert "natural, conversational tone" in prompt
        assert "thoughtful colleague explaining your reasoning" in prompt
        assert "but on the other hand" in prompt
        assert "so perhaps the best way forward is" in prompt
        # Ensure it doesn't have rigid markdown headings
        assert "Avoid rigid headings like ## THESIS" in prompt

    def test_bullet_points_style_format(self):
        """Test that bullet_points style includes proper formatting instructions."""
        prompt = create_single_shot_dialectic_prompt(
            query="Test query for bullet points style", response_style="bullet_points"
        )

        # Check for bullet points specific instructions
        assert "concise set of bullet points" in prompt
        assert "**Thesis**: [Key point]" in prompt
        assert "**Antithesis**: [Key counter-point]" in prompt
        assert "**Synthesis**: [Resolution]" in prompt
        assert "Keep it brief and scannable" in prompt

    def test_json_style_unchanged(self):
        """Test that json style still works as before."""
        prompt = create_single_shot_dialectic_prompt(
            query="Test query for json style", response_style="json"
        )

        # Check for JSON-specific instructions
        assert '"query":' in prompt
        assert '"thesis":' in prompt
        assert '"antithesis":' in prompt
        assert '"synthesis":' in prompt
        assert "No markdown, no commentary outside the JSON" in prompt

    def test_sections_style_unchanged(self):
        """Test that sections style still works as before."""
        prompt = create_single_shot_dialectic_prompt(
            query="Test query for sections style", response_style="sections"
        )

        # Should use default formatting with sections
        assert "## THESIS" in prompt
        assert "## ANTITHESIS" in prompt
        assert "## SYNTHESIS" in prompt

    def test_synthesis_only_style_unchanged(self):
        """Test that synthesis_only style still works as before."""
        prompt = create_single_shot_dialectic_prompt(
            query="Test query for synthesis only style", response_style="synthesis_only"
        )

        # Should only include synthesis
        assert "Return ONLY the SYNTHESIS as 2-3 tight paragraphs" in prompt
        assert "Do not include thesis, antithesis, headings, or lists" in prompt

    def test_invalid_response_style(self):
        """Test that invalid response style uses default formatting."""
        # The function doesn't raise an error for invalid styles,
        # it falls back to default formatting
        prompt = create_single_shot_dialectic_prompt(
            query="Test query", response_style="invalid_style"
        )
        # Should include the query
        assert "Test query" in prompt
        # Should have default formatting
        assert "## THESIS" in prompt

    @pytest.mark.parametrize(
        "style",
        ["conversational", "bullet_points", "json", "sections", "synthesis_only"],
    )
    def test_all_styles_include_core_content(self, style):
        """Test that all styles include the core query content."""
        prompt = create_single_shot_dialectic_prompt(
            query="Test query with specific content: 12345", response_style=style
        )

        # All prompts should include the input content
        assert "Test query with specific content: 12345" in prompt

    def test_conversational_style_transitions(self):
        """Test conversational style includes natural transitions."""
        prompt = create_single_shot_dialectic_prompt(
            query="Query about complex topic", response_style="conversational"
        )

        # Should include natural transitions
        assert "thoughtful colleague" in prompt
        assert "Avoid rigid headings" in prompt
        assert "natural transitions" in prompt

    def test_bullet_points_style_conciseness(self):
        """Test bullet_points style emphasizes conciseness."""
        prompt = create_single_shot_dialectic_prompt(
            query="Query about detailed analysis", response_style="bullet_points"
        )

        # Should emphasize clarity and brevity
        assert "concise" in prompt
        assert "brief and scannable" in prompt
        # Should include bullet structure
        assert "**Thesis**:" in prompt
        assert "**Antithesis**:" in prompt
        assert "**Synthesis**:" in prompt


if __name__ == "__main__":
    pytest.main([__file__])
