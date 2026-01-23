from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional

from sap2.applicability.params import ApplicabilityParams
from sap2.engine.pipeline import PipelineRunResult, run_pipeline
from sap2.render.json import write_json_bundle
from sap2.render.markdown import render_pipeline_run, write_markdown


def run_and_export(
    sat_path: str | Path,
    matrices_dir: str | Path,
    params: ApplicabilityParams,
    out_dir: str | Path,
    *,
    decoder_params_by_method: Optional[Mapping[str, Mapping[str, Any]]] = None,
    channels: Optional[list[str]] = None,
    report_title: str = "SAP² Report",
) -> PipelineRunResult:
    run = run_pipeline(
        sat_path=sat_path,
        matrices_dir=matrices_dir,
        applicability_params=params,
        decoder_params_by_method=decoder_params_by_method,
        channels=channels,
    )

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    write_json_bundle(out_dir, "pipeline_run", run)

    md = render_pipeline_run(run, title=report_title)
    write_markdown(out_dir / "report.md", md)

    return run
