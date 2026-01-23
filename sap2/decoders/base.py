"""
SAP² Decoder Base - sap2/decoders/base.py

Defines the decoder interface for SAP².

A Decoder is a structural transformer:
- It consumes an InputBundle plus explicit parameters.
- It produces an ExperimentResult.
- It must not infer meaning or intent.
- It must not decide applicability (handled upstream).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Protocol, runtime_checkable

from sap2.model.inputs import InputBundle
from sap2.model.experiment import ExperimentResult, ExperimentStatus


@dataclass(frozen=True)
class DecoderParams:
    """
    Wrapper for decoder parameters.

    Decoders must treat all parameters as explicit.
    No hidden defaults beyond what is declared in the decoder itself.
    """
    values: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def require(self, key: str) -> Any:
        if key not in self.values:
            raise KeyError(f"Missing required decoder parameter: '{key}'")
        return self.values[key]


@runtime_checkable
class Decoder(Protocol):
    """
    Decoder interface.

    Each decoder implements exactly one method_id (the one used in the applicability matrix).
    """

    method_id: str
    version: str

    def decode(self, bundle: InputBundle, params: DecoderParams) -> ExperimentResult:
        """
        Perform a single decoding attempt with fixed parameters.

        The decoder may refuse if strict preconditions are not met, even when the
        method is "applicable" at the family level. Example: expects a specific
        field in Input.data that is missing.

        Returns:
            ExperimentResult with status:
              - SUCCESS: artifacts produced
              - FAILURE: attempted but structurally failed
              - REFUSED: not attempted due to unmet preconditions
        """
        ...


def refused(method_id: str, version: str, reason: str) -> ExperimentResult:
    """
    Helper to create a standardized REFUSED result.
    """
    return ExperimentResult(
        method_id=method_id,
        decoder_version=version,
        status=ExperimentStatus.REFUSED,
        diagnostics=[reason],
    )


def failure(method_id: str, version: str, reason: str) -> ExperimentResult:
    """
    Helper to create a standardized FAILURE result.
    """
    return ExperimentResult(
        method_id=method_id,
        decoder_version=version,
        status=ExperimentStatus.FAILURE,
        diagnostics=[reason],
    )
