"""
sap2/render/json.py

JSON rendering for SAP² outputs.

Presentation-only:
- No applicability logic
- No decoding logic
- No heuristics

Provides robust serialization for dataclasses, enums, and common containers.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence


def to_jsonable(obj: Any) -> Any:
    """
    Convert SAP² objects into JSON-serializable structures.
    Conservative: transforms representation only.
    """
    if obj is None:
        return None

    if isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, Path):
        return str(obj)

    if isinstance(obj, Enum):
        return obj.value

    if is_dataclass(obj):
        # asdict converts nested dataclasses to dict/list, but may keep Enums; post-process recursively.
        return to_jsonable(asdict(obj))

    if isinstance(obj, Mapping):
        return {str(k): to_jsonable(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]

    if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray)):
        return [to_jsonable(v) for v in obj]

    # Last-resort fallback: explicit string representation
    return str(obj)


def write_json(path: str | Path, payload: Any, *, indent: int = 2) -> Path:
    """
    Write payload to path as JSON.
    Returns the resolved output path.
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    data = to_jsonable(payload)

    with out.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent, sort_keys=True)

    return out.resolve()


def write_json_bundle(output_dir: str | Path, name: str, payload: Any, *, indent: int = 2) -> Path:
    """
    Convenience helper: writes <output_dir>/<name>.json
    """
    output_dir = Path(output_dir)
    return write_json(output_dir / f"{name}.json", payload, indent=indent)
