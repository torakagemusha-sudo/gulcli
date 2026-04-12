"""
Decision Types - GUL v2.1

4-valued decision logic with combination semantics.
Extends traditional binary allow/deny with defer and abstain.

Mathematical Foundation:
    - Decision forms a partial order: abstain < defer < {permit, deny}
    - Deny dominates permit in combination
    - Defer propagates uncertainty
    - Abstain is the identity element
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .confidence import Confidence
    from .jurisdiction import JurisdictionId


class Decision(Enum):
    """
    4-valued decision from GUL.lean.

    Values:
        PERMIT: Allow the action (positive authorization)
        DENY: Block the action (negative authorization)
        DEFER: Uncertain, defer to higher authority
        ABSTAIN: No opinion (neutral/out-of-scope)

    Semantics:
        - PERMIT and DENY are terminal decisions
        - DEFER indicates insufficient confidence to decide
        - ABSTAIN indicates the decision is not applicable
    """

    PERMIT = "permit"
    DENY = "deny"
    DEFER = "defer"
    ABSTAIN = "abstain"

    def is_terminal(self) -> bool:
        """Check if decision is terminal (permit or deny)."""
        return self in (Decision.PERMIT, Decision.DENY)

    def is_positive(self) -> bool:
        """Check if decision authorizes action."""
        return self == Decision.PERMIT

    def is_negative(self) -> bool:
        """Check if decision blocks action."""
        return self == Decision.DENY

    def __repr__(self) -> str:
        return f"Decision.{self.name}"


@dataclass
class EvaluatedDecision:
    """
    Decision with confidence and evidence.

    Represents a complete decision outcome including:
    - The decision value (permit/deny/defer/abstain)
    - Confidence level in the decision
    - Evidence trail supporting the decision
    - Optional jurisdiction scope

    Attributes:
        decision: The 4-valued decision
        confidence: Confidence level in [0,1]
        evidence: List of evidence strings
        jurisdiction: Optional jurisdiction scope
    """

    decision: Decision
    confidence: "Confidence"
    evidence: list[str] = field(default_factory=list)
    jurisdiction: Optional["JurisdictionId"] = None

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if decision has high confidence."""
        return self.confidence.value >= threshold

    def should_defer(self, min_confidence: float = 0.5) -> bool:
        """Check if decision should be deferred due to low confidence."""
        return (
            self.decision == Decision.DEFER
            or self.confidence.value < min_confidence
        )

    def with_evidence(self, *new_evidence: str) -> "EvaluatedDecision":
        """Return new decision with additional evidence."""
        return EvaluatedDecision(
            decision=self.decision,
            confidence=self.confidence,
            evidence=self.evidence + list(new_evidence),
            jurisdiction=self.jurisdiction,
        )

    def __repr__(self) -> str:
        return (
            f"EvaluatedDecision({self.decision.name}, "
            f"conf={self.confidence.value:.3f}, "
            f"evidence={len(self.evidence)})"
        )


class DecisionCombiner:
    """
    Combination logic from GUL.lean.

    Implements decision combination semantics:
    - Deny dominates all other decisions
    - Permit requires both parties to permit
    - Defer propagates uncertainty
    - Abstain is the identity element
    """

    @staticmethod
    def combine(d1: Decision, d2: Decision) -> Decision:
        """
        Combine two decisions using GUL semantics.

        Priority order:
        1. Deny dominates (either deny -> deny)
        2. Permit requires both (both permit -> permit)
        3. Defer propagates (either defer -> defer)
        4. Abstain is identity (abstain + x -> x)

        Args:
            d1: First decision
            d2: Second decision

        Returns:
            Combined decision
        """
        # Deny dominates
        if d1 == Decision.DENY or d2 == Decision.DENY:
            return Decision.DENY

        # Permit requires both
        if d1 == Decision.PERMIT and d2 == Decision.PERMIT:
            return Decision.PERMIT

        # Defer propagates
        if d1 == Decision.DEFER or d2 == Decision.DEFER:
            return Decision.DEFER

        # Abstain is identity
        if d1 == Decision.ABSTAIN:
            return d2
        if d2 == Decision.ABSTAIN:
            return d1

        # Default to defer for safety
        return Decision.DEFER

    @staticmethod
    def combine_all(decisions: list[Decision]) -> Decision:
        """
        Combine multiple decisions.

        Args:
            decisions: List of decisions to combine

        Returns:
            Combined decision
        """
        if not decisions:
            return Decision.ABSTAIN

        result = decisions[0]
        for d in decisions[1:]:
            result = DecisionCombiner.combine(result, d)
        return result

    @staticmethod
    def override(base: Decision, override: Decision) -> Decision:
        """
        Override base decision with authority decision.

        Unlike combine, override gives priority to the override decision
        unless it's ABSTAIN (indicating no override).

        Args:
            base: Base decision
            override: Authority override

        Returns:
            Final decision
        """
        if override == Decision.ABSTAIN:
            return base
        return override

    @staticmethod
    def invert(d: Decision) -> Decision:
        """
        Invert a decision.

        PERMIT <-> DENY, DEFER and ABSTAIN unchanged.

        Args:
            d: Decision to invert

        Returns:
            Inverted decision
        """
        if d == Decision.PERMIT:
            return Decision.DENY
        if d == Decision.DENY:
            return Decision.PERMIT
        return d
