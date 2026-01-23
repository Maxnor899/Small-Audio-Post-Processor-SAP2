#!/usr/bin/env python3
"""
SAP² entry point.

Runs the SAP² pipeline end-to-end and exports results
(JSON + Markdown).
"""

import argparse
from pathlib import Path

from sap2.applicability.params import ApplicabilityParams
from sap2.engine.export import run_and_export


def main() -> None:
    parser = argparse.ArgumentParser(description="SAP² - Small Audio Post-Processor")
    parser.add_argument(
        "sat_path",
        type=Path,
        help="Path to results.json or SAT output directory"
    )
    parser.add_argument(
        "--channels",
        type=str,
        default="left,right",
        help="Comma-separated list of channels to process (default: left,right)"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory (default: ./sap2_out)"
    )
    parser.add_argument(
        "--min-regularity",
        type=float,
        default=0.1,
        help="Minimum regularity score for events (default: 0.1)"
    )
    parser.add_argument(
        "--max-cv",
        type=float,
        default=1.0,
        help="Maximum coefficient of variation for intervals (default: 1.0)"
    )
    parser.add_argument(
        "--accept-matrix-proxies",
        action="store_true",
        help="Accept time-series proxies as matrix inputs"
    )
    
    args = parser.parse_args()
    
    # --- Paths ---
    sat_path = args.sat_path
    
    # Matrices directory is in the package
    matrices_dir = Path(__file__).parent / "sap2" / "applicability" / "matrices"
    
    # Output directory
    out_dir = args.out if args.out else Path.cwd() / "sap2_out"
    
    # Channels
    channels = [ch.strip() for ch in args.channels.split(",")]
    
    # --- Applicability parameters ---
    params = ApplicabilityParams(
        min_regularity=args.min_regularity,
        max_cv=args.max_cv,
        min_symbol_balance=0.2,
        min_vector_sources=3,
        min_matrix_windows=10,
        accept_matrix_proxies=args.accept_matrix_proxies,
        min_relation_types=1,
    )

    # --- Optional decoder parameters ---
    decoder_params_by_method = {
        # "duration_based_morse_like": {
        #     "dot_max": 0.12,
        #     "dash_min": 0.20,
        # }
    }

    run_and_export(
        sat_path=sat_path,
        matrices_dir=matrices_dir,
        params=params,
        out_dir=out_dir,
        decoder_params_by_method=decoder_params_by_method,
        report_title="SAP² Analysis Report",
        channels=channels,
    )


if __name__ == "__main__":
    main()