"""
Vectors Builder (V family) - sap2/grammar/builders/vectors.py

ETHICAL PRINCIPLE: Aggregate all available sources. No judgment on quantity.
"""


from sap2.io.load_sat import SatResults
from sap2.model.inputs import Input, Provenance


# Explicit mapping of SAT methods to vector features
VECTOR_SOURCES = {
    'shannon_entropy': ['shannon_entropy', 'normalized_entropy'],
    'local_entropy': ['mean_entropy', 'std_entropy'],
    'compression_ratio': ['compression_ratio'],
    'am_detection': ['modulation_depth', 'modulation_index'],
    'fm_detection': ['frequency_deviation'],
    'fft_global': ['peak_frequency', 'spectral_energy'],
    'peak_detection': ['num_peaks'],
    'spectral_centroid': ['centroid_mean'],
    'spectral_bandwidth': ['bandwidth_mean'],
    'spectral_flatness': ['flatness_mean'],
    'band_stability': ['stability'],
    'harmonic_analysis': ['harmonic_ratio']
}


def build_vectors(sat: SatResults, channel: str) -> Input:
    """
    Build V (Vectors) family from statistical/spectral analyses.
    
    Returns Input with:
    - available: True if ≥1 vector source exists
    - data: aggregated vector features
    - metrics: num_sources (FACTUAL, no threshold)
    - provenance: all SAT methods used
    
    NO JUDGMENT about quantity or diversity of sources.
    Number of sources reported factually.
    """
    
    # Collect all available vectors
    vectors = {}
    sat_methods = []
    sat_params = {}
    
    for method_name in VECTOR_SOURCES.keys():
        data = sat.get_method(method_name, channel)
        
        if data is not None:
            sat_methods.append(method_name)
            params = sat.get_method_metrics(method_name)
            if params:
                sat_params[method_name] = params
            
            vectors[method_name] = data
    
    provenance = Provenance.create(
        sat_methods=sat_methods,
        sat_params=sat_params,
        builder_version='1.0.0'
    )
    
    # If no vectors
    if not vectors:
        return Input(
            family='V',
            available=False,
            data=None,
            provenance=provenance,
            metrics={},
            notes=['no vector analyses in SAT results']
        )
    
    # FACTUAL metrics (no thresholds)
    num_sources = len(vectors)
    num_features = sum(len(v) for v in vectors.values() if isinstance(v, dict))
    
    metrics = {
        'num_sources': float(num_sources),
        'num_features': float(num_features)
    }
    
    # Factual availability
    available = (num_sources >= 1)
    
    return Input(
        family='V',
        available=available,
        data={'vectors': vectors},
        provenance=provenance,
        metrics=metrics,
        notes=[f'{num_sources} vector source(s)']
    )