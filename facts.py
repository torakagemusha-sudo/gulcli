"""Fact environment for executing atom predicates in GUL specs."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .confidence import Confidence
from .decision import Decision, EvaluatedDecision
from .expr import Entity, Predicate


def _entity_key(entity: Any) -> str:
    if isinstance(entity, Entity):
        return f"{entity.kind}:{entity.id}"
    if isinstance(entity, dict):
        return f"{entity.get('kind', 'agent')}:{entity.get('id', '')}"
    return f"agent:{entity}"


@dataclass
class FactEnvironment:
    """Bindings used to evaluate atom predicates during inference."""

    roles: dict[str, list[str]] = field(default_factory=dict)
    attributes: dict[str, dict[str, str]] = field(default_factory=dict)
    belongs_to: set[tuple[str, str]] = field(default_factory=set)
    in_context: set[tuple[str, str]] = field(default_factory=set)
    custom: dict[str, bool] = field(default_factory=dict)
    now: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FactEnvironment:
        roles: dict[str, list[str]] = {}
        for key, value in dict(data.get("roles", {})).items():
            roles[str(key)] = [str(item) for item in value]

        attributes: dict[str, dict[str, str]] = {}
        for key, value in dict(data.get("attributes", {})).items():
            attributes[str(key)] = {str(attr): str(val) for attr, val in dict(value).items()}

        belongs_to: set[tuple[str, str]] = set()
        for item in data.get("belongs_to", []):
            entity = _entity_key(item.get("entity", {}))
            resource = _entity_key(item.get("resource", {}))
            belongs_to.add((entity, resource))

        in_context: set[tuple[str, str]] = set()
        for item in data.get("in_context", []):
            entity = _entity_key(item.get("entity", {}))
            context = _entity_key(item.get("ctx", item.get("context", {})))
            in_context.add((entity, context))

        custom = {str(key): bool(value) for key, value in dict(data.get("custom", {})).items()}
        now = data.get("now")
        return cls(
            roles=roles,
            attributes=attributes,
            belongs_to=belongs_to,
            in_context=in_context,
            custom=custom,
            now=int(now) if now is not None else None,
        )

    def _current_time(self) -> int:
        return self.now if self.now is not None else int(time.time())

    def _permit(self, evidence: str, confidence: float = 0.95) -> EvaluatedDecision:
        return EvaluatedDecision(
            decision=Decision.PERMIT,
            confidence=Confidence(confidence),
            evidence=[evidence],
        )

    def _deny(self, evidence: str, confidence: float = 1.0) -> EvaluatedDecision:
        return EvaluatedDecision(
            decision=Decision.DENY,
            confidence=Confidence(confidence),
            evidence=[evidence],
        )

    def _defer(self, evidence: str) -> EvaluatedDecision:
        return EvaluatedDecision(
            decision=Decision.DEFER,
            confidence=Confidence.zero(),
            evidence=[evidence],
        )

    def evaluate_predicate(self, pred: Predicate | dict[str, Any]) -> EvaluatedDecision:
        if isinstance(pred, dict):
            pred = Predicate.from_dict(pred)

        tag = pred.tag
        if tag == "has_role" and len(pred.args) >= 2:
            agent_key = _entity_key(pred.args[0])
            role = str(pred.args[1])
            roles = self.roles.get(agent_key)
            if roles is None:
                return self._defer(f"fact not found: roles for {agent_key}")
            if role in roles:
                return self._permit(f"has_role({agent_key}, {role})")
            return self._deny(f"missing role {role!r} for {agent_key}")

        if tag == "has_attribute" and len(pred.args) >= 3:
            entity_key = _entity_key(pred.args[0])
            attr = str(pred.args[1])
            expected = str(pred.args[2])
            attrs = self.attributes.get(entity_key)
            if attrs is None:
                return self._defer(f"fact not found: attributes for {entity_key}")
            actual = attrs.get(attr)
            if actual == expected:
                return self._permit(f"has_attribute({entity_key}, {attr}={expected})")
            return self._deny(f"attribute {attr!r} for {entity_key} is {actual!r}, expected {expected!r}")

        if tag == "belongs_to" and len(pred.args) >= 2:
            entity_key = _entity_key(pred.args[0])
            resource_key = _entity_key(pred.args[1])
            if (entity_key, resource_key) in self.belongs_to:
                return self._permit(f"belongs_to({entity_key}, {resource_key})")
            return self._deny(f"no belongs_to fact for {entity_key} -> {resource_key}")

        if tag == "in_context" and len(pred.args) >= 2:
            entity_key = _entity_key(pred.args[0])
            context_key = _entity_key(pred.args[1])
            if (entity_key, context_key) in self.in_context:
                return self._permit(f"in_context({entity_key}, {context_key})")
            return self._deny(f"no in_context fact for {entity_key} -> {context_key}")

        if tag == "time_before" and len(pred.args) >= 1:
            timestamp = int(pred.args[0])
            now = self._current_time()
            if now < timestamp:
                return self._permit(f"time_before({timestamp}); now={now}")
            return self._deny(f"time_before({timestamp}) failed; now={now}")

        if tag == "time_after" and len(pred.args) >= 1:
            timestamp = int(pred.args[0])
            now = self._current_time()
            if now > timestamp:
                return self._permit(f"time_after({timestamp}); now={now}")
            return self._deny(f"time_after({timestamp}) failed; now={now}")

        if tag == "custom" and len(pred.args) >= 1:
            name = str(pred.args[0])
            if name not in self.custom:
                return self._defer(f"fact not found: custom.{name}")
            if self.custom[name]:
                return self._permit(f"custom({name})")
            return self._deny(f"custom({name}) is false")

        return self._defer(f"unsupported predicate tag for fact evaluation: {tag}")
