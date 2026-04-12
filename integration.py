"""
GUL Integration Adapters - GUL v2.1

Adapters for integrating GUL with existing geodesic_ai components.
Provides seamless migration path from legacy to GUL semantics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .confidence import Confidence, ConfidenceOps
from .decision import Decision, EvaluatedDecision
from .jurisdiction import Jurisdiction, JurisdictionId, JurisdictionLevel
from .policy import GULGovernanceDecision, GULGovernancePolicy

if TYPE_CHECKING:
    from geodesic_ai.constraints.constraint import Constraint
    from geodesic_ai.constraints.lattice import ConstraintLattice
    from geodesic_ai.kernel.governance.policy import GovernanceDecision, GovernancePolicy


def legacy_decision_to_gul(
    decision: "GovernanceDecision",
    confidence: Optional[float] = None,
) -> GULGovernanceDecision:
    """
    Convert legacy GovernanceDecision to GULGovernanceDecision.

    Args:
        decision: Legacy GovernanceDecision
        confidence: Optional confidence override (default 1.0)

    Returns:
        GULGovernanceDecision with equivalent semantics
    """
    gul_decision = Decision.PERMIT if decision.ok else Decision.DENY
    conf = Confidence(confidence if confidence is not None else 1.0)

    return GULGovernanceDecision(
        decision=gul_decision,
        confidence=conf,
        reason=decision.reason,
        evidence=[decision.reason] if decision.reason else [],
        meta=decision.meta or {},
        timestamp=decision.timestamp,
        policy_version=decision.policy_version,
    )


def gul_decision_to_legacy(
    decision: GULGovernanceDecision,
) -> "GovernanceDecision":
    """
    Convert GULGovernanceDecision to legacy GovernanceDecision.

    Uses the `ok` property for backward compatibility.

    Args:
        decision: GULGovernanceDecision

    Returns:
        Legacy GovernanceDecision
    """
    return decision.to_legacy()


def legacy_policy_to_gul(
    policy: "GovernancePolicy",
    min_confidence: float = 0.5,
    jurisdiction: Optional[Jurisdiction] = None,
) -> GULGovernancePolicy:
    """
    Convert legacy GovernancePolicy to GULGovernancePolicy.

    Args:
        policy: Legacy GovernancePolicy
        min_confidence: Minimum confidence threshold
        jurisdiction: Optional jurisdiction scope

    Returns:
        GULGovernancePolicy with extended semantics
    """
    return GULGovernancePolicy(
        max_risk=policy.max_risk,
        min_coherence=policy.min_coherence,
        min_confidence=min_confidence,
        jurisdiction=jurisdiction,
        db_manager=policy.db_manager,
        policy_name=policy.policy_name,
    )


def constraint_with_confidence(
    constraint: "Constraint",
    confidence: float,
    jurisdiction: Optional[JurisdictionId] = None,
) -> "Constraint":
    """
    Create constraint copy with GUL confidence and jurisdiction.

    Args:
        constraint: Source constraint
        confidence: Confidence level in [0,1]
        jurisdiction: Optional jurisdiction scope

    Returns:
        New Constraint with GUL attributes set
    """
    from geodesic_ai.constraints.constraint import Constraint as ConstraintClass

    new_constraint = ConstraintClass(
        name=constraint.name,
        func=constraint.func,
        weight=constraint.weight,
        z3_builder=constraint.z3_builder,
        projector=constraint.projector,
        analytical_gradient=constraint.analytical_gradient,
    )
    new_constraint.confidence = Confidence(confidence)
    new_constraint.jurisdiction = jurisdiction
    return new_constraint


def lattice_with_uniform_confidence(
    lattice: "ConstraintLattice",
    confidence: float,
) -> "ConstraintLattice":
    """
    Create lattice copy with uniform confidence on all constraints.

    Args:
        lattice: Source constraint lattice
        confidence: Confidence level to apply to all constraints

    Returns:
        New ConstraintLattice with GUL confidence
    """
    from geodesic_ai.constraints.lattice import ConstraintLattice as LatticeClass

    result = LatticeClass()
    for c in lattice.constraints:
        new_c = constraint_with_confidence(c, confidence)
        result.add(new_c)
    return result


def evaluate_constraint_with_gul(
    constraint: "Constraint",
    x,  # torch.Tensor
    min_confidence: float = 0.5,
) -> EvaluatedDecision:
    """
    Evaluate constraint and return GUL EvaluatedDecision.

    Args:
        constraint: Constraint to evaluate
        x: Point to evaluate at
        min_confidence: Threshold for deferral

    Returns:
        EvaluatedDecision based on constraint satisfaction
    """
    import torch

    value = constraint.evaluate(x)
    is_satisfied = bool(torch.all(value <= 0.0))
    conf = constraint.confidence

    if is_satisfied:
        decision = Decision.PERMIT
    else:
        decision = Decision.DENY

    if conf.value < min_confidence:
        decision = Decision.DEFER

    return EvaluatedDecision(
        decision=decision,
        confidence=conf,
        evidence=[f"constraint:{constraint.name}={value.max().item():.4f}"],
        jurisdiction=constraint.jurisdiction,
    )


def evaluate_lattice_with_gul(
    lattice: "ConstraintLattice",
    x,  # torch.Tensor
    min_confidence: float = 0.5,
    combiner: str = "and",
) -> EvaluatedDecision:
    """
    Evaluate constraint lattice and return GUL EvaluatedDecision.

    Args:
        lattice: ConstraintLattice to evaluate
        x: Point to evaluate at
        min_confidence: Threshold for deferral
        combiner: How to combine constraint decisions

    Returns:
        Combined EvaluatedDecision for all constraints
    """
    from .inference import GULInferenceEngine

    if not lattice.constraints:
        return EvaluatedDecision(
            decision=Decision.PERMIT,
            confidence=Confidence.one(),
            evidence=["no constraints"],
        )

    decisions = [
        evaluate_constraint_with_gul(c, x, min_confidence)
        for c in lattice.constraints
    ]

    engine = GULInferenceEngine()
    return engine.evaluate_all(decisions, combiner)


def create_jurisdiction_hierarchy(
    names: List[str],
    levels: Optional[List[JurisdictionLevel]] = None,
    authority: str = "system",
) -> List[Jurisdiction]:
    """
    Create a hierarchy of jurisdictions from names.

    Args:
        names: List of jurisdiction names (root first)
        levels: Optional list of levels (defaults to descending)
        authority: Authority entity name

    Returns:
        List of Jurisdiction objects in hierarchy
    """
    if not names:
        return []

    if levels is None:
        all_levels = list(JurisdictionLevel)
        levels = all_levels[:len(names)]

    result = []
    parent_id = None

    for name, level in zip(names, levels):
        jid = JurisdictionId(name=name, parent=parent_id)
        jurisdiction = Jurisdiction(
            id=jid,
            level=level,
            authority=authority,
        )
        result.append(jurisdiction)
        parent_id = jid

    return result


class GULAdapter:
    """
    Central adapter for GUL integration.

    Provides methods to convert between legacy and GUL types
    and to evaluate with GUL semantics.
    """

    def __init__(
        self,
        min_confidence: float = 0.5,
        default_jurisdiction: Optional[Jurisdiction] = None,
    ):
        """
        Initialize GUL adapter.

        Args:
            min_confidence: Default minimum confidence threshold
            default_jurisdiction: Default jurisdiction scope
        """
        self.min_confidence = min_confidence
        self.default_jurisdiction = default_jurisdiction

    def wrap_policy(self, policy: "GovernancePolicy") -> GULGovernancePolicy:
        """Wrap legacy policy with GUL semantics."""
        return legacy_policy_to_gul(
            policy,
            min_confidence=self.min_confidence,
            jurisdiction=self.default_jurisdiction,
        )

    def wrap_decision(
        self,
        decision: "GovernanceDecision",
        confidence: Optional[float] = None,
    ) -> GULGovernanceDecision:
        """Wrap legacy decision with GUL semantics."""
        return legacy_decision_to_gul(decision, confidence)

    def wrap_constraint(
        self,
        constraint: "Constraint",
        confidence: float = 1.0,
    ) -> "Constraint":
        """Add GUL confidence to constraint."""
        return constraint_with_confidence(
            constraint,
            confidence,
            self.default_jurisdiction.id if self.default_jurisdiction else None,
        )

    def evaluate_constraint(
        self,
        constraint: "Constraint",
        x,
    ) -> EvaluatedDecision:
        """Evaluate constraint with GUL semantics."""
        return evaluate_constraint_with_gul(constraint, x, self.min_confidence)

    def evaluate_lattice(
        self,
        lattice: "ConstraintLattice",
        x,
        combiner: str = "and",
    ) -> EvaluatedDecision:
        """Evaluate lattice with GUL semantics."""
        return evaluate_lattice_with_gul(lattice, x, self.min_confidence, combiner)
