"""
Applicability Parameters - sap2/applicability/params.py

EXPLICIT, DOCUMENTED, OVERRIDABLE thresholds.

ETHICAL PRINCIPLE: All heuristics are visible, not hidden in code.
"""

from dataclasses import dataclass


@dataclass
class ApplicabilityParams:
    """
    Explicit thresholds for applicability evaluation.
    
    These parameters define what "good enough" means.
    They are:
    - EXPLICIT (not hidden)
    - DOCUMENTED (with rationale)
    - OVERRIDABLE (user can adjust)
    - VERSIONED (for reproducibility)
    """
    
    # Events (E)
    min_regularity: float = 0.1
    """
    Minimum regularity_score for events.
    - 0.0 = completely irregular
    - 1.0 = perfectly regular
    - Default: 0.1 (very permissive)
    """
    
    # Intervals (Δ)
    max_cv: float = 1.0
    """
    Maximum coefficient of variation (std/mean) for intervals.
    - CV = 0.0 = no variation
    - CV = 1.0 = std equals mean
    - Default: 1.0 (permits high variability)
    """
    
    # Symbols (S)
    min_symbol_balance: float = 0.2
    """
    Minimum ratio of minority symbol class.
    - If < 0.2, distribution is very unbalanced
    - Default: 0.2 (at least 20% each)
    """
    
    # Vectors (V)
    min_vector_sources: int = 3
    """
    Minimum number of independent vector sources.
    - More sources = better coverage
    - Default: 3 (moderate requirement)
    """
    
    # Matrices (M)
    min_matrix_windows: int = 10
    """
    Minimum number of time windows for matrix proxies.
    - Relevant for local_entropy
    - Default: 10
    """
    
    accept_matrix_proxies: bool = False
    """
    Whether to accept time-series proxies as matrix inputs.
    
    SAT results.json does not include full TF matrices (visualization_data).
    Instead, we get proxies: local_entropy, band_stability, stft stats.
    
    - If False (default): methods requiring M will be underconstrained
    - If True: proxies are accepted (but limitation noted)
    
    Rationale:
        Full TF matrices and proxies are NOT equivalent.
        Methods expecting M(t,f) matrices may not work with proxies.
        Default is strict (False) to avoid false applicability.
    """
    
    # Relations (R)
    min_relation_types: int = 1
    """
    Minimum number of relation types.
    - Types: xcorr, phase, delay, lr_diff
    - Default: 1 (any relation is sufficient)
    """