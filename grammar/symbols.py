"""
Symbols Builder (S family) - sap2/grammar/builders/symbols.py

ETHICAL PRINCIPLE: Discretization is EXPLICIT and DOCUMENTED.
No hidden judgment on distribution balance.
"""

import numpy as np

from sap2.io.load_sat import SatResults
from sap2.model.inputs import Input, Provenance


def build_symbols(sat: SatResults, channel: str) -> Input:
    """
    Build S (Symbols) family by discretizing intervals.
    
    Discretization method: median threshold, binary alphabet.
    This method is EXPLICIT and documented in provenance.
    
    Returns Input with:
    - available: True if ≥2 symbols (from ≥3 events)
    - data: symbol sequence + alphabet
    - metrics: symbol_entropy, ratio_short, ratio_long (FACTUAL)
    - provenance: includes discretization method
    
    NO JUDGMENT about distribution balance.
    Ratios reported factually for downstream evaluator.
    """
    
    pulse = sat.get_method('pulse_detection', channel)
    
    # Build provenance (includes discretization params)
    sat_methods = []
    sat_params = {}
    
    if pulse is not None:
        sat_methods.append('pulse_detection')
        params = sat.get_method_metrics('pulse_detection')
        if params:
            sat_params['pulse_detection'] = params
    
    # Document discretization method
    sat_params['discretization'] = {
        'method': 'median_threshold',
        'alphabet': ['short', 'long']
    }
    
    provenance = Provenance.create(
        sat_methods=sat_methods,
        sat_params=sat_params,
        builder_version='1.0.0'
    )
    
    # If method not run
    if pulse is None:
        return Input(
            family='S',
            available=False,
            data=None,
            provenance=provenance,
            metrics={},
            notes=['pulse_detection not in SAT results']
        )
    
    # Need ≥3 events (2+ intervals)
    positions = pulse.get('pulse_positions', [])
    
    if len(positions) < 3:
        return Input(
            family='S',
            available=False,
            data=None,
            provenance=provenance,
            metrics={'num_events': float(len(positions))},
            notes=[f'only {len(positions)} events, need ≥3']
        )
    
    # Compute intervals and discretize
    intervals = np.diff(positions)
    threshold = float(np.median(intervals))
    
    alphabet = ['short', 'long']
    symbols = [alphabet[0] if i < threshold else alphabet[1] for i in intervals]
    
    # FACTUAL distribution metrics (no judgment)
    short_count = symbols.count('short')
    long_count = symbols.count('long')
    total = len(symbols)
    
    # Shannon entropy (factual)
    p_short = short_count / total if total > 0 else 0
    p_long = long_count / total if total > 0 else 0
    
    entropy = 0.0
    if p_short > 0:
        entropy += -p_short * np.log2(p_short)
    if p_long > 0:
        entropy += -p_long * np.log2(p_long)
    
    metrics = {
        'num_symbols': float(len(symbols)),
        'symbol_entropy': float(entropy),
        'ratio_short': p_short,
        'ratio_long': p_long,
        'discretization_threshold': threshold
    }
    
    # Factual availability
    available = (len(symbols) >= 2)
    
    return Input(
        family='S',
        available=available,
        data={
            'symbols': symbols,
            'alphabet': alphabet,
            'threshold': threshold
        },
        provenance=provenance,
        metrics=metrics,
        notes=[]
    )