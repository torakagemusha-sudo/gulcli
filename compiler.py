"""
GUL Constraint Compiler - GUL v2.1

Compiles PolicyExpr/Predicate to geodesic_ai Constraint using a registry
of named constraint builders. Supports build_lattice_from_gul_spec for
checkpoint loading.

Patent Note: GUL v2.1 is core IP - all implementation stays local.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from geodesic_ai.constraints.constraint import Constraint
    from geodesic_ai.constraints.lattice import ConstraintLattice

from .expr import PolicyExpr, Predicate
from .confidence import Confidence


def default_registry() -> Dict[str, Callable[..., "Constraint"]]:
    """Default registry of named constraint builders for geodesic use.

    Provides box bounds and sphere so minimal checkpoint JSON works.
    Each builder is called with (name, weight, **kwargs) and returns a Constraint.
    """
    import torch
    from geodesic_ai.constraints.constraint import Constraint

    def box_bounds(
        name: str,
        weight: float = 1.0,
        low: float = -5.0,
        high: float = 5.0,
        dims: Optional[List[int]] = None,
        **kwargs: Any,
    ) -> Constraint:
        dims = dims or [0, 1]
        # Single constraint that evaluates max over all bound violations
        def func(x: torch.Tensor) -> torch.Tensor:
            flat = x.view(-1)
            violations = []
            for d in dims:
                violations.append(flat[d] - high)
                violations.append(low - flat[d])
            return torch.stack(violations).max().unsqueeze(0)

        return Constraint(name=name, func=func, weight=weight)

    def sphere(
        name: str,
        weight: float = 1.0,
        radius: float = 1.0,
        center: Optional[List[float]] = None,
        **kwargs: Any,
    ) -> Constraint:
        center = center or [0.0, 0.0]
        c = torch.tensor(center, dtype=torch.float32)

        def func(x: torch.Tensor) -> torch.Tensor:
            diff = x.view(-1) - c[: x.numel()]
            return (diff.pow(2).sum() - radius ** 2).unsqueeze(0)

        return Constraint(name=name, func=func, weight=weight)

    def upper_bound(
        name: str,
        weight: float = 1.0,
        dim: int = 0,
        value: float = 0.0,
        **kwargs: Any,
    ) -> Constraint:
        def func(x: torch.Tensor) -> torch.Tensor:
            return (x.view(-1)[dim] - value).unsqueeze(0)

        return Constraint(name=name, func=func, weight=weight)

    def lower_bound(
        name: str,
        weight: float = 1.0,
        dim: int = 0,
        value: float = 0.0,
        **kwargs: Any,
    ) -> Constraint:
        def func(x: torch.Tensor) -> torch.Tensor:
            return (value - x.view(-1)[dim]).unsqueeze(0)

        return Constraint(name=name, func=func, weight=weight)

    return {
        "box": box_bounds,
        "box_bounds": box_bounds,
        "sphere": sphere,
        "upper_bound": upper_bound,
        "lower_bound": lower_bound,
    }


def compile_predicate_to_constraint(
    pred: Predicate,
    name: str,
    weight: float = 1.0,
    registry: Optional[Dict[str, Callable[..., "Constraint"]]] = None,
    confidence: Optional[float] = None,
) -> Optional["Constraint"]:
    """Compile a single Predicate to Constraint via registry.

    Only predicates that have a registry entry (e.g. custom(name, ...) with
    name in registry) can be compiled to a numeric Constraint. Others return None.

    Args:
        pred: Predicate to compile
        name: Constraint name
        weight: Constraint weight
        registry: Map from predicate name to builder (name, weight, **kwargs) -> Constraint
        confidence: Optional GUL confidence to attach

    Returns:
        Constraint or None if no registry match
    """
    from geodesic_ai.constraints.constraint import Constraint
    from geodesic_ai.gul.integration import constraint_with_confidence

    reg = registry or default_registry()
    if pred.tag == "custom" and pred.args:
        key = str(pred.args[0])
        if key in reg:
            builder = reg[key]
            c = builder(name=name, weight=weight)
            if confidence is not None:
                c = constraint_with_confidence(c, confidence, None)
            return c
    return None


def compile_policy_expr_to_constraints(
    expr: PolicyExpr,
    name_prefix: str = "c",
    weight: float = 1.0,
    registry: Optional[Dict[str, Callable[..., "Constraint"]]] = None,
    confidence: Optional[float] = None,
    index: int = 0,
) -> List["Constraint"]:
    """Compile a PolicyExpr to a list of Constraints.

    - atom(pred): compile pred via registry; if no match, skip.
    - and_(p1, p2): compile p1 and p2 and concatenate.
    - or_, not_, implies, with_confidence: compile first child; with_confidence
      passes confidence to compiled constraints.
    - always, eventually, until: compile child only (structural for now).

    Args:
        expr: PolicyExpr to compile
        name_prefix: Base name for constraints
        weight: Default weight
        registry: Named constraint builders
        confidence: Optional confidence (overridden by with_confidence)
        index: Suffix for unique names

    Returns:
        List of Constraint (may be empty)
    """
    from geodesic_ai.constraints.constraint import Constraint
    from geodesic_ai.gul.integration import constraint_with_confidence

    reg = registry or default_registry()
    out: List[Constraint] = []

    if expr.tag == "atom" and expr.children:
        pred = expr.children[0]
        if isinstance(pred, Predicate):
            c = compile_predicate_to_constraint(
                pred, f"{name_prefix}_{index}", weight, reg, confidence
            )
            if c is not None:
                out.append(c)
        return out

    if expr.tag == "with_confidence" and len(expr.children) >= 2:
        conf = float(expr.children[1]) if isinstance(expr.children[1], (int, float)) else 1.0
        sub = compile_policy_expr_to_constraints(
            expr.children[0], name_prefix, weight, reg, conf, index
        )
        for c in sub:
            out.append(constraint_with_confidence(c, conf, None))
        return out

    if expr.tag in ("and_", "or_", "implies") and len(expr.children) >= 2:
        for i, child in enumerate(expr.children[:2]):
            if isinstance(child, PolicyExpr):
                out.extend(
                    compile_policy_expr_to_constraints(
                        child, name_prefix, weight, reg, confidence, index + i
                    )
                )
        return out

    if expr.tag == "not_" and expr.children and isinstance(expr.children[0], PolicyExpr):
        out.extend(
            compile_policy_expr_to_constraints(
                expr.children[0], name_prefix, weight, reg, confidence, index
            )
        )
        return out

    if expr.tag in ("always", "eventually", "until") and expr.children:
        if isinstance(expr.children[0], PolicyExpr):
            out.extend(
                compile_policy_expr_to_constraints(
                    expr.children[0], name_prefix, weight, reg, confidence, index
                )
            )
    return out


def build_lattice_from_gul_spec(
    spec: dict,
    registry: Optional[Dict[str, Callable[..., "Constraint"]]] = None,
) -> "ConstraintLattice":
    """Build a ConstraintLattice from a spec containing gul_constraints.

    Reads "gul_constraints": list of { "name", "weight", "expr": <PolicyExpr dict>,
    "confidence"?: number }. Parses each expr, compiles via registry, and adds
    to the lattice. Missing registry entries are skipped.

    If "gul_constraints" is absent, returns an empty lattice (backward compat).

    Args:
        spec: Checkpoint-like dict with optional gul_constraints
        registry: Named constraint builders (default_registry() if None)

    Returns:
        ConstraintLattice with compiled constraints
    """
    from geodesic_ai.constraints.lattice import ConstraintLattice

    lattice = ConstraintLattice()
    items = spec.get("gul_constraints") or []
    reg = registry or default_registry()

    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", f"gul_{i}"))
        weight = float(item.get("weight", 1.0))
        confidence = item.get("confidence")
        if confidence is not None:
            confidence = float(confidence)
        expr_dict = item.get("expr")
        if not expr_dict:
            continue
        expr = PolicyExpr.from_dict(expr_dict)
        constraints = compile_policy_expr_to_constraints(
            expr, name_prefix=name, weight=weight, registry=reg, confidence=confidence, index=i
        )
        for c in constraints:
            lattice.add(c)

    return lattice
