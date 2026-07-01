"""
GUL Inference Engine - GUL v2.1

Formal inference rules for policy evaluation.
Implements logical combination of evaluated decisions.

Mathematical Foundation:
    - AND/OR rules follow 4-valued logic semantics
    - Confidence propagation tracks uncertainty
    - Evidence chains support audit trails
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from .confidence import Confidence, ConfidenceOps
from .decision import Decision, DecisionCombiner, EvaluatedDecision
from .jurisdiction import JurisdictionId


@dataclass
class InferenceTrace:
    """
    Trace of inference steps for audit.

    Records the reasoning chain that led to a decision.

    Attributes:
        rule: Name of inference rule applied
        inputs: Input decisions
        output: Resulting decision
        metadata: Additional context
    """

    rule: str
    inputs: list[EvaluatedDecision]
    output: EvaluatedDecision
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "rule": self.rule,
            "inputs": [
                {"decision": d.decision.value, "confidence": d.confidence.value}
                for d in self.inputs
            ],
            "output": {
                "decision": self.output.decision.value,
                "confidence": self.output.confidence.value,
            },
            "metadata": self.metadata,
        }


class GULInferenceEngine:
    """
    Inference rules from Inference.lean.

    Provides formal inference operations for combining
    evaluated decisions under different logical semantics.

    Usage:
        >>> engine = GULInferenceEngine()
        >>> d1 = EvaluatedDecision(Decision.PERMIT, Confidence(0.9))
        >>> d2 = EvaluatedDecision(Decision.PERMIT, Confidence(0.8))
        >>> result = engine.evaluate_and(d1, d2)
        >>> result.decision
        Decision.PERMIT
        >>> result.confidence.value
        0.8
    """

    def __init__(self):
        self.trace: list[InferenceTrace] = []
        self._trace_enabled = True

    def enable_trace(self, enabled: bool = True):
        """Enable or disable inference tracing."""
        self._trace_enabled = enabled

    def clear_trace(self):
        """Clear inference trace."""
        self.trace.clear()

    def _record_trace(
        self,
        rule: str,
        inputs: list[EvaluatedDecision],
        output: EvaluatedDecision,
        **metadata,
    ):
        """Record inference step if tracing enabled."""
        if self._trace_enabled:
            self.trace.append(
                InferenceTrace(
                    rule=rule,
                    inputs=inputs,
                    output=output,
                    metadata=metadata,
                )
            )

    def evaluate_and(
        self,
        d1: EvaluatedDecision,
        d2: EvaluatedDecision,
    ) -> EvaluatedDecision:
        """
        AND rule: both permit → min confidence; either deny → deny.

        Logic:
        - If either is DENY, result is DENY with max confidence
        - If both are PERMIT, result is PERMIT with min confidence
        - Otherwise, result is DEFER

        Args:
            d1: First evaluated decision
            d2: Second evaluated decision

        Returns:
            Combined decision under AND semantics
        """
        combined_evidence = d1.evidence + d2.evidence

        if d1.decision == Decision.DENY or d2.decision == Decision.DENY:
            # Deny with maximum confidence (most certain about denial)
            conf = ConfidenceOps.combine_union(d1.confidence, d2.confidence)
            result = EvaluatedDecision(
                Decision.DENY,
                conf,
                combined_evidence,
            )
        elif d1.decision == Decision.PERMIT and d2.decision == Decision.PERMIT:
            # Permit with minimum confidence (weakest link)
            conf = ConfidenceOps.combine_intersection(d1.confidence, d2.confidence)
            result = EvaluatedDecision(
                Decision.PERMIT,
                conf,
                combined_evidence,
            )
        else:
            # One defers or abstains
            conf = ConfidenceOps.combine_intersection(d1.confidence, d2.confidence)
            result = EvaluatedDecision(
                Decision.DEFER,
                conf,
                combined_evidence,
            )

        self._record_trace("AND", [d1, d2], result)
        return result

    def evaluate_or(
        self,
        d1: EvaluatedDecision,
        d2: EvaluatedDecision,
    ) -> EvaluatedDecision:
        """
        OR rule: either permit → permit; both deny → deny.

        Logic:
        - If either is PERMIT, result is PERMIT with max confidence
        - If both are DENY, result is DENY with min confidence
        - Otherwise, result is DEFER

        Args:
            d1: First evaluated decision
            d2: Second evaluated decision

        Returns:
            Combined decision under OR semantics
        """
        combined_evidence = d1.evidence + d2.evidence

        if d1.decision == Decision.PERMIT or d2.decision == Decision.PERMIT:
            # Permit with maximum confidence
            conf = ConfidenceOps.combine_union(d1.confidence, d2.confidence)
            result = EvaluatedDecision(
                Decision.PERMIT,
                conf,
                combined_evidence,
            )
        elif d1.decision == Decision.DENY and d2.decision == Decision.DENY:
            # Deny with minimum confidence
            conf = ConfidenceOps.combine_intersection(d1.confidence, d2.confidence)
            result = EvaluatedDecision(
                Decision.DENY,
                conf,
                combined_evidence,
            )
        else:
            # Uncertainty
            conf = ConfidenceOps.combine_intersection(d1.confidence, d2.confidence)
            result = EvaluatedDecision(
                Decision.DEFER,
                conf,
                combined_evidence,
            )

        self._record_trace("OR", [d1, d2], result)
        return result

    def evaluate_sequential(
        self,
        d1: EvaluatedDecision,
        d2: EvaluatedDecision,
    ) -> EvaluatedDecision:
        """
        Sequential: chain of reasoning with product confidence.

        Models dependent reasoning where d2 depends on d1.
        Confidence compounds through multiplication.

        Args:
            d1: First (prerequisite) decision
            d2: Second (dependent) decision

        Returns:
            Combined decision with sequential semantics
        """
        decision = DecisionCombiner.combine(d1.decision, d2.decision)
        conf = ConfidenceOps.combine_sequential(d1.confidence, d2.confidence)
        combined_evidence = d1.evidence + d2.evidence

        result = EvaluatedDecision(decision, conf, combined_evidence)
        self._record_trace("SEQ", [d1, d2], result)
        return result

    def evaluate_parallel(
        self,
        d1: EvaluatedDecision,
        d2: EvaluatedDecision,
    ) -> EvaluatedDecision:
        """
        Parallel: independent evidence with parallel confidence.

        Models independent reasoning paths that reinforce each other.

        Args:
            d1: First independent decision
            d2: Second independent decision

        Returns:
            Combined decision with parallel semantics
        """
        decision = DecisionCombiner.combine(d1.decision, d2.decision)
        conf = ConfidenceOps.combine_parallel(d1.confidence, d2.confidence)
        combined_evidence = d1.evidence + d2.evidence

        result = EvaluatedDecision(decision, conf, combined_evidence)
        self._record_trace("PAR", [d1, d2], result)
        return result

    def evaluate_not(self, d: EvaluatedDecision) -> EvaluatedDecision:
        """
        NOT rule: invert decision, preserve confidence.

        PERMIT <-> DENY, DEFER and ABSTAIN unchanged.

        Args:
            d: Decision to negate

        Returns:
            Negated decision
        """
        inverted = DecisionCombiner.invert(d.decision)
        result = EvaluatedDecision(
            inverted,
            d.confidence,
            d.evidence + [f"NOT({d.decision.value})"],
        )
        self._record_trace("NOT", [d], result)
        return result

    def evaluate_conditional(
        self,
        condition: EvaluatedDecision,
        then_branch: EvaluatedDecision,
        else_branch: EvaluatedDecision,
    ) -> EvaluatedDecision:
        """
        Conditional: if-then-else with confidence propagation.

        Args:
            condition: Condition to evaluate
            then_branch: Result if condition permits
            else_branch: Result if condition denies

        Returns:
            Branch result with combined confidence
        """
        if condition.decision == Decision.PERMIT:
            conf = ConfidenceOps.combine_sequential(
                condition.confidence, then_branch.confidence
            )
            result = EvaluatedDecision(
                then_branch.decision,
                conf,
                condition.evidence + then_branch.evidence,
            )
        elif condition.decision == Decision.DENY:
            conf = ConfidenceOps.combine_sequential(
                condition.confidence, else_branch.confidence
            )
            result = EvaluatedDecision(
                else_branch.decision,
                conf,
                condition.evidence + else_branch.evidence,
            )
        else:
            # Condition uncertain - defer
            conf = condition.confidence
            result = EvaluatedDecision(
                Decision.DEFER,
                conf,
                condition.evidence + ["condition uncertain"],
            )

        self._record_trace(
            "IF-THEN-ELSE",
            [condition, then_branch, else_branch],
            result,
        )
        return result

    def evaluate_threshold(
        self,
        d: EvaluatedDecision,
        threshold: float,
    ) -> EvaluatedDecision:
        """
        Threshold rule: require minimum confidence for terminal decision.

        If confidence is below threshold, convert to DEFER.

        Args:
            d: Decision to check
            threshold: Minimum required confidence

        Returns:
            Original decision if confident enough, else DEFER
        """
        if d.confidence.value >= threshold:
            result = d
        else:
            result = EvaluatedDecision(
                Decision.DEFER,
                d.confidence,
                d.evidence + [f"below threshold {threshold}"],
            )

        self._record_trace("THRESHOLD", [d], result, threshold=threshold)
        return result

    def evaluate_jurisdiction_check(
        self,
        d: EvaluatedDecision,
        request_jurisdiction: Optional[JurisdictionId],
        policy_jurisdiction: Optional[JurisdictionId],
    ) -> EvaluatedDecision:
        """
        Jurisdiction check: verify authority scope.

        If request is outside policy jurisdiction, ABSTAIN.

        Args:
            d: Decision to scope
            request_jurisdiction: Jurisdiction of request
            policy_jurisdiction: Jurisdiction of policy

        Returns:
            Decision if in scope, ABSTAIN otherwise
        """
        if policy_jurisdiction is None:
            # No jurisdiction constraint
            return d

        if request_jurisdiction is None:
            # No request jurisdiction - assume in scope
            return d

        if request_jurisdiction.is_sub_jurisdiction(policy_jurisdiction):
            return d

        # Out of scope
        result = EvaluatedDecision(
            Decision.ABSTAIN,
            Confidence.one(),
            d.evidence + ["out of jurisdiction"],
            jurisdiction=policy_jurisdiction,
        )
        self._record_trace("JURISDICTION", [d], result)
        return result

    def evaluate_always(self, d: EvaluatedDecision) -> EvaluatedDecision:
        """Structural ALWAYS approximation with temporal trace metadata."""
        result = EvaluatedDecision(
            d.decision,
            d.confidence,
            d.evidence + ["always: structural approximation"],
            jurisdiction=d.jurisdiction,
        )
        self._record_trace(
            "ALWAYS",
            [d],
            result,
            temporal="always",
            approximation="structural",
        )
        return result

    def evaluate_eventually(self, d: EvaluatedDecision) -> EvaluatedDecision:
        """Structural EVENTUALLY approximation with temporal trace metadata."""
        result = EvaluatedDecision(
            d.decision,
            d.confidence,
            d.evidence + ["eventually: structural approximation"],
            jurisdiction=d.jurisdiction,
        )
        self._record_trace(
            "EVENTUALLY",
            [d],
            result,
            temporal="eventually",
            approximation="structural",
        )
        return result

    def evaluate_until(
        self,
        d1: EvaluatedDecision,
        d2: EvaluatedDecision,
    ) -> EvaluatedDecision:
        """UNTIL composed as sequential approximation with temporal trace metadata."""
        out = self.evaluate_sequential(d1, d2)
        result = EvaluatedDecision(
            out.decision,
            out.confidence,
            out.evidence + ["until: sequential approximation"],
            jurisdiction=out.jurisdiction,
        )
        self._record_trace(
            "UNTIL",
            [d1, d2],
            result,
            temporal="until",
            approximation="sequential",
        )
        return result

    def evaluate_all(
        self,
        decisions: list[EvaluatedDecision],
        combiner: str = "and",
    ) -> EvaluatedDecision:
        """
        Evaluate multiple decisions with specified combiner.

        Args:
            decisions: List of decisions to combine
            combiner: One of 'and', 'or', 'sequential', 'parallel'

        Returns:
            Combined decision

        Raises:
            ValueError: If combiner is not recognized
        """
        combiner_map: dict[str, Callable] = {
            "and": self.evaluate_and,
            "or": self.evaluate_or,
            "sequential": self.evaluate_sequential,
            "parallel": self.evaluate_parallel,
        }

        if combiner not in combiner_map:
            raise ValueError(f"Unknown combiner: {combiner}")

        if not decisions:
            return EvaluatedDecision(Decision.ABSTAIN, Confidence.one())

        if len(decisions) == 1:
            return decisions[0]

        combine_fn = combiner_map[combiner]
        result = decisions[0]
        for d in decisions[1:]:
            result = combine_fn(result, d)

        return result

    def get_trace_summary(self) -> list[dict]:
        """Get serializable trace summary."""
        return [t.to_dict() for t in self.trace]
