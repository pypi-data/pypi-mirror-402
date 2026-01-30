"""State management for dialectical autocoding sessions.

This module provides stateless state management for the coach-player
autocoding loop based on the g3 paper's adversarial cooperation paradigm.
State is passed explicitly between tool calls to maintain fresh context each turn.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from hegelion.core.constants import AutocodingPhase, AutocodingStatus


@dataclass
class AutocodingState:
    """State for a dialectical autocoding session.

    This state is passed explicitly between tool calls, enabling fresh
    context each turn while maintaining session continuity.

    Attributes:
        session_id: Unique identifier for this autocoding session.
        session_name: Optional human-readable session label.
        requirements: The requirements document (source of truth).
        current_turn: Current turn number (0-indexed).
        max_turns: Maximum turns before timeout.
        phase: Current phase - init | player | coach | approved | timeout.
        status: Session status - active | approved | rejected | timeout.
        turn_history: List of turn records with feedback and scores.
        last_coach_feedback: Most recent coach feedback for player context.
        quality_scores: List of compliance scores from each coach turn.
        approval_threshold: Minimum score threshold for approval (0-1).
    """

    session_id: str
    requirements: str
    session_name: Optional[str] = None
    current_turn: int = 0
    max_turns: int = 10
    phase: str = AutocodingPhase.INIT.value
    status: str = AutocodingStatus.ACTIVE.value
    turn_history: List[Dict[str, Any]] = field(default_factory=list)
    last_coach_feedback: Optional[str] = None
    quality_scores: List[float] = field(default_factory=list)
    approval_threshold: float = 0.9

    def __post_init__(self) -> None:
        """Validate state after initialization."""
        valid_phases = AutocodingPhase.values()
        valid_statuses = AutocodingStatus.values()

        if self.phase not in valid_phases:
            raise ValueError(f"Invalid phase: {self.phase}. Must be one of {valid_phases}")
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {valid_statuses}")
        if not 0 <= self.approval_threshold <= 1:
            raise ValueError(f"approval_threshold must be 0-1, got {self.approval_threshold}")

    @classmethod
    def create(
        cls,
        requirements: str,
        max_turns: int = 10,
        approval_threshold: float = 0.9,
        session_name: Optional[str] = None,
    ) -> "AutocodingState":
        """Create a new autocoding session.

        Args:
            requirements: The requirements document (source of truth).
            max_turns: Maximum turns before timeout.
            approval_threshold: Minimum score threshold for approval.
            session_name: Optional human-readable session label.

        Returns:
            A new AutocodingState ready for the first player turn.
        """
        return cls(
            session_id=str(uuid.uuid4()),
            session_name=session_name,
            requirements=requirements,
            max_turns=max_turns,
            approval_threshold=approval_threshold,
            phase=AutocodingPhase.PLAYER.value,  # Start with player phase
            status=AutocodingStatus.ACTIVE.value,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to a dictionary for MCP transport.

        Returns:
            Dictionary representation of the state.
        """
        return {
            "schema_version": 1,
            "session_id": self.session_id,
            "session_name": self.session_name,
            "requirements": self.requirements,
            "current_turn": self.current_turn,
            "max_turns": self.max_turns,
            "phase": self.phase,
            "status": self.status,
            "turn_history": self.turn_history,
            "last_coach_feedback": self.last_coach_feedback,
            "quality_scores": self.quality_scores,
            "approval_threshold": self.approval_threshold,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutocodingState":
        """Deserialize state from a dictionary.

        Args:
            data: Dictionary representation of the state.

        Returns:
            Reconstructed AutocodingState.
        """
        return cls(
            session_id=data["session_id"],
            session_name=data.get("session_name"),
            requirements=data["requirements"],
            current_turn=data.get("current_turn", 0),
            max_turns=data.get("max_turns", 10),
            phase=data.get("phase", AutocodingPhase.INIT.value),
            status=data.get("status", AutocodingStatus.ACTIVE.value),
            turn_history=data.get("turn_history", []),
            last_coach_feedback=data.get("last_coach_feedback"),
            quality_scores=data.get("quality_scores", []),
            approval_threshold=data.get("approval_threshold", 0.9),
        )

    def advance_to_coach(self) -> "AutocodingState":
        """Advance state from player phase to coach phase.

        Returns:
            New state with coach phase active.

        Raises:
            ValueError: If not in player phase or session not active.
        """
        if self.phase != AutocodingPhase.PLAYER.value:
            raise ValueError(f"Cannot advance to coach from phase: {self.phase}")
        if self.status != AutocodingStatus.ACTIVE.value:
            raise ValueError(f"Cannot advance: session status is {self.status}")

        return AutocodingState(
            session_id=self.session_id,
            session_name=self.session_name,
            requirements=self.requirements,
            current_turn=self.current_turn,
            max_turns=self.max_turns,
            phase=AutocodingPhase.COACH.value,
            status=AutocodingStatus.ACTIVE.value,
            turn_history=self.turn_history.copy(),
            last_coach_feedback=self.last_coach_feedback,
            quality_scores=self.quality_scores.copy(),
            approval_threshold=self.approval_threshold,
        )

    def advance_turn(
        self,
        coach_feedback: str,
        approved: bool,
        compliance_score: Optional[float] = None,
    ) -> "AutocodingState":
        """Advance state after coach review.

        Args:
            coach_feedback: Feedback from the coach agent.
            approved: Whether the coach approved the implementation.
            compliance_score: Optional compliance score (0-1).

        Returns:
            New state with updated turn, feedback, and status.
        """
        if self.phase != AutocodingPhase.COACH.value:
            raise ValueError(f"Cannot advance turn from phase: {self.phase}")

        new_turn = self.current_turn + 1
        new_history = self.turn_history.copy()
        new_scores = self.quality_scores.copy()

        # Record turn history
        turn_record = {
            "turn": self.current_turn,
            "feedback": coach_feedback,
            "approved": approved,
            "score": compliance_score,
        }
        new_history.append(turn_record)

        if compliance_score is not None:
            new_scores.append(compliance_score)

        # Determine next phase and status
        if approved:
            new_phase = AutocodingPhase.APPROVED.value
            new_status = AutocodingStatus.APPROVED.value
        elif new_turn >= self.max_turns:
            new_phase = AutocodingPhase.TIMEOUT.value
            new_status = AutocodingStatus.TIMEOUT.value
        else:
            new_phase = AutocodingPhase.PLAYER.value
            new_status = AutocodingStatus.ACTIVE.value

        return AutocodingState(
            session_id=self.session_id,
            session_name=self.session_name,
            requirements=self.requirements,
            current_turn=new_turn,
            max_turns=self.max_turns,
            phase=new_phase,
            status=new_status,
            turn_history=new_history,
            last_coach_feedback=coach_feedback,
            quality_scores=new_scores,
            approval_threshold=self.approval_threshold,
        )

    def is_complete(self) -> bool:
        """Check if the session has completed (approved or timeout).

        Returns:
            True if session is no longer active.
        """
        return self.status in {
            AutocodingStatus.APPROVED.value,
            AutocodingStatus.REJECTED.value,
            AutocodingStatus.TIMEOUT.value,
        }

    def turns_remaining(self) -> int:
        """Get the number of turns remaining.

        Returns:
            Number of turns left before timeout.
        """
        return max(0, self.max_turns - self.current_turn)

    def average_score(self) -> Optional[float]:
        """Calculate average compliance score across turns.

        Returns:
            Average score, or None if no scores recorded.
        """
        if not self.quality_scores:
            return None
        return sum(self.quality_scores) / len(self.quality_scores)

    def summary(self) -> str:
        """Generate a human-readable summary of session state.

        Returns:
            Summary string for display.
        """
        avg_score = self.average_score()
        score_str = f"{avg_score:.1%}" if avg_score is not None else "N/A"
        if self.session_name:
            session_label = f"{self.session_name} ({self.session_id[:8]}...)"
        else:
            session_label = f"{self.session_id[:8]}..."

        return (
            f"Session: {session_label}\n"
            f"Turn: {self.current_turn + 1}/{self.max_turns}\n"
            f"Phase: {self.phase}\n"
            f"Status: {self.status}\n"
            f"Avg Score: {score_str}"
        )


def save_session(state: AutocodingState, filepath: str) -> None:
    """Save an autocoding session to a JSON file.

    Args:
        state: The AutocodingState to save.
        filepath: Path to save the session JSON file.
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, indent=2)


def load_session(filepath: str) -> AutocodingState:
    """Load an autocoding session from a JSON file.

    Args:
        filepath: Path to the session JSON file to load.

    Returns:
        Reconstructed AutocodingState.

    Raises:
        FileNotFoundError: If the session file doesn't exist.
        json.JSONDecodeError: If the file is not valid JSON.
        ValueError: If the JSON doesn't contain valid session data.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Session file not found: {filepath}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return AutocodingState.from_dict(data)
