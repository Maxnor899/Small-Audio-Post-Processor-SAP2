"""
Applicability Evaluator - sap2/applicability/evaluator.py

Evaluates decoding method applicability using EXPLICIT thresholds.

ETHICAL PRINCIPLE: Judgment happens HERE, with visible parameters.
                    Builders observe. Evaluator judges.
"""


from dataclasses import dataclass, field
from typing import List

from sap2.model.inputs import InputBundle
from sap2.applicability.params import ApplicabilityParams


@dataclass(frozen=True)
class ApplicabilityReport:
    """
    Result of evaluating a decoding method.
    
    This is a JUDGMENT based on:
    - Method requirements
    - Available inputs
    - Explicit thresholds
    """
    
    method_id: str
    status: str  # "applicable", "missing", "underconstrained"
    required_inputs: List[str]
    missing_inputs: List[str]
    unstable_inputs: List[str]
    diagnostics: List[str] = field(default_factory=list)


def evaluate_applicability(
    method_id: str,
    requires: dict,  # E.g. {'E': 'required', 'Δ': 'required', 'S': 'optional'}
    bundle: InputBundle,
    params: ApplicabilityParams
) -> ApplicabilityReport:
    """
    Evaluate whether a decoding method can be applied.
    
    This is where JUDGMENT happens, using EXPLICIT thresholds from params.
    
    Args:
        method_id: Method identifier
        requires: Dict mapping family -> 'required'/'optional'/'not_applicable'
        bundle: InputBundle with observations
        params: Explicit thresholds
        
    Returns:
        ApplicabilityReport with judgment
        
    Logic:
        1. Check which inputs are required
        2. For each required input:
           - Is it available? (factual check)
           - Is it stable? (judgment using params)
        3. Status:
           - "missing": ≥1 required input unavailable
           - "underconstrained": all available but ≥1 unstable
           - "applicable": all available and stable
    """
    
    # Identify required inputs
    required = [f for f, level in requires.items() if level == 'required']
    
    missing = []
    unstable = []
    diagnostics = []
    
    for family in required:
        inp = bundle.inputs[family]
        
        # Factual check: is input available?
        if not inp.available:
            missing.append(family)
            diagnostics.append(f"{family}: unavailable - {', '.join(inp.notes)}")
            continue
        
        # Judgment check: is input stable? (using EXPLICIT thresholds)
        is_stable, diag = _check_stability(inp, params)
        
        if not is_stable:
            unstable.append(family)
            diagnostics.extend(diag)
    
    # Determine status
    if missing:
        status = "missing"
    elif unstable:
        status = "underconstrained"
    else:
        status = "applicable"
    
    return ApplicabilityReport(
        method_id=method_id,
        status=status,
        required_inputs=required,
        missing_inputs=missing,
        unstable_inputs=unstable,
        diagnostics=diagnostics
    )


def _check_stability(inp, params):
    """
    Check if an input is stable according to thresholds.
    
    This is where THRESHOLDS are applied.
    All thresholds come from params (explicit).
    """
    
    diag = []
    
    # E (Events) stability
    if inp.family == 'E':
        reg = inp.metrics.get('regularity_score', 0.0)
        if reg < params.min_regularity:
            diag.append(
                f"E: low regularity {reg:.3f} < {params.min_regularity}"
            )
            return (False, diag)
    
    # Δ (Intervals) stability
    elif inp.family == 'Δ':
        cv = inp.metrics.get('coefficient_of_variation', 0.0)
        if cv > params.max_cv:
            diag.append(
                f"Δ: high CV {cv:.3f} > {params.max_cv}"
            )
            return (False, diag)
    
    # S (Symbols) stability
    elif inp.family == 'S':
        ratio_short = inp.metrics.get('ratio_short', 0.0)
        ratio_long = inp.metrics.get('ratio_long', 0.0)
        min_ratio = min(ratio_short, ratio_long)
        
        if min_ratio < params.min_symbol_balance:
            diag.append(
                f"S: unbalanced {min_ratio:.3f} < {params.min_symbol_balance}"
            )
            return (False, diag)
    
    # V (Vectors) stability
    elif inp.family == 'V':
        num = int(inp.metrics.get('num_sources', 0))
        if num < params.min_vector_sources:
            diag.append(
                f"V: insufficient sources {num} < {params.min_vector_sources}"
            )
            return (False, diag)
    
    # M (Matrices) stability
    elif inp.family == 'M':
        # Check if using proxies via explicit flag (robust)
        is_proxy_only = inp.metrics.get('is_proxy_only', 0.0) > 0.5
        
        if is_proxy_only:
            # Proxies are NOT equivalent to full TF matrices
            if not params.accept_matrix_proxies:
                # Strict mode: proxies are not acceptable
                diag.append(
                    "M: using time-series proxies only, not full TF matrices "
                    "(set params.accept_matrix_proxies=True to allow)"
                )
                return (False, diag)
            else:
                # Permissive mode: proxies accepted but noted
                diag.append(
                    "M: using time-series proxies (accepted by params.accept_matrix_proxies=True)"
                )
                # Continue, not unstable in this mode
    
    # R (Relations) stability
    elif inp.family == 'R':
        num = int(inp.metrics.get('num_relation_types', 0))
        if num < params.min_relation_types:
            diag.append(
                f"R: insufficient types {num} < {params.min_relation_types}"
            )
            return (False, diag)
    
    return (True, diag)