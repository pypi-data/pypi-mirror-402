"""Prompt-driven dialectical reasoning for any LLM via MCP.

This module provides a way to run dialectical reasoning without making external API calls.
Instead, it returns structured prompts that guide the calling LLM through the process.
Perfect for Cursor, Claude Desktop, ChatGPT/Codex, or any MCP-compatible environment.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from hegelion.core.constants import DialecticPhase


@dataclass
class DialecticalPrompt:
    """A structured prompt for dialectical reasoning."""

    phase: str
    prompt: str
    instructions: str
    expected_format: str

    def to_dict(self) -> Dict[str, str]:
        """Serialize prompt to dictionary."""
        return {
            "phase": self.phase,
            "prompt": self.prompt,
            "instructions": self.instructions,
            "expected_format": self.expected_format,
        }


def _json_output_instructions(phase: str) -> tuple[str, str]:
    """Return JSON-only output instructions and expected format for a given phase."""
    if phase == DialecticPhase.THESIS.value:
        schema = """{
  "phase": "thesis",
  "thesis": "...",
  "assumptions": ["..."],
  "uncertainties": ["..."]
}"""
        expected = "JSON object with phase, thesis, assumptions, uncertainties"
    elif phase == DialecticPhase.ANTITHESIS.value or phase.startswith("council_"):
        schema = f"""{{
  "phase": "{phase}",
  "antithesis": "...",
  "contradictions": [
    {{"description": "...", "evidence": "..."}}
  ]
}}"""
        expected = "JSON object with phase, antithesis, contradictions"
    elif phase == DialecticPhase.SYNTHESIS.value:
        schema = """{
  "phase": "synthesis",
  "synthesis": "...",
  "research_proposals": [
    {"proposal": "...", "testable_prediction": "..."}
  ]
}"""
        expected = "JSON object with phase, synthesis, research_proposals"
    elif phase == DialecticPhase.JUDGE.value:
        schema = """{
  "phase": "judge",
  "score": 0,
  "critique_validity": true,
  "reasoning": "...",
  "strengths": "...",
  "improvements": "..."
}"""
        expected = "JSON object with score, critique_validity, reasoning, strengths, improvements"
    else:
        return "", ""

    instructions = f"""OUTPUT FORMAT (JSON ONLY):
Return ONLY a JSON object with this shape:
{schema}
No markdown, no commentary outside the JSON."""
    return instructions, expected


class PromptDrivenDialectic:
    """Orchestrates dialectical reasoning using prompts instead of API calls."""

    def __init__(self):
        self.conversation_state = {}

    def generate_thesis_prompt(
        self, query: str, response_style: str = "sections"
    ) -> DialecticalPrompt:
        """Generate a prompt for the thesis phase."""
        output_instructions = ""
        expected_format = "Free-form text thesis response"
        if response_style == "json":
            output_instructions, expected_format = _json_output_instructions("thesis")
            output_instructions = f"\n\n{output_instructions}"

        return DialecticalPrompt(
            phase=DialecticPhase.THESIS.value,
            prompt=f"""You are in the THESIS phase of Hegelian dialectical reasoning.

QUERY: {query}

Your task:
1. Provide a comprehensive, well-reasoned initial position on this query
2. Consider multiple perspectives and build a strong foundational argument
3. Be thorough but clear in your reasoning
4. Acknowledge uncertainty where appropriate
5. Think carefully before responding, then present a polished thesis
{output_instructions}

Generate your THESIS response now.""",
            instructions="Respond with a clear, well-structured thesis that establishes your initial position on the query.",
            expected_format=expected_format,
        )

    def generate_antithesis_prompt(
        self,
        query: str,
        thesis: str,
        use_search_context: bool = False,
        response_style: str = "sections",
    ) -> DialecticalPrompt:
        """Generate a prompt for the antithesis phase."""

        search_instruction = ""
        if use_search_context:
            search_instruction = """
IMPORTANT: Before critiquing, use available search tools to find current information about this topic. Ground your critique in real-world evidence and recent developments."""

        output_instructions = ""
        expected_format = "Text with embedded CONTRADICTION: and EVIDENCE: sections"
        if response_style == "json":
            output_instructions, expected_format = _json_output_instructions("antithesis")
            output_instructions = f"\n\n{output_instructions}"
            contradiction_instruction = (
                "Capture each issue in the JSON contradictions array with description and evidence."
            )
        else:
            contradiction_instruction = """For each significant problem you identify, use this EXACT format:
CONTRADICTION: [brief description]
EVIDENCE: [detailed explanation of why this is problematic]"""

        return DialecticalPrompt(
            phase=DialecticPhase.ANTITHESIS.value,
            prompt=f"""You are in the ANTITHESIS phase of Hegelian dialectical reasoning.

ORIGINAL QUERY: {query}

THESIS TO CRITIQUE: {thesis}
{search_instruction}

Your task as the critical voice:
1. Find contradictions, inconsistencies, or logical gaps in the thesis
2. Identify unexamined assumptions and hidden premises  
3. Propose alternative framings that challenge the thesis
4. Find edge cases or scenarios where the thesis breaks down
5. Be adversarial but intellectually honest

{contradiction_instruction}
{output_instructions}

Generate your ANTITHESIS critique now.""",
            instructions="Respond with a rigorous critique that identifies specific contradictions and weaknesses in the thesis.",
            expected_format=expected_format,
        )

    def generate_council_prompts(
        self, query: str, thesis: str, response_style: str = "sections"
    ) -> List[DialecticalPrompt]:
        """Generate prompts for multi-perspective council critique."""

        council_members = [
            {
                "name": "The Logician",
                "expertise": "Logical consistency and formal reasoning",
                "focus": "logical fallacies, internal contradictions, invalid inferences, missing premises",
            },
            {
                "name": "The Empiricist",
                "expertise": "Evidence, facts, and empirical grounding",
                "focus": "factual errors, unsupported claims, missing evidence, contradictions with established science",
            },
            {
                "name": "The Ethicist",
                "expertise": "Ethical implications and societal impact",
                "focus": "potential harm, ethical blind spots, fairness issues, unintended consequences",
            },
        ]

        prompts = []
        for member in council_members:
            output_instructions = ""
            expected_format = "Text with embedded CONTRADICTION: and EVIDENCE: sections"
            phase = f"council_{member['name'].lower().replace(' ', '_')}"
            if response_style == "json":
                output_instructions, expected_format = _json_output_instructions(phase)
                output_instructions = f"\n\n{output_instructions}"
                contradiction_instruction = "Capture each issue in the JSON contradictions array with description and evidence."
            else:
                contradiction_instruction = """For each issue you identify, use this format:
CONTRADICTION: [brief description]
EVIDENCE: [detailed explanation from your expert perspective]"""

            prompt = DialecticalPrompt(
                phase=phase,
                prompt=f"""You are {member["name"].upper()}, an expert in {member["expertise"]}.

ORIGINAL QUERY: {query}

THESIS TO CRITIQUE: {thesis}

Your expertise: {member["expertise"]}
Focus specifically on: {member["focus"]}

Examine the thesis from your specialized perspective and identify problems within your domain.

{contradiction_instruction}
{output_instructions}

Generate your specialized critique now.""",
                instructions=f"Respond as {member['name']} with critiques specific to {member['expertise']}",
                expected_format=expected_format,
            )
            prompts.append(prompt)

        return prompts

    def generate_synthesis_prompt(
        self,
        query: str,
        thesis: str,
        antithesis: str,
        contradictions: Optional[List[str]] = None,
        response_style: str = "sections",
    ) -> DialecticalPrompt:
        """Generate a prompt for the synthesis phase."""

        contradictions_text = ""
        if contradictions:
            contradictions_text = f"""

IDENTIFIED CONTRADICTIONS:
{chr(10).join(f"- {contradiction}" for contradiction in contradictions)}"""

        output_instructions = ""
        expected_format = "Text with optional RESEARCH_PROPOSAL: and TESTABLE_PREDICTION: sections"
        if response_style == "json":
            output_instructions, expected_format = _json_output_instructions("synthesis")
            output_instructions = f"\n\n{output_instructions}"
            research_instruction = "If the synthesis suggests new research, include it in the research_proposals array."
        else:
            research_instruction = """If the synthesis suggests new research, use this format:
RESEARCH_PROPOSAL: [brief description]
TESTABLE_PREDICTION: [specific falsifiable claim]"""

        return DialecticalPrompt(
            phase=DialecticPhase.SYNTHESIS.value,
            prompt=f"""You are in the SYNTHESIS phase of Hegelian dialectical reasoning.

ORIGINAL QUERY: {query}

THESIS: {thesis}

ANTITHESIS (critique): {antithesis}
{contradictions_text}

Your task:
1. Generate a SYNTHESIS that TRANSCENDS both thesis and antithesis
2. Resolve or reframe the contradictions by finding a higher-level perspective
3. Make predictions that NEITHER thesis nor antithesis would make alone
4. Ensure your synthesis is testable or falsifiable when possible
5. Propose research directions or experiments if appropriate

Requirements for a valid SYNTHESIS:
- Must not simply say "the thesis is right" or "the antithesis is right"
- Must not just say "both have merit" 
- Must offer a genuinely novel perspective
- Should be more sophisticated than either original position

{research_instruction}
{output_instructions}

Generate your SYNTHESIS now.""",
            instructions="Respond with a synthesis that transcends both positions and offers novel insights",
            expected_format=expected_format,
        )

    def generate_judge_prompt(
        self,
        query: str,
        thesis: str,
        antithesis: str,
        synthesis: str,
        response_style: str = "sections",
    ) -> DialecticalPrompt:
        """Generate a prompt for quality evaluation."""
        output_instructions = ""
        expected_format = "Structured response with SCORE:, CRITIQUE_VALIDITY:, REASONING:, STRENGTHS:, IMPROVEMENTS:"
        if response_style == "json":
            output_instructions, expected_format = _json_output_instructions("judge")
            output_instructions = f"\n\n{output_instructions}"
            format_instruction = ""
        else:
            format_instruction = """Respond with EXACTLY this format:
SCORE: [integer 0-10]
CRITIQUE_VALIDITY: [true/false]
REASONING: [detailed explanation]
STRENGTHS: [specific areas of excellence]
IMPROVEMENTS: [specific areas needing work]"""

        return DialecticalPrompt(
            phase=DialecticPhase.JUDGE.value,
            prompt=f"""You are the Iron Judge, evaluating dialectical reasoning quality.

ORIGINAL QUERY: {query}
THESIS: {thesis}
ANTITHESIS: {antithesis} 
SYNTHESIS: {synthesis}

Evaluate this dialectical process on:

1. **Thesis Quality** (0-2 points): Is the initial position well-reasoned?
2. **Antithesis Rigor** (0-3 points): Does the critique identify genuine problems?
3. **Synthesis Innovation** (0-3 points): Does the synthesis transcend both positions?
4. **Critique Validity** (0-2 points): Were critiques actually addressed?

Score criteria:
- 0-3: Poor quality, major logical flaws
- 4-5: Below average, some good elements but significant issues
- 6-7: Good quality, solid reasoning with minor gaps  
- 8-9: Excellent, sophisticated analysis with minimal flaws
- 10: Outstanding, exemplary dialectical reasoning

{format_instruction}{output_instructions}""",
            instructions="Evaluate the dialectical quality and provide structured feedback",
            expected_format=expected_format,
        )


def create_dialectical_workflow(
    query: str,
    use_search: bool = False,
    use_council: bool = False,
    use_judge: bool = False,
    response_style: str = "sections",
) -> Dict[str, Any]:
    """Create a complete dialectical workflow as structured prompts.

    Returns a workflow that can be executed by any LLM via MCP.
    """

    dialectic = PromptDrivenDialectic()
    workflow = {"query": query, "workflow_type": "prompt_driven_dialectic", "steps": []}

    # Step 1: Thesis
    workflow["steps"].append(
        {
            "step": 1,
            "name": "Generate Thesis",
            "prompt": dialectic.generate_thesis_prompt(
                query, response_style=response_style
            ).to_dict(),
        }
    )

    # Step 2: Antithesis (standard or council-based)
    if use_council:
        council_prompts = dialectic.generate_council_prompts(
            query, "{{thesis_from_step_1}}", response_style=response_style
        )
        antithesis_refs = []
        for i, council_prompt in enumerate(council_prompts):
            step_num = 2 + i
            workflow["steps"].append(
                {
                    "step": step_num,
                    "name": f"Council Critique: {council_prompt.phase}",
                    "prompt": council_prompt.to_dict(),
                }
            )
            antithesis_refs.append(
                f"### {council_prompt.phase.replace('_', ' ').title()}\n{{{{{council_prompt.phase}_from_step_{step_num}}}}}"
            )

        antithesis_step = 2 + len(council_prompts)
        antithesis_output_ref = "\n\n".join(antithesis_refs)
    else:
        workflow["steps"].append(
            {
                "step": 2,
                "name": "Generate Antithesis",
                "prompt": dialectic.generate_antithesis_prompt(
                    query,
                    "{{thesis_from_step_1}}",
                    use_search,
                    response_style=response_style,
                ).to_dict(),
            }
        )
        antithesis_step = 3
        antithesis_output_ref = "{{antithesis_from_step_2}}"

    # Step 3: Synthesis
    workflow["steps"].append(
        {
            "step": antithesis_step,
            "name": "Generate Synthesis",
            "prompt": dialectic.generate_synthesis_prompt(
                query,
                "{{thesis_from_step_1}}",
                antithesis_output_ref,
                response_style=response_style,
            ).to_dict(),
        }
    )

    # Step 4: Judge (optional)
    if use_judge:
        workflow["steps"].append(
            {
                "step": antithesis_step + 1,
                "name": "Evaluate Quality",
                "prompt": dialectic.generate_judge_prompt(
                    query,
                    "{{thesis_from_step_1}}",
                    antithesis_output_ref,
                    f"{{synthesis_from_step_{antithesis_step}}}",
                    response_style=response_style,
                ).to_dict(),
            }
        )

    workflow["instructions"] = {
        "execution_mode": "sequential",
        "description": "Execute each step in order, using outputs from previous steps as inputs to later steps",
        "variable_substitution": "Replace {{variable_name}} with actual outputs from previous steps",
        "final_output": "Combine all outputs into a structured HegelionResult",
    }

    return workflow


def create_single_shot_dialectic_prompt(
    query: str,
    use_search: bool = False,
    use_council: bool = False,
    response_style: str = "sections",
) -> str:
    """Create a single comprehensive prompt for dialectical reasoning.

    This is for models that can handle complex multi-step reasoning in one go.
    """

    search_instruction = ""
    if use_search:
        search_instruction = """
Before beginning, use available search tools to gather current information about this topic."""

    council_instruction = ""
    if use_council:
        council_instruction = """
For the ANTITHESIS phase, adopt three distinct critical perspectives:
- THE LOGICIAN: Focus on logical consistency and formal reasoning
- THE EMPIRICIST: Focus on evidence, facts, and empirical grounding  
- THE ETHICIST: Focus on ethical implications and societal impact

Generate critiques from each perspective, then synthesize them."""

    antithesis_format_instruction = """For each problem, use:
CONTRADICTION: [description]
EVIDENCE: [explanation]"""
    research_instruction = """If the synthesis suggests new research, use this format:
RESEARCH_PROPOSAL: [description]  
TESTABLE_PREDICTION: [falsifiable claim]"""
    output_visibility_note = ""
    if response_style == "json":
        antithesis_format_instruction = (
            "Capture contradictions as JSON objects with description and evidence."
        )
        research_instruction = (
            "If the synthesis suggests new research, include it in the research_proposals array."
        )
        output_instructions = f"""Return ONLY a JSON object with this shape:
{{
  "query": "{query}",
  "thesis": "...",
  "antithesis": "...",
  "synthesis": "...",
  "contradictions": [
    {{"description": "...", "evidence": "..."}}
  ],
  "research_proposals": [
    {{"proposal": "...", "testable_prediction": "..."}}
  ]
}}
No markdown, no commentary outside the JSON."""
    elif response_style == "synthesis_only":
        antithesis_format_instruction = (
            "Identify contradictions and evidence during antithesis (keep these internal)."
        )
        research_instruction = (
            "If research directions emerge, weave them into the synthesis without labels."
        )
        output_visibility_note = (
            "Perform the thesis and antithesis internally; only output the synthesis."
        )
        output_instructions = """Return ONLY the SYNTHESIS as 2-3 tight paragraphs. Do not include thesis, antithesis, headings, or lists."""
    elif response_style == "conversational":
        output_instructions = """Adopt a natural, conversational tone. Present the dialectical analysis as if you are a thoughtful colleague explaining your reasoning.
        
Structure:
1. Start with your initial thoughts (Thesis)
2. Then, "but on the other hand..." (Antithesis)
3. Finally, "so perhaps the best way forward is..." (Synthesis)

Avoid rigid headings like ## THESIS. Use natural transitions."""
    elif response_style == "bullet_points":
        output_instructions = """Format the response as a concise set of bullet points.

*   **Thesis**: [Key point]
*   **Antithesis**: [Key counter-point]
*   **Synthesis**: [Resolution]

Keep it brief and scannable."""
    else:
        output_instructions = f"""Structure your complete response as:

# DIALECTICAL ANALYSIS: {query}

## THESIS
[Your initial position]

## ANTITHESIS  
[Your critical examination]

## SYNTHESIS
[Your transcendent resolution]

## CONTRADICTIONS IDENTIFIED
1. [Contradiction 1]: [Evidence]
2. [Contradiction 2]: [Evidence]

## RESEARCH PROPOSALS
1. [Proposal 1]: [Testable prediction]"""

    return f"""You will now perform Hegelian dialectical reasoning on the following query using a three-phase process: THESIS → ANTITHESIS → SYNTHESIS.
{search_instruction}
{output_visibility_note}

QUERY: {query}

Execute the following phases:

**PHASE 1 - THESIS:**
Generate a comprehensive initial position on the query. Be thorough, well-reasoned, and consider multiple perspectives while establishing your foundational argument.

**PHASE 2 - ANTITHESIS:**{council_instruction}
Critically examine your thesis. Find contradictions, logical gaps, unexamined assumptions, and alternative framings.
{antithesis_format_instruction}

**PHASE 3 - SYNTHESIS:**
Transcend both thesis and antithesis with a novel perspective that resolves the contradictions. Make predictions neither position would make alone. Include research proposals if appropriate:
{research_instruction}

{output_instructions}

Begin your dialectical analysis now."""
