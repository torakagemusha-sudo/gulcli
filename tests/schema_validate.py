"""Minimal JSON schema checks without external dependencies."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMAS = Path(__file__).resolve().parents[1] / "schemas"


def load_schema(name: str) -> dict[str, Any]:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def validate_against_schema(data: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []

    if "const" in schema and data != schema["const"]:
        return [f"{path}: expected const {schema['const']!r}, got {data!r}"]

    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        if not any(_matches_type(data, t) for t in schema_type):
            errors.append(f"{path}: expected one of types {schema_type}")
        schema_type = None

    if schema_type == "object":
        if not isinstance(data, dict):
            return [f"{path}: expected object"]
        for key in schema.get("required", []):
            if key not in data:
                errors.append(f"{path}: missing required field {key!r}")
        props = schema.get("properties", {})
        for key, subschema in props.items():
            if key in data:
                errors.extend(validate_against_schema(data[key], subschema, f"{path}.{key}"))
    elif schema_type == "array":
        if not isinstance(data, list):
            return [f"{path}: expected array"]
        item_schema = schema.get("items", {})
        for i, item in enumerate(data):
            errors.extend(validate_against_schema(item, item_schema, f"{path}[{i}]"))
    elif schema_type == "string":
        if not isinstance(data, str):
            errors.append(f"{path}: expected string")
        enum = schema.get("enum")
        if enum is not None and data not in enum:
            errors.append(f"{path}: expected one of {enum}, got {data!r}")
        min_length = schema.get("minLength")
        if min_length is not None and isinstance(data, str) and len(data) < min_length:
            errors.append(f"{path}: string shorter than minLength {min_length}")
    elif schema_type == "boolean":
        if not isinstance(data, bool):
            errors.append(f"{path}: expected boolean")
    elif schema_type == "number":
        if not isinstance(data, (int, float)) or isinstance(data, bool):
            errors.append(f"{path}: expected number")
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if isinstance(data, (int, float)):
            if minimum is not None and data < minimum:
                errors.append(f"{path}: below minimum {minimum}")
            if maximum is not None and data > maximum:
                errors.append(f"{path}: above maximum {maximum}")

    return errors


def _matches_type(data: Any, schema_type: str) -> bool:
    if schema_type == "string":
        return isinstance(data, str)
    if schema_type == "null":
        return data is None
    if schema_type == "number":
        return isinstance(data, (int, float)) and not isinstance(data, bool)
    if schema_type == "boolean":
        return isinstance(data, bool)
    if schema_type == "object":
        return isinstance(data, dict)
    if schema_type == "array":
        return isinstance(data, list)
    return False
