"""
Intervals Builder (Δ family) - sap2/grammar/builders/intervals.py

ETHICAL PRINCIPLE: OBSERVE ONLY. Do not judge.
"""

import numpy as np

from sap2.io.load_sat import SatResults
from sap2.model.inputs import Input, Provenance


def build_intervals(sat: SatResults, channel: str) -> Input:
    """
    Build Δ (Intervals) family from SAT pulse_detection.
    
    Returns Input with:
    - available: True if ≥1 interval exists
    - data: computed intervals
    - metrics: mean, std, cv (FACTUAL, no threshold)
    - provenance: complete traceability
    
    NO JUDGMENT about variability, regularity, stability.
    CV (coefficient of variation) is reported as FACTUAL metric.
    """
    
    pulse = sat.get_method('pulse_detection', channel)
    
    # Build provenance
    sat_methods = []
    sat_params = {}
    
    if pulse is not None:
        sat_methods.append('pulse_detection')
        params = sat.get_method_metrics('pulse_detection')
        if params:
            sat_params['pulse_detection'] = params
    
    provenance = Provenance.create(
        sat_methods=sat_methods,
        sat_params=sat_params,
        builder_version='1.0.0'
    )
    
    # If method not run
    if pulse is None:
        return Input(
            family='Δ',
            available=False,
            data=None,
            provenance=provenance,
            metrics={},
            notes=['pulse_detection not in SAT results']
        )
    
    # Extract positions
    positions = pulse.get('pulse_positions', [])
    
    if len(positions) < 2:
        return Input(
            family='Δ',
            available=False,
            data=None,
            provenance=provenance,
            metrics={'num_events': float(len(positions))},
            notes=[f'only {len(positions)} event(s), need ≥2']
        )
    
    # Compute intervals
    intervals = np.diff(positions)
    
    # FACTUAL metrics (no thresholds)
    mean = float(np.mean(intervals))
    std = float(np.std(intervals))
    cv = std / mean if mean > 0 else 0.0  # Factual metric, not a judgment
    
    metrics = {
        'num_intervals': float(len(intervals)),
        'interval_mean': mean,
        'interval_std': std,
        'interval_min': float(np.min(intervals)),
        'interval_max': float(np.max(intervals)),
        'coefficient_of_variation': cv
    }
    
    # Factual availability
    available = (len(intervals) >= 1)
    
    return Input(
        family='Δ',
        available=available,
        data={'intervals': intervals.tolist()},
        provenance=provenance,
        metrics=metrics,
        notes=[]
    )