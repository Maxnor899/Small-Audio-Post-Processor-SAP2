"""
sap2/applicability/matrix_loader.py

Loads and validates the applicability matrix YAML files declared in _index.yaml,
using matrix.schema.json.

This module is a PURE LOADER:
- no applicability judgment
- no thresholds
- no duplication of model types

Types are defined in:
- sap2.applicability.matrix
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

import json
import yaml
from jsonschema import Draft202012Validator

from sap2.applicability.matrix import (
    ApplicabilityMatrix,
    MethodRequirements,
    INPUT_FAMILIES,
)


class MatrixLoadError(RuntimeError):
    """Raised when the applicability matrix cannot be loaded or validated."""


def load_applicability_matrix(matrices_dir: Path | str) -> ApplicabilityMatrix:
    """
    matrices_dir: directory containing:
      - _index.yaml
      - matrix.schema.json
      - <family>.yaml files (time_domain.yaml, frequency_domain.yaml, ...)
    """
    matrices_dir = Path(matrices_dir)

    if not matrices_dir.exists() or not matrices_dir.is_dir():
        raise MatrixLoadError(f"matrices_dir does not exist or is not a directory: {matrices_dir}")

    index_path = matrices_dir / "_index.yaml"
    schema_path = matrices_dir / "matrix.schema.json"

    if not index_path.exists():
        raise MatrixLoadError(f"Missing required index file: {index_path}")
    if not schema_path.exists():
        raise MatrixLoadError(f"Missing required schema file: {schema_path}")

    index_doc = _read_yaml(index_path)
    schema_doc = _read_json(schema_path)

    _validate_index(index_doc, index_path)

    # Contract check: ensure index and code agree on the canonical family list
    index_families = index_doc["input_families"]
    if list(index_families) != list(INPUT_FAMILIES):
        raise MatrixLoadError(
            f"{index_path}: input_families mismatch.\n"
            f"- index: {index_families}\n"
            f"- code : {INPUT_FAMILIES}"
        )

    matrices_entries = index_doc["matrices"]
    schema_version = str(index_doc.get("schema_version", "1.0")).strip() or "1.0"

    methods: Dict[str, MethodRequirements] = {}

    for entry in matrices_entries:
        file_name = entry["file"]
        family_expected = entry["family"]

        doc_path = matrices_dir / file_name
        if not doc_path.exists():
            raise MatrixLoadError(f"Matrix file referenced in _index.yaml not found: {doc_path}")

        doc = _read_yaml(doc_path)
        _validate_against_schema(schema_doc, doc, doc_path)

        family_in_doc = doc.get("family")
        if family_in_doc != family_expected:
            raise MatrixLoadError(
                f"Family mismatch for {doc_path}: index says '{family_expected}' "
                f"but file says '{family_in_doc}'"
            )

        doc_methods = doc.get("methods")
        if not isinstance(doc_methods, dict) or not doc_methods:
            raise MatrixLoadError(f"{doc_path}: 'methods' must be a non-empty object")

        for method_id, spec in doc_methods.items():
            if method_id in methods:
                prev = methods[method_id].source_file
                raise MatrixLoadError(
                    f"Duplicate method_id '{method_id}' found in {doc_path} "
                    f"(already defined in {prev})"
                )

            label = spec["label"]
            requires = spec["requires"]

            methods[method_id] = MethodRequirements(
                method_id=method_id,
                family=family_expected,
                label=label,
                requires=requires,
                source_file=str(doc_path.name),  # keep it short; change to str(doc_path) if you prefer
            )

    return ApplicabilityMatrix(schema_version=schema_version, methods=methods)


def _read_yaml(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        raise MatrixLoadError(f"Failed to read YAML: {path} ({e})") from e

    if not isinstance(data, dict):
        raise MatrixLoadError(f"YAML root must be a mapping/object: {path}")

    return data


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise MatrixLoadError(f"Failed to read JSON: {path} ({e})") from e


def _validate_against_schema(schema: Dict[str, Any], doc: Dict[str, Any], doc_path: Path) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: e.path)

    if errors:
        lines: List[str] = [f"Schema validation failed for: {doc_path}"]
        for err in errors[:20]:
            loc = ".".join([str(p) for p in err.absolute_path]) or "<root>"
            lines.append(f"- {loc}: {err.message}")
        if len(errors) > 20:
            lines.append(f"... and {len(errors) - 20} more error(s)")
        raise MatrixLoadError("\n".join(lines))


def _validate_index(index_doc: Mapping[str, Any], index_path: Path) -> None:
    # Minimal validation. We can add index.schema.json later if you want, but keep it explicit.
    if "schema_version" not in index_doc:
        raise MatrixLoadError(f"{index_path}: missing required key 'schema_version'")
    if not isinstance(index_doc["schema_version"], str) or not index_doc["schema_version"].strip():
        raise MatrixLoadError(f"{index_path}: 'schema_version' must be a non-empty string")

    if "input_families" not in index_doc:
        raise MatrixLoadError(f"{index_path}: missing required key 'input_families'")
    if not isinstance(index_doc["input_families"], list) or not index_doc["input_families"]:
        raise MatrixLoadError(f"{index_path}: 'input_families' must be a non-empty list")
    for i, fam in enumerate(index_doc["input_families"]):
        if not isinstance(fam, str) or not fam.strip():
            raise MatrixLoadError(f"{index_path}: input_families[{i}] must be a non-empty string")

    matrices_entries = index_doc.get("matrices")
    if not isinstance(matrices_entries, list) or not matrices_entries:
        raise MatrixLoadError(f"{index_path}: 'matrices' must be a non-empty list")

    for i, entry in enumerate(matrices_entries):
        if not isinstance(entry, dict):
            raise MatrixLoadError(f"{index_path}: matrices[{i}] must be an object")

        file_name = entry.get("file")
        family = entry.get("family")

        if not isinstance(file_name, str) or not file_name.strip():
            raise MatrixLoadError(f"{index_path}: matrices[{i}].file must be a non-empty string")
        if not isinstance(family, str) or not family.strip():
            raise MatrixLoadError(f"{index_path}: matrices[{i}].family must be a non-empty string")
