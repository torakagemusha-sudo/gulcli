"""
Governed Uncertainty Logic (GUL) v2.1


Core IP implementation for geodesic_ai framework.
Provides:
- Confidence lattice with bounded [0,1] values and algebraic operations
- 4-valued decision types (permit, deny, defer, abstain)
- Jurisdiction type system for authority boundaries
- Formal inference rules for policy evaluation
- Extended certificate/audit system

Patent Note: GUL v2.1 is core IP - all implementation stays local.
"""

__version__ = "2.2.0-dev0"

from .confidence import Confidence, ConfidenceOps
from .decision import Decision, EvaluatedDecision, DecisionCombiner
from .jurisdiction import (
    JurisdictionLevel,
    JurisdictionId,
    Jurisdiction,
    JType,
)
from .inference import GULInferenceEngine
from .policy import GULGovernanceDecision, GULGovernancePolicy
from .integration import (
    GULAdapter,
    legacy_decision_to_gul,
    legacy_policy_to_gul,
    constraint_with_confidence,
    lattice_with_uniform_confidence,
    evaluate_constraint_with_gul,
    evaluate_lattice_with_gul,
    create_jurisdiction_hierarchy,
)
from .expr import (
    Entity,
    Predicate,
    PolicyExpr,
    atom,
    and_,
    or_,
    not_,
    implies,
    with_confidence,
    always,
    eventually,
    until,
    belongs_to,
    has_role,
    has_attribute,
    in_context,
    time_before,
    time_after,
    custom,
)
from .compiler import (
    default_registry,
    compile_predicate_to_constraint,
    compile_policy_expr_to_constraints,
    build_lattice_from_gul_spec,
)
from .runtime_io import (
    evaluate_expr_data,
    infer_file,
    validate_file,
    validate_spec_data,
)
from .cli_bridge import (
    find_gul_exe,
    generate_dataset,
    stream_dataset,
    validate as cli_validate,
    infer as cli_infer,
)

__all__ = [
    # Confidence
    "Confidence",
    "ConfidenceOps",
    # Decision
    "Decision",
    "EvaluatedDecision",
    "DecisionCombiner",
    # Jurisdiction
    "JurisdictionLevel",
    "JurisdictionId",
    "Jurisdiction",
    "JType",
    # Inference
    "GULInferenceEngine",
    # Policy
    "GULGovernanceDecision",
    "GULGovernancePolicy",
    # Integration
    "GULAdapter",
    "legacy_decision_to_gul",
    "legacy_policy_to_gul",
    "constraint_with_confidence",
    "lattice_with_uniform_confidence",
    "evaluate_constraint_with_gul",
    "evaluate_lattice_with_gul",
    "create_jurisdiction_hierarchy",
    # Expr DSL
    "Entity",
    "Predicate",
    "PolicyExpr",
    "atom",
    "and_",
    "or_",
    "not_",
    "implies",
    "with_confidence",
    "always",
    "eventually",
    "until",
    "belongs_to",
    "has_role",
    "has_attribute",
    "in_context",
    "time_before",
    "time_after",
    "custom",
    # Compiler
    "default_registry",
    "compile_predicate_to_constraint",
    "compile_policy_expr_to_constraints",
    "build_lattice_from_gul_spec",
    # Executable runtime (JSON specs)
    "validate_spec_data",
    "evaluate_expr_data",
    "validate_file",
    "infer_file",
    # CLI bridge
    "find_gul_exe",
    "generate_dataset",
    "stream_dataset",
    "cli_validate",
    "cli_infer",
]
