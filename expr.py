"""
GUL Policy Expression DSL - GUL v2.1

Mirrors gul-formal/GUL.lean Predicate and PolicyExpr.
Provides JSON-friendly to_dict/from_dict for checkpoints and configs.

Patent Note: GUL v2.1 is core IP - all implementation stays local.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Union


# ---------------------------------------------------------------------------
# Entity (simple string or small struct for agent/resource/context/policy)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Entity:
    """Entity in GUL universe: agent, resource, context, or policy."""

    kind: str  # "agent" | "resource" | "context" | "policy"
    id: str

    def to_dict(self) -> dict:
        return {"kind": self.kind, "id": self.id}

    @classmethod
    def from_dict(cls, d: dict) -> Entity:
        return cls(kind=str(d.get("kind", "agent")), id=str(d.get("id", "")))


# ---------------------------------------------------------------------------
# Predicate (atomic policy predicates from GUL.lean)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Predicate:
    """
    Atomic policy predicate - mirrors GUL.lean Predicate.

    Variants: belongs_to, has_role, has_attribute, in_context,
    time_before, time_after, custom.
    """

    tag: str
    args: tuple = field(default_factory=tuple)

    def to_dict(self) -> dict:
        out: Dict[str, Any] = {"tag": self.tag}
        if self.tag == "belongs_to" and len(self.args) >= 2:
            out["entity"] = _entity_to_dict(self.args[0])
            out["resource"] = _entity_to_dict(self.args[1])
        elif self.tag == "has_role" and len(self.args) >= 2:
            out["agent"] = _entity_to_dict(self.args[0])
            out["role"] = str(self.args[1])
        elif self.tag == "has_attribute" and len(self.args) >= 3:
            out["entity"] = _entity_to_dict(self.args[0])
            out["attr"] = str(self.args[1])
            out["value"] = str(self.args[2])
        elif self.tag == "in_context" and len(self.args) >= 2:
            out["entity"] = _entity_to_dict(self.args[0])
            out["ctx"] = _entity_to_dict(self.args[1])
        elif self.tag == "time_before" and len(self.args) >= 1:
            out["timestamp"] = self.args[0]
        elif self.tag == "time_after" and len(self.args) >= 1:
            out["timestamp"] = self.args[0]
        elif self.tag == "custom" and len(self.args) >= 1:
            out["name"] = str(self.args[0])
            out["args"] = [_entity_to_dict(a) for a in self.args[1:]]
        return out

    @classmethod
    def from_dict(cls, d: dict) -> Predicate:
        tag = str(d.get("tag", "custom"))
        if tag == "belongs_to":
            return belongs_to(
                _dict_to_entity(d.get("entity", {})),
                _dict_to_entity(d.get("resource", {})),
            )
        if tag == "has_role":
            return has_role(
                _dict_to_entity(d.get("agent", {})),
                str(d.get("role", "")),
            )
        if tag == "has_attribute":
            return has_attribute(
                _dict_to_entity(d.get("entity", {})),
                str(d.get("attr", "")),
                str(d.get("value", "")),
            )
        if tag == "in_context":
            return in_context(
                _dict_to_entity(d.get("entity", {})),
                _dict_to_entity(d.get("ctx", {})),
            )
        if tag == "time_before":
            return time_before(int(d.get("timestamp", 0)))
        if tag == "time_after":
            return time_after(int(d.get("timestamp", 0)))
        if tag == "custom":
            name = str(d.get("name", ""))
            args = [_dict_to_entity(a) for a in d.get("args", [])]
            return custom(name, *args)
        return custom(str(d.get("name", tag)), *d.get("args", []))


def _entity_to_dict(e: Any) -> dict:
    if isinstance(e, Entity):
        return e.to_dict()
    if isinstance(e, dict):
        return e
    return {"kind": "agent", "id": str(e)}


def _dict_to_entity(d: Any) -> Union[Entity, str]:
    if isinstance(d, Entity):
        return d
    if isinstance(d, dict):
        return Entity.from_dict(d)
    return Entity("agent", str(d))


def belongs_to(entity: Union[Entity, str], resource: Union[Entity, str]) -> Predicate:
    e = entity if isinstance(entity, Entity) else Entity("agent", str(entity))
    r = resource if isinstance(resource, Entity) else Entity("resource", str(resource))
    return Predicate(tag="belongs_to", args=(e, r))


def has_role(agent: Union[Entity, str], role: str) -> Predicate:
    a = agent if isinstance(agent, Entity) else Entity("agent", str(agent))
    return Predicate(tag="has_role", args=(a, role))


def has_attribute(entity: Union[Entity, str], attr: str, value: str) -> Predicate:
    e = entity if isinstance(entity, Entity) else Entity("agent", str(entity))
    return Predicate(tag="has_attribute", args=(e, attr, value))


def in_context(entity: Union[Entity, str], ctx: Union[Entity, str]) -> Predicate:
    e = entity if isinstance(entity, Entity) else Entity("agent", str(entity))
    c = ctx if isinstance(ctx, Entity) else Entity("context", str(ctx))
    return Predicate(tag="in_context", args=(e, c))


def time_before(timestamp: int) -> Predicate:
    return Predicate(tag="time_before", args=(timestamp,))


def time_after(timestamp: int) -> Predicate:
    return Predicate(tag="time_after", args=(timestamp,))


def custom(name: str, *args: Any) -> Predicate:
    return Predicate(tag="custom", args=(name, *args))


# ---------------------------------------------------------------------------
# PolicyExpr (policy expression abstract syntax from GUL.lean)
# ---------------------------------------------------------------------------

PolicyExprChild = Union["PolicyExpr", Predicate]


@dataclass
class PolicyExpr:
    """
    Policy expression - mirrors GUL.lean PolicyExpr.

    Variants: atom, and_, or_, not_, implies, with_confidence,
    always, eventually, until (optional).
    """

    tag: str
    children: List[Any] = field(default_factory=list)  # PolicyExpr or Predicate or float

    def to_dict(self) -> dict:
        out: Dict[str, Any] = {"tag": self.tag}
        if self.tag == "atom" and self.children:
            out["pred"] = self.children[0].to_dict() if hasattr(self.children[0], "to_dict") else self.children[0]
        elif self.tag in ("and_", "or_", "implies") and len(self.children) >= 2:
            out["p1"] = _expr_to_dict(self.children[0])
            out["p2"] = _expr_to_dict(self.children[1])
        elif self.tag == "not_" and self.children:
            out["p"] = _expr_to_dict(self.children[0])
        elif self.tag == "with_confidence" and len(self.children) >= 2:
            out["p"] = _expr_to_dict(self.children[0])
            c1 = self.children[1]
            out["confidence"] = (
                float(c1) if isinstance(c1, (int, float)) else getattr(c1, "value", 1.0)
            )
        elif self.tag in ("always", "eventually") and self.children:
            out["p"] = _expr_to_dict(self.children[0])
        elif self.tag == "until" and len(self.children) >= 2:
            out["p1"] = _expr_to_dict(self.children[0])
            out["p2"] = _expr_to_dict(self.children[1])
        return out

    @classmethod
    def from_dict(cls, d: dict) -> PolicyExpr:
        tag = str(d.get("tag", "atom"))

        def _p(key: str):
            return PolicyExpr.from_dict(d[key]) if key in d else atom(Predicate.from_dict({}))

        def _p1p2():
            return _p("p1"), _p("p2")

        if tag == "atom":
            pred = d.get("pred", d)
            return atom(
                Predicate.from_dict(pred) if isinstance(pred, dict) else pred
            )
        if tag == "and_":
            a, b = _p1p2()
            return and_(a, b)
        if tag == "or_":
            a, b = _p1p2()
            return or_(a, b)
        if tag == "not_":
            return not_(_p("p"))
        if tag == "implies":
            a, b = _p1p2()
            return implies(a, b)
        if tag == "with_confidence":
            p = _p("p")
            c = float(d.get("confidence", 1.0))
            return with_confidence(p, c)
        if tag == "always":
            return always(_p("p"))
        if tag == "eventually":
            return eventually(_p("p"))
        if tag == "until":
            a, b = _p1p2()
            return until(a, b)
        return atom(Predicate.from_dict(d.get("pred", d)))


def _expr_to_dict(x: Any) -> dict:
    if hasattr(x, "to_dict"):
        return x.to_dict()
    if isinstance(x, dict):
        return x
    return {"tag": "atom", "pred": x}


def atom(pred: Predicate) -> PolicyExpr:
    return PolicyExpr(tag="atom", children=[pred])


def and_(p1: PolicyExpr, p2: PolicyExpr) -> PolicyExpr:
    return PolicyExpr(tag="and_", children=[p1, p2])


def or_(p1: PolicyExpr, p2: PolicyExpr) -> PolicyExpr:
    return PolicyExpr(tag="or_", children=[p1, p2])


def not_(p: PolicyExpr) -> PolicyExpr:
    return PolicyExpr(tag="not_", children=[p])


def implies(p1: PolicyExpr, p2: PolicyExpr) -> PolicyExpr:
    return PolicyExpr(tag="implies", children=[p1, p2])


def with_confidence(p: PolicyExpr, c: float) -> PolicyExpr:
    return PolicyExpr(tag="with_confidence", children=[p, c])


def always(p: PolicyExpr) -> PolicyExpr:
    return PolicyExpr(tag="always", children=[p])


def eventually(p: PolicyExpr) -> PolicyExpr:
    return PolicyExpr(tag="eventually", children=[p])


def until(p1: PolicyExpr, p2: PolicyExpr) -> PolicyExpr:
    return PolicyExpr(tag="until", children=[p1, p2])
