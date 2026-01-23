"""
SAP² Engine Pipeline - sap2/engine/pipeline.py

Minimal orchestration:
- load SAT results
- build InputBundle(s) for all channels
- load applicability matrix (multi-file YAML)
- evaluate applicability for all methods
- run decoders for applicable methods only

No heuristics, no retries, no parameter scanning here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from sap2.io.load_sat import SatResults
from sap2.grammar.bundle_builder import build_all_channels

from sap2.applicability.matrix_loader import load_applicability_matrix
from sap2.applicability.params import ApplicabilityParams
from sap2.applicability.checks import evaluate_all_methods, filter_applicable

from sap2.decoders.registry import get_decoder
from sap2.decoders.base import DecoderParams, refused

from sap2.model.applicability import ApplicabilityReport
from sap2.model.experiment import ExperimentResult


@dataclass(frozen=True)
class PipelineChannelResult:
    channel: str
    applicability: Dict[str, ApplicabilityReport] = field(default_factory=dict)
    experiments: Dict[str, ExperimentResult] = field(default_factory=dict)


@dataclass(frozen=True)
class PipelineRunResult:
    sat_source: str
    matrix_schema_version: str
    channels: Dict[str, PipelineChannelResult] = field(default_factory=dict)


def run_pipeline(
    sat_path: Path | str,
    matrices_dir: Path | str,
    applicability_params: ApplicabilityParams,
    decoder_params_by_method: Optional[Mapping[str, Mapping[str, Any]]] = None,
    *,
    channels: Optional[list[str]] = None,
) -> PipelineRunResult:
    """
    Run SAP² end-to-end pipeline.

    Args:
        sat_path:
            Path to SAT results.json (or any path accepted by SatResults.load).
        matrices_dir:
            Directory containing _index.yaml, matrix.schema.json, and domain YAMLs.
        applicability_params:
            Explicit thresholds used by applicability checks.
        decoder_params_by_method:
            Optional mapping: method_id -> params dict (explicit).
        channels:
            Optional allow-list of channel names to run (e.g. ["left", "right"]).
            If None: run all channels produced by build_all_channels().

    Returns:
        PipelineRunResult containing applicability reports and experiment results per channel.
    """
    sat = SatResults.load(sat_path)
    matrix = load_applicability_matrix(matrices_dir)

    bundles_by_channel = build_all_channels(sat)

    if channels is not None:
        allow = set(channels)
        bundles_by_channel = {ch: b for ch, b in bundles_by_channel.items() if ch in allow}

    decoder_params_by_method = decoder_params_by_method or {}

    out_channels: Dict[str, PipelineChannelResult] = {}

    for channel_name, bundle in bundles_by_channel.items():
        reports = evaluate_all_methods(matrix=matrix, bundle=bundle, params=applicability_params)
        applicable = filter_applicable(reports)

        experiments: Dict[str, ExperimentResult] = {}

        for method_id in applicable.keys():
            dec = get_decoder(method_id)

            if dec is None:
                # Not implemented is not an error; represent as a factual refusal.
                experiments[method_id] = refused(
                    method_id=method_id,
                    version="registry",
                    reason=f"Decoder not implemented for method_id '{method_id}'.",
                )
                continue

            raw_params = decoder_params_by_method.get(method_id, {})
            params = DecoderParams(values=dict(raw_params))

            experiments[method_id] = dec.decode(bundle=bundle, params=params)

        out_channels[channel_name] = PipelineChannelResult(
            channel=channel_name,
            applicability=reports,
            experiments=experiments,
        )

    # SatResults has .source_path in your implementation; fallback is the input path string.
    sat_source = str(getattr(sat, "source_path", sat_path))
    matrix_schema_version = str(getattr(matrix, "schema_version", ""))

    return PipelineRunResult(
        sat_source=sat_source,
        matrix_schema_version=matrix_schema_version,
        channels=out_channels,
    )
