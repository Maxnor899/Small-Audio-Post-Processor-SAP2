"""
SAP² Experiment Model - sap2/model/experiment.py

Defines the contract for decoder outputs.

An ExperimentResult represents the outcome of a single, explicit decoding
attempt under fixed parameters. It is an experimental artifact, not an
interpretation or a verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional
from enum import Enum


class ExperimentStatus(str, Enum):
    """
    Outcome status of a decoding attempt.
    """
    SUCCESS = "success"     # decoding procedure executed and produced artifacts
    FAILURE = "failure"     # decoding attempted but failed structurally
    REFUSED = "refused"     # decoding not attempted (missing inputs, unmet preconditions)


@dataclass(frozen=True)
class ExperimentResult:
    """
    Result of a single decoding experiment.

    This object is intentionally factual and non-interpretative.
    It must not claim meaning, intent, or correctness.
    """

    # Identity
    method_id: str
    decoder_version: str

    # Outcome
    status: ExperimentStatus

    # Parameters explicitly used for this run
    parameters_used: Dict[str, Any] = field(default_factory=dict)

    # Structural artifacts produced by the decoder
    # Examples: symbol_stream, bitstream, segment_table, matrices, etc.
    artifacts: Dict[str, Any] = field(default_factory=dict)

    # Factual diagnostics and limitations
    # Examples: threshold values, ambiguities, instability notes
    diagnostics: List[str] = field(default_factory=list)

    # Provenance of inputs actually consumed
    # Usually derived from Input.provenance
    inputs_provenance: Dict[str, Any] = field(default_factory=dict)

    # Optional sensitivity information (parameter-dependence)
    # Example: {"dot_max": "symbol_stream changes significantly"}
    sensitivity: Optional[Dict[str, str]] = None
