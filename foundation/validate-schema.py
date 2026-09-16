#!/usr/bin/env python3
"""Validate foundation instances against the repository's JSON Schema catalog."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import FormatChecker, RefResolver, validators


FOUNDATION_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = FOUNDATION_DIR.parent
SCHEMA_PATHS = sorted((FOUNDATION_DIR / "schemas").glob("*.schema.json")) + [
    WORKSPACE_DIR / "portfolio" / "revenue-ledger.schema.json"
]


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def schema_catalog() -> tuple[dict[str, Any], dict[Path, dict[str, Any]]]:
    by_uri: dict[str, Any] = {}
    by_path: dict[Path, dict[str, Any]] = {}

    for path in SCHEMA_PATHS:
        resolved = path.resolve()
        schema = load_json(resolved)
        schema_uri = schema.get("$id")
        if not isinstance(schema_uri, str) or not schema_uri:
            raise ValueError(f"{path}: schema has no non-empty $id")
        if schema_uri in by_uri:
            raise ValueError(f"duplicate schema $id: {schema_uri}")

        validator_class = validators.validator_for(schema)
        validator_class.check_schema(schema)
        by_uri[schema_uri] = schema
        by_path[resolved] = schema

    return by_uri, by_path


def json_pointer(parts: list[Any]) -> str:
    if not parts:
        return "/"
    escaped = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(escaped)


def validate_instance(
    schema: dict[str, Any], instance: Any, label: str, schema_store: dict[str, Any]
) -> bool:
    validator_class = validators.validator_for(schema)
    resolver = RefResolver.from_schema(schema, store=schema_store)
    validator = validator_class(
        schema,
        resolver=resolver,
        format_checker=FormatChecker(),
    )
    errors = sorted(
        validator.iter_errors(instance),
        key=lambda error: [str(part) for part in error.absolute_path],
    )
    for error in errors:
        pointer = json_pointer(list(error.absolute_path))
        print(f"{label}:{pointer}: {error.message}", file=sys.stderr)
    return not errors


def resolve_schema(argument: str, schemas_by_path: dict[Path, dict[str, Any]]) -> dict[str, Any]:
    requested = Path(argument)
    if not requested.is_absolute():
        requested = (Path.cwd() / requested).resolve()
    else:
        requested = requested.resolve()
    try:
        return schemas_by_path[requested]
    except KeyError as error:
        known = ", ".join(str(path.relative_to(WORKSPACE_DIR)) for path in schemas_by_path)
        raise ValueError(f"unknown schema path {argument}; expected one of: {known}") from error


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate one or more JSON instances against a cataloged schema."
    )
    parser.add_argument("schema", help="Path to the root JSON Schema")
    parser.add_argument(
        "instances",
        nargs="+",
        help="JSON instance paths; use - to read one instance from standard input",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        schemas_by_uri, schemas_by_path = schema_catalog()
        schema = resolve_schema(arguments.schema, schemas_by_path)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Schema validation setup failed: {error}", file=sys.stderr)
        return 2

    valid = True
    standard_input_used = False
    for instance_argument in arguments.instances:
        try:
            if instance_argument == "-":
                if standard_input_used:
                    raise ValueError("standard input can be used only once")
                instance = json.load(sys.stdin)
                standard_input_used = True
                label = "stdin"
            else:
                instance_path = Path(instance_argument)
                instance = load_json(instance_path)
                label = str(instance_path)
        except (OSError, json.JSONDecodeError, ValueError) as error:
            print(f"{instance_argument}: could not load JSON: {error}", file=sys.stderr)
            valid = False
            continue

        valid = validate_instance(schema, instance, label, schemas_by_uri) and valid

    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
