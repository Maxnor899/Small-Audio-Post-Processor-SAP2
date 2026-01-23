"""
SAP² Applicability Checks - sap2/applicability/checks.py

Evaluates whether decoding methods can be applied.

JUDGMENT happens HERE with EXPLICIT parameters.
"""

from typing import Dict, List, Tuple

from sap2.model.inputs import InputBundle, Input
from sap2.model.applicability import ApplicabilityReport
from sap2.applicability.matrix import MethodRequirements, ApplicabilityMatrix
from sap2.applicability.params import ApplicabilityParams


def evaluate_applicability(
    method: MethodRequirements,
    bundle: InputBundle,
    params: ApplicabilityParams
) -> ApplicabilityReport:
    """
    Evaluate whether a method can be applied to an InputBundle.
    
    This is where JUDGMENT happens, using EXPLICIT thresholds from params.
    
    Args:
        method: Method requirements (from matrix)
        bundle: InputBundle (rich, from grammar builders)
        params: Explicit threshold parameters
        
    Returns:
        ApplicabilityReport with detailed evaluation
        
    Logic:
        1. Identify required inputs
        2. For each required input:
           - Check if available (factual)
           - Check if stable (judgment with params)
        3. Determine status:
           - missing_inputs: ≥1 required unavailable
           - underconstrained: all available but ≥1 unstable
           - applicable: all available and stable
    """
    
    # Identify required inputs
    required = [
        family for family, level in method.requires.items()
        if level == 'required'
    ]
    
    missing: Dict[str, str] = {}
    unstable: Dict[str, str] = {}
    diagnostics: List[str] = []
    
    for family in required:
        inp = bundle.inputs[family]
        
        # Factual check: is input available?
        if not inp.available:
            reason = ', '.join(inp.notes) if inp.notes else 'unavailable'
            missing[family] = reason
            diagnostics.append(f"{family}: {reason}")
            continue
        
        # Judgment check: is input stable? (using EXPLICIT params)
        is_stable, reason = _check_stability(inp, params)
        
        if not is_stable:
            unstable[family] = reason
            diagnostics.append(f"{family}: {reason}")
    
    # Determine final status
    if missing:
        status = 'missing_inputs'
    elif unstable:
        status = 'underconstrained'
    else:
        status = 'applicable'
    
    # Build provenance
    provenance = {
        'method_source': method.source_file,
        'params_version': '1.0.0',
        'bundle_channel': bundle.channel,
        'thresholds': {
            'min_regularity': params.min_regularity,
            'max_cv': params.max_cv,
            'min_symbol_balance': params.min_symbol_balance,
            'min_vector_sources': params.min_vector_sources,
            'accept_matrix_proxies': params.accept_matrix_proxies,
            'min_relation_types': params.min_relation_types
        }
    }
    
    return ApplicabilityReport(
        method_id=method.method_id,
        family=method.family,
        label=method.label,
        status=status,
        required_inputs=required,
        missing_inputs=missing,
        unstable_inputs=unstable,
        diagnostics=diagnostics,
        provenance=provenance
    )


def _check_stability(inp: Input, params: ApplicabilityParams) -> Tuple[bool, str]:
    """
    Check if an input is stable according to thresholds.
    
    This applies EXPLICIT thresholds from params.
    
    Args:
        inp: Input to check
        params: Threshold parameters
        
    Returns:
        (is_stable, reason) tuple
        - is_stable: True if passes all thresholds
        - reason: Explanation if unstable (empty if stable)
    """
    
    family = inp.family
    metrics = inp.metrics
    
    # E (Events) stability
    if family == 'E':
        regularity = metrics.get('regularity_score', 0.0)
        if regularity < params.min_regularity:
            return (False, f"low regularity {regularity:.3f} < {params.min_regularity}")
    
    # Δ (Intervals) stability
    elif family == 'Δ':
        cv = metrics.get('coefficient_of_variation', 0.0)
        if cv > params.max_cv:
            return (False, f"high CV {cv:.3f} > {params.max_cv}")
    
    # S (Symbols) stability
    elif family == 'S':
        ratio_short = metrics.get('ratio_short', 0.0)
        ratio_long = metrics.get('ratio_long', 0.0)
        min_ratio = min(ratio_short, ratio_long)
        
        if min_ratio < params.min_symbol_balance:
            return (False, f"unbalanced {min_ratio:.3f} < {params.min_symbol_balance}")
    
    # V (Vectors) stability
    elif family == 'V':
        num_sources = int(metrics.get('num_sources', 0))
        if num_sources < params.min_vector_sources:
            return (False, f"insufficient sources {num_sources} < {params.min_vector_sources}")
    
    # M (Matrices) stability
    elif family == 'M':
        is_proxy_only = metrics.get('is_proxy_only', 0.0) > 0.5
        
        if is_proxy_only and not params.accept_matrix_proxies:
            return (False, "using proxies only (set accept_matrix_proxies=True to allow)")
    
    # R (Relations) stability
    elif family == 'R':
        num_types = int(metrics.get('num_relation_types', 0))
        if num_types < params.min_relation_types:
            return (False, f"insufficient types {num_types} < {params.min_relation_types}")
    
    # If we get here, input is stable
    return (True, '')


def evaluate_all_methods(
    matrix: ApplicabilityMatrix,
    bundle: InputBundle,
    params: ApplicabilityParams
) -> Dict[str, ApplicabilityReport]:
    """
    Evaluate all methods in the matrix.
    
    Helper function to evaluate the entire matrix at once.
    
    Args:
        matrix: Complete applicability matrix
        bundle: InputBundle (rich)
        params: Threshold parameters
        
    Returns:
        Dict mapping method_id → ApplicabilityReport
    """
    
    reports = {}
    
    for method_id, method in matrix.methods.items():
        reports[method_id] = evaluate_applicability(method, bundle, params)
    
    return reports


def filter_applicable(
    reports: Dict[str, ApplicabilityReport]
) -> Dict[str, ApplicabilityReport]:
    """
    Filter to only applicable methods.
    
    Args:
        reports: All reports
        
    Returns:
        Only reports with status='applicable'
    """
    return {
        mid: report 
        for mid, report in reports.items() 
        if report.status == 'applicable'
    }