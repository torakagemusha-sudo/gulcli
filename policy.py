"""
GUL Policy - GUL v2.1

Extended governance policy with 4-valued decisions and confidence.
Integrates with existing GovernancePolicy for backward compatibility.

Mathematical Foundation:
    - Policy evaluation produces EvaluatedDecision with confidence
    - Jurisdiction scoping limits policy applicability
    - Audit trails capture full inference history
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .confidence import Confidence
from .decision import Decision, EvaluatedDecision
from .inference import GULInferenceEngine
from .jurisdiction import Jurisdiction, JurisdictionId


@dataclass
class GULGovernanceDecision:
    """
    Extended decision with 4-valued logic and confidence.

    Provides full GUL semantics while maintaining backward
    compatibility with legacy GovernanceDecision.

    Attributes:
        decision: 4-valued decision (permit/deny/defer/abstain)
        confidence: Confidence level in [0,1]
        reason: Human-readable explanation
        evidence: List of evidence strings
        jurisdiction: Optional jurisdiction scope
        meta: Additional metadata
        timestamp: ISO timestamp of decision
        policy_version: Policy version identifier
        risk_score: Optional risk metric
        coherence_score: Optional coherence metric
    """

    decision: Decision
    confidence: Confidence
    reason: str = ""
    evidence: List[str] = field(default_factory=list)
    jurisdiction: Optional[JurisdictionId] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[str] = None
    policy_version: str = "2.1"
    risk_score: Optional[float] = None
    coherence_score: Optional[float] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    @property
    def ok(self) -> bool:
        """
        Backward compatibility with legacy GovernanceDecision.

        Returns True only if decision is PERMIT with sufficient confidence.
        """
        return self.decision == Decision.PERMIT and self.confidence.value >= 0.5

    def to_legacy(self) -> "GovernanceDecision":
        """
        Convert to legacy GovernanceDecision.

        Imports here to avoid circular dependency. Requires geodesic_ai.
        """
        try:
            from geodesic_ai.kernel.governance.policy import GovernanceDecision
        except ImportError as e:
            raise RuntimeError("geodesic_ai required for to_legacy()") from e

        return GovernanceDecision(
            ok=self.ok,
            reason=self.reason,
            meta=self.meta,
            timestamp=self.timestamp,
            policy_version=self.policy_version,
        )

    def to_evaluated(self) -> EvaluatedDecision:
        """Convert to EvaluatedDecision for inference."""
        return EvaluatedDecision(
            decision=self.decision,
            confidence=self.confidence,
            evidence=self.evidence,
            jurisdiction=self.jurisdiction,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "decision": self.decision.value,
            "confidence": self.confidence.value,
            "reason": self.reason,
            "evidence": self.evidence,
            "jurisdiction": (
                self.jurisdiction.fully_qualified_name()
                if self.jurisdiction
                else None
            ),
            "meta": self.meta,
            "timestamp": self.timestamp,
            "policy_version": self.policy_version,
            "risk_score": self.risk_score,
            "coherence_score": self.coherence_score,
            "ok": self.ok,  # Legacy compatibility
        }

    def with_evidence(self, *new_evidence: str) -> "GULGovernanceDecision":
        """Return new decision with additional evidence."""
        return GULGovernanceDecision(
            decision=self.decision,
            confidence=self.confidence,
            reason=self.reason,
            evidence=self.evidence + list(new_evidence),
            jurisdiction=self.jurisdiction,
            meta=self.meta,
            timestamp=self.timestamp,
            policy_version=self.policy_version,
            risk_score=self.risk_score,
            coherence_score=self.coherence_score,
        )

    def __repr__(self) -> str:
        return (
            f"GULGovernanceDecision({self.decision.name}, "
            f"conf={self.confidence.value:.3f}, "
            f"ok={self.ok})"
        )


class GULGovernancePolicy:
    """
    Extended governance policy with GUL semantics.

    Evaluates risk and coherence with 4-valued decisions,
    confidence tracking, and jurisdiction scoping.

    Usage:
        >>> policy = GULGovernancePolicy(max_risk=0.5, min_confidence=0.7)
        >>> decision = policy.evaluate(risk_score=0.3, coherence=0.8)
        >>> decision.ok
        True
        >>> decision.decision
        Decision.PERMIT
    """

    def __init__(
        self,
        max_risk: float = 1.0,
        min_coherence: float = 0.0,
        min_confidence: float = 0.5,
        jurisdiction: Optional[Jurisdiction] = None,
        db_manager=None,
        policy_name: str = "gul_default",
    ):
        """
        Initialize GUL governance policy.

        Args:
            max_risk: Maximum allowable risk score
            min_coherence: Minimum required coherence score
            min_confidence: Minimum confidence to avoid deferral
            jurisdiction: Policy jurisdiction scope
            db_manager: Optional DB manager for audit logging
            policy_name: Name identifier for this policy
        """
        self.max_risk = max_risk
        self.min_coherence = min_coherence
        self.min_confidence = min_confidence
        self.jurisdiction = jurisdiction
        self.db_manager = db_manager
        self.policy_name = policy_name
        self.decision_history: List[GULGovernanceDecision] = []
        self._decision_count = 0
        self._inference_engine = GULInferenceEngine()

    def evaluate(
        self,
        risk_score: float,
        coherence: float,
        confidence: Optional[Confidence] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> GULGovernanceDecision:
        """
        Evaluate risk and coherence, returning a GUL governance decision.

        Args:
            risk_score: Risk metric (lower is better)
            coherence: Coherence metric (higher is better)
            confidence: Optional confidence in inputs
            context: Optional additional context

        Returns:
            GULGovernanceDecision with full audit trail
        """
        self._decision_count += 1
        conf = confidence or Confidence.one()
        ctx = context or {}

        # Build metadata
        meta = {
            "max_risk": self.max_risk,
            "min_coherence": self.min_coherence,
            "min_confidence": self.min_confidence,
            "decision_number": self._decision_count,
            "policy_name": self.policy_name,
            "risk_score": risk_score,
            "coherence": coherence,
            **ctx,
        }

        evidence: List[str] = []

        # Check jurisdiction scope
        if self.jurisdiction and ctx.get("jurisdiction"):
            req_jurisdiction = ctx.get("jurisdiction")
            if isinstance(req_jurisdiction, JurisdictionId):
                if not req_jurisdiction.is_sub_jurisdiction(self.jurisdiction.id):
                    decision = GULGovernanceDecision(
                        decision=Decision.ABSTAIN,
                        confidence=Confidence.one(),
                        reason="out of jurisdiction",
                        evidence=["request jurisdiction outside policy scope"],
                        jurisdiction=self.jurisdiction.id if self.jurisdiction else None,
                        meta=meta,
                        risk_score=risk_score,
                        coherence_score=coherence,
                    )
                    self._record_decision(decision)
                    return decision

        # Check hard constraints: risk
        if risk_score > self.max_risk:
            evidence.append(f"risk {risk_score:.4f} > max {self.max_risk}")
            decision = GULGovernanceDecision(
                decision=Decision.DENY,
                confidence=Confidence.one(),
                reason=f"risk {risk_score:.4f} exceeds threshold {self.max_risk}",
                evidence=evidence,
                jurisdiction=self.jurisdiction.id if self.jurisdiction else None,
                meta=meta,
                risk_score=risk_score,
                coherence_score=coherence,
            )
            self._record_decision(decision)
            return decision

        # Check hard constraints: coherence
        if coherence < self.min_coherence:
            evidence.append(f"coherence {coherence:.4f} < min {self.min_coherence}")
            decision = GULGovernanceDecision(
                decision=Decision.DENY,
                confidence=Confidence.one(),
                reason=f"coherence {coherence:.4f} below threshold {self.min_coherence}",
                evidence=evidence,
                jurisdiction=self.jurisdiction.id if self.jurisdiction else None,
                meta=meta,
                risk_score=risk_score,
                coherence_score=coherence,
            )
            self._record_decision(decision)
            return decision

        # Check confidence threshold
        if conf.value < self.min_confidence:
            evidence.append(f"confidence {conf.value:.4f} < min {self.min_confidence}")
            decision = GULGovernanceDecision(
                decision=Decision.DEFER,
                confidence=conf,
                reason=f"confidence {conf.value:.4f} below threshold {self.min_confidence}",
                evidence=evidence,
                jurisdiction=self.jurisdiction.id if self.jurisdiction else None,
                meta=meta,
                risk_score=risk_score,
                coherence_score=coherence,
            )
            self._record_decision(decision)
            return decision

        # All checks passed
        evidence.append("all thresholds satisfied")
        decision = GULGovernanceDecision(
            decision=Decision.PERMIT,
            confidence=conf,
            reason="approved",
            evidence=evidence,
            jurisdiction=self.jurisdiction.id if self.jurisdiction else None,
            meta=meta,
            risk_score=risk_score,
            coherence_score=coherence,
        )
        self._record_decision(decision)
        return decision

    def evaluate_stats(
        self,
        stats: Dict[str, float],
        context: Optional[Dict[str, Any]] = None,
    ) -> GULGovernanceDecision:
        """Evaluate from a statistics dictionary."""
        risk = float(stats.get("risk", 0.0))
        coherence = float(stats.get("coherence", 1.0))
        confidence = stats.get("confidence")
        conf = Confidence(confidence) if confidence is not None else None
        return self.evaluate(risk, coherence, conf, context)

    def evaluate_with_inference(
        self,
        decisions: List[EvaluatedDecision],
        combiner: str = "and",
        context: Optional[Dict[str, Any]] = None,
    ) -> GULGovernanceDecision:
        """
        Evaluate multiple sub-decisions using inference engine.

        Args:
            decisions: List of evaluated decisions to combine
            combiner: Combination method ('and', 'or', 'sequential', 'parallel')
            context: Optional context

        Returns:
            Combined GUL governance decision
        """
        self._decision_count += 1

        if not decisions:
            return GULGovernanceDecision(
                decision=Decision.ABSTAIN,
                confidence=Confidence.one(),
                reason="no decisions to evaluate",
            )

        result = self._inference_engine.evaluate_all(decisions, combiner)
        trace = self._inference_engine.get_trace_summary()

        meta = {
            "inference_trace": trace,
            "combiner": combiner,
            "num_inputs": len(decisions),
            "decision_number": self._decision_count,
            "policy_name": self.policy_name,
            **(context or {}),
        }

        decision = GULGovernanceDecision(
            decision=result.decision,
            confidence=result.confidence,
            reason=f"combined {len(decisions)} decisions via {combiner}",
            evidence=result.evidence,
            jurisdiction=result.jurisdiction,
            meta=meta,
        )
        self._record_decision(decision)
        self._inference_engine.clear_trace()
        return decision

    def _record_decision(self, decision: GULGovernanceDecision):
        """Record decision to history and database."""
        self.decision_history.append(decision)
        self._log_to_db(decision)

    def _log_to_db(self, decision: GULGovernanceDecision):
        """Emit audit event; DBSink persists to database if registered (optional geodesic_ai)."""
        try:
            from geodesic_ai.data.event_bus import EventBus
            from geodesic_ai.data.events import envelope_audit

            msg = (
                f"GUL Governance: {decision.decision.value.upper()} "
                f"(conf={decision.confidence.value:.3f}) - {decision.reason}"
            )
            EventBus.instance().emit(
                envelope_audit(
                    decision=decision.to_dict(),
                    policy_name=self.policy_name,
                    policy_params={
                        "max_risk": self.max_risk,
                        "min_coherence": self.min_coherence,
                        "min_confidence": self.min_confidence,
                    },
                    message=msg,
                )
            )
        except ImportError:
            pass  # geodesic_ai not installed: skip audit emission
        except Exception as e:
            import logging
            logging.error("Failed to emit GUL audit: %s", e)

    def get_decision_history(
        self, n: Optional[int] = None
    ) -> List[GULGovernanceDecision]:
        """Get recent decision history."""
        if n is None:
            return list(self.decision_history)
        return list(self.decision_history[-n:])

    def get_audit_summary(self) -> Dict[str, Any]:
        """Get summary of governance decisions for reporting."""
        if not self.decision_history:
            return {
                "total_decisions": 0,
                "by_decision": {},
                "average_confidence": 0.0,
            }

        total = len(self.decision_history)
        by_decision = {}
        for d in Decision:
            count = sum(1 for h in self.decision_history if h.decision == d)
            by_decision[d.value] = count

        avg_conf = sum(d.confidence.value for d in self.decision_history) / total

        return {
            "total_decisions": total,
            "by_decision": by_decision,
            "average_confidence": avg_conf,
            "policy_name": self.policy_name,
            "max_risk": self.max_risk,
            "min_coherence": self.min_coherence,
            "min_confidence": self.min_confidence,
        }

    def reset_history(self):
        """Clear decision history."""
        self.decision_history.clear()
        self._decision_count = 0

    def to_legacy_policy(self) -> "GovernancePolicy":
        """
        Convert to legacy GovernancePolicy.

        Returns a GovernancePolicy with equivalent thresholds. Requires geodesic_ai.
        """
        try:
            from geodesic_ai.kernel.governance.policy import GovernancePolicy
        except ImportError as e:
            raise RuntimeError("geodesic_ai required for to_legacy_policy()") from e

        return GovernancePolicy(
            max_risk=self.max_risk,
            min_coherence=self.min_coherence,
            db_manager=self.db_manager,
            policy_name=self.policy_name,
        )
