"""
SAP² Input Model - sap2/model/inputs.py

Core data structures for inputs with complete provenance.

ETHICAL PRINCIPLE: No hidden heuristics. All observations are factual.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional


@dataclass(frozen=True)
class Provenance:
    """
    Documents where an Input came from.
    
    Includes:
    - SAT methods used
    - SAT parameters/metrics
    - Builder version
    - Timestamp
    """
    
    sat_methods: List[str]
    sat_params: Dict[str, Dict[str, Any]]  # Parameters used by SAT methods
    builder_version: str
    timestamp: str
    
    @classmethod
    def create(
        cls,
        sat_methods: List[str],
        sat_params: Dict[str, Dict[str, Any]],
        builder_version: str
    ) -> Provenance:
        """Create Provenance with automatic timestamp"""
        return cls(
            sat_methods=sat_methods,
            sat_params=sat_params,
            builder_version=builder_version,
            timestamp=datetime.utcnow().isoformat() + 'Z'
        )


@dataclass(frozen=True)
class Input:
    """
    Represents one input family instance (E, Δ, S, V, M, or R).
    
    This is an ARTIFACT, not a status flag.
    
    - family: Input family identifier (E, Δ, S, V, M, R)
    - available: Factual presence/absence
    - data: Optional payload (events, intervals, vectors, etc.)
    - provenance: Where it came from and how it was built
    - metrics: Numeric descriptors (factual, no thresholds)
    - notes: Factual observations and limitations
    """
    
    family: str
    available: bool
    data: Optional[Any]
    provenance: Provenance
    metrics: Dict[str, float]
    notes: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate family"""
        valid_families = ['E', 'Δ', 'S', 'V', 'M', 'R']
        if self.family not in valid_families:
            raise ValueError(
                f"Invalid family '{self.family}'. Must be one of {valid_families}"
            )


@dataclass(frozen=True)
class InputBundle:
    """
    Complete set of inputs for all 6 families.
    
    - inputs: Mapping from family name → Input
    - channel: Channel identifier ('left', 'right', 'difference', etc.)
    """
    
    inputs: Mapping[str, Input]
    channel: str
    
    def __post_init__(self):
        """Validate that all 6 families are present"""
        expected = {'E', 'Δ', 'S', 'V', 'M', 'R'}
        actual = set(self.inputs.keys())
        
        if actual != expected:
            missing = expected - actual
            extra = actual - expected
            msg = []
            if missing:
                msg.append(f"missing: {sorted(missing)}")
            if extra:
                msg.append(f"extra: {sorted(extra)}")
            raise ValueError(f"InputBundle must have exactly E,Δ,S,V,M,R. {', '.join(msg)}")