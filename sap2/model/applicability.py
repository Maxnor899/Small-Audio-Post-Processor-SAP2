"""
Applicability Model - sap2/model/applicability.py

Defines the output contract for applicability evaluation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class ApplicabilityReport:
    """
    Structural applicability report for a single decoding method.
    
    This is the OUTPUT of applicability evaluation.
    It documents whether a method can be attempted, and why.
    
    Attributes:
        method_id: Unique method identifier
        family: Method family (e.g. 'time_domain', 'frequency_domain')
        label: Human-readable method name
        status: One of:
            - 'applicable': all required inputs present and stable
            - 'missing_inputs': at least one required input unavailable
            - 'underconstrained': required inputs exist but unstable
            - 'not_applicable': structural incompatibility (reserved)
        required_inputs: List of input families required by this method
        missing_inputs: Dict mapping family → reason for each missing input
        unstable_inputs: Dict mapping family → reason for each unstable input
        diagnostics: Additional factual observations
        provenance: How this evaluation was performed
    """
    method_id: str
    family: str
    label: str
    status: str
    required_inputs: List[str]
    missing_inputs: Dict[str, str] = field(default_factory=dict)
    unstable_inputs: Dict[str, str] = field(default_factory=dict)
    diagnostics: List[str] = field(default_factory=list)
    provenance: Dict[str, str] = field(default_factory=dict)
    
    def summary(self) -> str:
        """One-line summary"""
        return f"{self.method_id}: {self.status}"
    
    def is_applicable(self) -> bool:
        """Check if method can be attempted"""
        return self.status == 'applicable'