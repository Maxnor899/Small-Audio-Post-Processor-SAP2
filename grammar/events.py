"""
Events Builder (E family) - sap2/grammar/builders/events.py

ETHICAL PRINCIPLE: OBSERVE ONLY. Do not judge.
No hidden thresholds. No implicit quality assessment.
"""


from sap2.io.load_sat import SatResults
from sap2.model.inputs import Input, Provenance


def build_events(sat: SatResults, channel: str) -> Input:
    """
    Build E (Events) family from SAT pulse_detection.
    
    Returns Input with:
    - available: True if ≥2 pulses (factual minimum for intervals)
    - data: pulse positions
    - metrics: num_events, regularity_score (FACTUAL, no threshold)
    - provenance: complete traceability
    
    NO JUDGMENT about quality, regularity, spacing.
    All metrics reported factually for downstream evaluator.
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
            family='E',
            available=False,
            data=None,
            provenance=provenance,
            metrics={},
            notes=['pulse_detection not in SAT results']
        )
    
    # Extract data
    positions = pulse.get('pulse_positions', [])
    num_pulses = pulse.get('num_pulses', 0)
    
    # FACTUAL metrics (no thresholds)
    metrics = {
        'num_events': float(num_pulses),
        'regularity_score': float(pulse.get('regularity_score', 0.0)),
        'interval_mean': float(pulse.get('interval_mean', 0.0)),
        'interval_std': float(pulse.get('interval_std', 0.0))
    }
    
    # Factual availability: need ≥2 for intervals
    available = (num_pulses >= 2)
    
    notes = []
    if num_pulses < 2:
        notes.append(f'only {num_pulses} event(s), need ≥2 for intervals')
    
    return Input(
        family='E',
        available=available,
        data={'positions': positions},
        provenance=provenance,
        metrics=metrics,
        notes=notes
    )