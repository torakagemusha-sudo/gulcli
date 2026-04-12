from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from .confidence import Confidence, ConfidenceOps
from .decision import Decision, DecisionCombiner, EvaluatedDecision
from .expr import Predicate
from .inference import GULInferenceEngine

RUNTIME_VERSION = "2.2.0-dev0"

_VALID_DECISIONS = {d.value for d in Decision}
_BINARY_TAGS = {"and_", "or_", "sequential", "parallel", "implies", "until"}
_UNARY_TAGS = {"not_", "always", "eventually"}


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_data(data: Any) -> str:
    return hashlib.sha256(_stable_json(data).encode("utf-8")).hexdigest()


def _message(path: str, code: str, message: str, severity: str = "error", **extra: Any) -> dict[str, Any]:
    out = {
        "path": path,
        "code": code,
        "severity": severity,
        "message": message,
    }
    out.update(extra)
    return out


def _ensure_confidence(value: Any, path: str, messages: list[dict[str, Any]]) -> float:
    if not isinstance(value, (int, float)):
        messages.append(_message(path, "E_CONF_TYPE", "confidence must be numeric"))
        return 0.0
    if not (0.0 <= float(value) <= 1.0):
        messages.append(_message(path, "E_CONF_RANGE", "confidence must be in [0,1]"))
    return float(value)


def _validate_predicate(pred: Any, path: str, messages: list[dict[str, Any]]) -> None:
    if not isinstance(pred, dict):
        messages.append(_message(path, "E_PRED_TYPE", "predicate must be an object"))
        return
    tag = pred.get("tag")
    if not isinstance(tag, str):
        messages.append(_message(path, "E_PRED_TAG", "predicate.tag must be a string"))
        return
    try:
        Predicate.from_dict(pred)
    except Exception as exc:
        messages.append(_message(path, "E_PRED_INVALID", f"invalid predicate: {exc}"))


def _validate_node(node: Any, path: str, messages: list[dict[str, Any]]) -> None:
    if not isinstance(node, dict):
        messages.append(_message(path, "E_NODE_TYPE", "expression node must be an object"))
        return
    tag = node.get("tag")
    if not isinstance(tag, str):
        messages.append(_message(path, "E_TAG", "tag must be a string"))
        return

    if tag in _BINARY_TAGS:
        if "p1" not in node or "p2" not in node:
            messages.append(_message(path, "E_BINARY_CHILDREN", f"{tag} requires p1 and p2"))
        else:
            _validate_node(node["p1"], f"{path}.p1", messages)
            _validate_node(node["p2"], f"{path}.p2", messages)
        return

    if tag in _UNARY_TAGS:
        if "p" not in node:
            messages.append(_message(path, "E_UNARY_CHILD", f"{tag} requires p"))
        else:
            _validate_node(node["p"], f"{path}.p", messages)
        return

    if tag == "decision":
        decision = node.get("decision")
        if decision not in _VALID_DECISIONS:
            messages.append(_message(path, "E_DECISION_VALUE", "decision must be one of permit|deny|defer|abstain"))
        _ensure_confidence(node.get("confidence", 1.0), f"{path}.confidence", messages)
        evidence = node.get("evidence", [])
        if not isinstance(evidence, list) or not all(isinstance(x, str) for x in evidence):
            messages.append(_message(path, "E_EVIDENCE", "evidence must be a list of strings"))
        jurisdiction = node.get("jurisdiction")
        if jurisdiction is not None and not isinstance(jurisdiction, str):
            messages.append(_message(path, "E_JURISDICTION", "jurisdiction must be a string when present"))
        return

    if tag == "atom":
        pred = node.get("pred")
        if pred is None:
            messages.append(_message(path, "E_ATOM_PRED", "atom requires pred"))
        else:
            _validate_predicate(pred, f"{path}.pred", messages)
        return

    if tag == "with_confidence":
        if "p" not in node:
            messages.append(_message(path, "E_WITH_CONF_CHILD", "with_confidence requires p"))
        else:
            _validate_node(node["p"], f"{path}.p", messages)
        _ensure_confidence(node.get("confidence"), f"{path}.confidence", messages)
        return

    if tag == "threshold":
        if "p" not in node:
            messages.append(_message(path, "E_THRESHOLD_CHILD", "threshold requires p"))
        else:
            _validate_node(node["p"], f"{path}.p", messages)
        _ensure_confidence(node.get("threshold"), f"{path}.threshold", messages)
        return

    if tag == "jurisdiction":
        if "p" not in node:
            messages.append(_message(path, "E_JUR_CHILD", "jurisdiction requires p"))
        else:
            _validate_node(node["p"], f"{path}.p", messages)
        required = node.get("required")
        if not isinstance(required, str) or not required:
            messages.append(_message(path, "E_JUR_REQUIRED", "jurisdiction.required must be a non-empty string"))
        request = node.get("request")
        if request is not None and not isinstance(request, str):
            messages.append(_message(path, "E_JUR_REQUEST", "jurisdiction.request must be a string when present"))
        return

    if tag == "override":
        if "base" not in node or "override" not in node:
            messages.append(_message(path, "E_OVERRIDE_CHILDREN", "override requires base and override"))
        else:
            _validate_node(node["base"], f"{path}.base", messages)
            _validate_node(node["override"], f"{path}.override", messages)
        return

    messages.append(_message(path, "E_TAG_UNKNOWN", f"unknown tag: {tag}"))


def _normalize_node(node: Any) -> Any:
    if isinstance(node, dict):
        return {key: _normalize_node(node[key]) for key in sorted(node.keys())}
    if isinstance(node, list):
        return [_normalize_node(item) for item in node]
    return node


def validate_spec_data(data: Any, source: str = "<memory>") -> dict[str, Any]:
    messages: list[dict[str, Any]] = []

    root = data
    if isinstance(data, dict) and "expr" in data:
        root = data["expr"]

    _validate_node(root, "$", messages)

    normalized = _normalize_node(data)
    ok = not any(msg["severity"] == "error" for msg in messages)
    return {
        "schema": "gul.validation.result/1",
        "version": RUNTIME_VERSION,
        "source": source,
        "ok": ok,
        "errors": messages,
        "normalized": normalized,
        "input_hash": _sha256_data(normalized),
    }


def _ed_from_node(node: dict[str, Any]) -> EvaluatedDecision:
    decision = Decision(node["decision"])
    confidence = Confidence(float(node.get("confidence", 1.0)))
    evidence = list(node.get("evidence", []))
    jurisdiction = node.get("jurisdiction")
    return EvaluatedDecision(decision=decision, confidence=confidence, evidence=evidence, jurisdiction=jurisdiction)


def _eval_atom(node: dict[str, Any]) -> EvaluatedDecision:
    pred = node.get("pred", {})
    tag = pred.get("tag")
    raise ValueError(f"atom nodes are structural only and cannot be executed without a fact environment (predicate tag={tag!r})")


def evaluate_expr_data(data: Any, include_trace: bool = False) -> dict[str, Any]:
    validation = validate_spec_data(data)
    if not validation["ok"]:
        raise ValueError("input did not validate")

    node = data["expr"] if isinstance(data, dict) and "expr" in data else data
    engine = GULInferenceEngine()

    def _eval(expr: dict[str, Any]) -> EvaluatedDecision:
        tag = expr["tag"]
        if tag == "decision":
            return _ed_from_node(expr)
        if tag == "atom":
            return _eval_atom(expr)
        if tag == "and_":
            return engine.evaluate_and(_eval(expr["p1"]), _eval(expr["p2"]))
        if tag == "or_":
            return engine.evaluate_or(_eval(expr["p1"]), _eval(expr["p2"]))
        if tag == "sequential":
            return engine.evaluate_sequential(_eval(expr["p1"]), _eval(expr["p2"]))
        if tag == "parallel":
            return engine.evaluate_parallel(_eval(expr["p1"]), _eval(expr["p2"]))
        if tag == "not_":
            return engine.evaluate_not(_eval(expr["p"]))
        if tag == "implies":
            antecedent = _eval(expr["p1"])
            consequent = _eval(expr["p2"])
            return engine.evaluate_or(engine.evaluate_not(antecedent), consequent)
        if tag == "with_confidence":
            inner = _eval(expr["p"])
            annotated = Confidence(float(expr["confidence"]))
            return EvaluatedDecision(
                decision=inner.decision,
                confidence=ConfidenceOps.combine_intersection(inner.confidence, annotated),
                evidence=inner.evidence + [f"annotated confidence={annotated.value:.4f}"],
                jurisdiction=inner.jurisdiction,
            )
        if tag == "threshold":
            inner = _eval(expr["p"])
            return engine.evaluate_threshold(inner, float(expr["threshold"]))
        if tag == "jurisdiction":
            inner = _eval(expr["p"])
            required = str(expr["required"])
            request = str(expr.get("request", required))
            if request == required or request.startswith(required + "."):
                return EvaluatedDecision(
                    decision=inner.decision,
                    confidence=inner.confidence,
                    evidence=inner.evidence + [f"jurisdiction in scope: {request} ⊆ {required}"],
                    jurisdiction=required,
                )
            result = EvaluatedDecision(
                decision=Decision.ABSTAIN,
                confidence=Confidence.one(),
                evidence=inner.evidence + [f"out of jurisdiction: {request} ⊄ {required}"],
                jurisdiction=required,
            )
            engine._record_trace("JURISDICTION", [inner], result, request=request, required=required)
            return result
        if tag == "override":
            base = _eval(expr["base"])
            over = _eval(expr["override"])
            final_decision = DecisionCombiner.override(base.decision, over.decision)
            if over.decision == Decision.ABSTAIN:
                return EvaluatedDecision(
                    decision=base.decision,
                    confidence=base.confidence,
                    evidence=base.evidence + over.evidence + ["override abstained"],
                    jurisdiction=base.jurisdiction,
                )
            return EvaluatedDecision(
                decision=final_decision,
                confidence=ConfidenceOps.combine_union(base.confidence, over.confidence),
                evidence=base.evidence + over.evidence + ["override applied"],
                jurisdiction=over.jurisdiction or base.jurisdiction,
            )
        if tag == "always":
            inner = _eval(expr["p"])
            return EvaluatedDecision(
                decision=inner.decision,
                confidence=inner.confidence,
                evidence=inner.evidence + ["always constraint preserved structurally"],
                jurisdiction=inner.jurisdiction,
            )
        if tag == "eventually":
            inner = _eval(expr["p"])
            return EvaluatedDecision(
                decision=inner.decision,
                confidence=inner.confidence,
                evidence=inner.evidence + ["eventually constraint preserved structurally"],
                jurisdiction=inner.jurisdiction,
            )
        if tag == "until":
            left = _eval(expr["p1"])
            right = _eval(expr["p2"])
            out = engine.evaluate_sequential(left, right)
            return EvaluatedDecision(
                decision=out.decision,
                confidence=out.confidence,
                evidence=out.evidence + ["until composed as sequential approximation"],
                jurisdiction=out.jurisdiction,
            )
        raise ValueError(f"unsupported tag: {tag}")

    result = _eval(node)
    payload = {
        "schema": "gul.inference.result/1",
        "version": RUNTIME_VERSION,
        "input_hash": _sha256_data(_normalize_node(data)),
        "decision": result.decision.value,
        "confidence": result.confidence.value,
        "evidence": list(result.evidence),
        "jurisdiction": result.jurisdiction,
        "trace": engine.get_trace_summary() if include_trace else [],
    }
    return payload


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_file(path: str | Path) -> dict[str, Any]:
    return validate_spec_data(load_json(path), source=str(path))


def infer_file(path: str | Path, include_trace: bool = False) -> dict[str, Any]:
    return evaluate_expr_data(load_json(path), include_trace=include_trace)


def _print_validation(result: dict[str, Any], as_json: bool) -> int:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        status = "OK" if result["ok"] else "INVALID"
        print(f"{status}: {result['source']}")
        for msg in result["errors"]:
            print(f"[{msg['severity']}] {msg['code']} {msg['path']}: {msg['message']}")
    return 0 if result["ok"] else 1


def _print_inference(result: dict[str, Any], as_json: bool) -> int:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"decision={result['decision']}")
        print(f"confidence={result['confidence']:.4f}")
        if result.get("jurisdiction"):
            print(f"jurisdiction={result['jurisdiction']}")
        if result["evidence"]:
            print("evidence:")
            for item in result["evidence"]:
                print(f"  - {item}")
        if result["trace"]:
            print("trace:")
            for step in result["trace"]:
                print(f"  - {step['rule']} -> {step['output']['decision']} ({step['output']['confidence']:.4f})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m gulcli.runtime_io")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("path")
    p_validate.add_argument("--format", choices=("text", "json"), default="text")
    p_validate.add_argument("--strict", action="store_true")

    p_infer = sub.add_parser("infer")
    p_infer.add_argument("path")
    p_infer.add_argument("--format", choices=("text", "json"), default="text")
    p_infer.add_argument("--trace", action="store_true")

    args = parser.parse_args(argv)

    if args.cmd == "validate":
        result = validate_file(args.path)
        if args.strict and result["errors"]:
            for error in result["errors"]:
                if error["severity"] == "warning":
                    error["severity"] = "error"
            result["ok"] = False
        return _print_validation(result, as_json=args.format == "json")

    if args.cmd == "infer":
        try:
            result = infer_file(args.path, include_trace=args.trace)
        except Exception as exc:
            payload = {
                "schema": "gul.inference.result/1",
                "version": RUNTIME_VERSION,
                "error": str(exc),
            }
            if args.format == "json":
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        return _print_inference(result, as_json=args.format == "json")

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
