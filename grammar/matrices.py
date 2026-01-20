"""
Matrices Builder (M family) - sap2/grammar/builders/matrices.py

ETHICAL PRINCIPLE: Document limitations explicitly.

KNOWN LIMITATION: SAT results.json does not include full TF matrices.
This is documented in provenance and notes.
"""


from sap2.io.load_sat import SatResults
from sap2.model.inputs import Input, Provenance


def build_matrices(sat: SatResults, channel: str) -> Input:
    """
    Build M (Matrices) family from time-frequency analyses.
    
    LIMITATION: SAT results.json does not export visualization_data.
    We use time-series proxies (local_entropy, band_stability, stft stats).
    
    This limitation is DOCUMENTED in provenance.
    
    Returns Input with:
    - available: True if ≥1 proxy exists
    - data: time-series proxies (not full matrices)
    - metrics: num_proxies (FACTUAL)
    - provenance: includes limitation documentation
    """
    
    proxies = {}
    sat_methods = []
    sat_params = {}
    
    # Local entropy (time-indexed)
    local_ent = sat.get_method('local_entropy', channel)
    if local_ent:
        sat_methods.append('local_entropy')
        params = sat.get_method_metrics('local_entropy')
        if params:
            sat_params['local_entropy'] = params
        
        proxies['local_entropy'] = {
            'type': 'time_series',
            'num_windows': local_ent.get('num_windows', 0)
        }
    
    # Band stability (frequency bands × time)
    band_stab = sat.get_method('band_stability', channel)
    if band_stab and isinstance(band_stab, dict):
        sat_methods.append('band_stability')
        params = sat.get_method_metrics('band_stability')
        if params:
            sat_params['band_stability'] = params
        
        proxies['band_stability'] = {
            'type': 'band_summary',
            'num_bands': len(band_stab)
        }
    
    # STFT stats (not the full matrix)
    stft = sat.get_method('stft', channel)
    if stft:
        sat_methods.append('stft')
        params = sat.get_method_metrics('stft')
        if params:
            sat_params['stft'] = params
        
        proxies['stft_stats'] = {
            'type': 'matrix_statistics',
            'num_time_frames': stft.get('num_time_frames'),
            'num_freq_bins': stft.get('num_freq_bins')
        }
    
    # Document limitation in provenance
    sat_params['LIMITATION'] = {
        'type': 'no_full_matrices',
        'reason': 'SAT results.json does not export visualization_data',
        'strategy': 'using time-series proxies'
    }
    
    provenance = Provenance.create(
        sat_methods=sat_methods,
        sat_params=sat_params,
        builder_version='1.0.0'
    )
    
    # If no proxies
    if not proxies:
        return Input(
            family='M',
            available=False,
            data=None,
            provenance=provenance,
            metrics={},
            notes=[
                'no time-frequency data',
                'LIMITATION: full matrices not in SAT results'
            ]
        )
    
    # FACTUAL metrics
    num_proxies = len(proxies)
    
    metrics = {
        'num_proxies': float(num_proxies),
        'is_proxy_only': 1.0  # Explicit flag: not full TF matrices
    }
    
    # Factual availability
    available = (num_proxies >= 1)
    
    return Input(
        family='M',
        available=available,
        data={'proxies': proxies},
        provenance=provenance,
        metrics=metrics,
        notes=[
            f'{num_proxies} time-series proxy/proxies',
            'LIMITATION: proxies only, not full TF matrices'
        ]
    )