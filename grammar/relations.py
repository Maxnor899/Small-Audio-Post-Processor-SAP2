"""
Relations Builder (R family) - sap2/grammar/builders/relations.py

ETHICAL PRINCIPLE: Aggregate all available relations. No judgment.
"""


from sap2.io.load_sat import SatResults
from sap2.model.inputs import Input, Provenance


RELATION_METHODS = [
    'cross_correlation',
    'phase_difference',
    'time_delay',
    'lr_difference'
]


def build_relations(sat: SatResults, channel: str = None) -> Input:
    """
    Build R (Relations) family from inter-channel analyses.
    
    Returns Input with:
    - available: True if ≥1 relation type exists
    - data: aggregated relations
    - metrics: num_relation_types (FACTUAL)
    - provenance: all SAT methods used
    
    NO JUDGMENT about quantity or quality of relations.
    
    Note:
        This builder ALWAYS checks for global relations (pairs like left_vs_right)
        in addition to any channel-specific relations.
        This ensures we don't miss inter-channel data even when a specific
        channel is requested.
    """
    
    relations = {}
    sat_methods = []
    sat_params = {}
    
    for method_name in RELATION_METHODS:
        # Try channel-specific
        data = sat.get_method(method_name, channel)
        
        if data is not None:
            sat_methods.append(method_name)
            params = sat.get_method_metrics(method_name)
            if params:
                sat_params[method_name] = params
            
            relations[method_name] = data
        
        # ALWAYS also check for global pairs
        # (Prevents missing left_vs_right etc. when channel is specified)
        all_data = sat.get_method(method_name)
        if all_data and isinstance(all_data, dict):
            # Check if this has pair-like keys
            has_pairs = any('_vs_' in str(k) for k in all_data.keys())
            
            if has_pairs:
                # Merge instead of overwrite
                if method_name in relations:
                    # Already have channel-specific, merge with global pairs
                    if isinstance(relations[method_name], dict):
                        # Merge: global pairs take precedence only if key not present
                        merged = {**all_data, **relations[method_name]}
                        relations[method_name] = merged
                else:
                    # No channel-specific data yet, use global pairs
                    if method_name not in sat_methods:
                        sat_methods.append(method_name)
                    params = sat.get_method_metrics(method_name)
                    if params:
                        sat_params[method_name] = params
                    
                    relations[method_name] = all_data
    
    provenance = Provenance.create(
        sat_methods=sat_methods,
        sat_params=sat_params,
        builder_version='1.0.0'
    )
    
    # If no relations
    if not relations:
        return Input(
            family='R',
            available=False,
            data=None,
            provenance=provenance,
            metrics={},
            notes=['no inter-channel analyses in SAT results']
        )
    
    # FACTUAL metrics
    num_types = len(relations)
    
    metrics = {
        'num_relation_types': float(num_types)
    }
    
    # Factual availability
    available = (num_types >= 1)
    
    return Input(
        family='R',
        available=available,
        data={'relations': relations},
        provenance=provenance,
        metrics=metrics,
        notes=[f'{num_types} relation type(s)']
    )