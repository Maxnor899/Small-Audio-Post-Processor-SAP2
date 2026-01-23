"""
SAP² Applicability Matrix - sap2/applicability/matrix.py

Defines method requirements structure.

DUMB MODULE: no logic, no judgment, just data structures.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping


# Canonical input family names
INPUT_FAMILIES = ['E', 'Δ', 'S', 'V', 'M', 'R']

# Valid requirement levels
REQUIREMENT_LEVELS = ['required', 'optional', 'not_applicable']


@dataclass(frozen=True)
class MethodRequirements:
    """
    Requirements for a single decoding method.
    
    This is DESCRIPTIVE data loaded from YAML.
    No logic, no evaluation.
    
    Attributes:
        method_id: Unique method identifier
        family: Method family (time_domain, frequency_domain, etc.)
        label: Human-readable label
        requires: Mapping from input family → requirement level
                  Keys: E, Δ, S, V, M, R
                  Values: required | optional | not_applicable
        source_file: Which YAML file defined this method
    """
    
    method_id: str
    family: str
    label: str
    requires: Mapping[str, str]
    source_file: str
    
    def __post_init__(self):
        """Validate structure (minimal checks)"""
        # Check all families present
        missing = set(INPUT_FAMILIES) - set(self.requires.keys())
        if missing:
            raise ValueError(
                f"Method {self.method_id}: missing requirement levels for {missing}"
            )
        
        # Check valid levels
        for family, level in self.requires.items():
            if level not in REQUIREMENT_LEVELS:
                raise ValueError(
                    f"Method {self.method_id}: invalid level '{level}' for {family}. "
                    f"Must be one of: {REQUIREMENT_LEVELS}"
                )


@dataclass(frozen=True)
class ApplicabilityMatrix:
    """
    Complete matrix of all method requirements.
    
    This is the LOADED data from YAML files.
    No logic, no evaluation.
    
    Attributes:
        schema_version: Version of the matrix schema
        methods: Mapping from method_id → MethodRequirements
    """
    
    schema_version: str
    methods: Mapping[str, MethodRequirements]
    
    def get_method(self, method_id: str) -> MethodRequirements:
        """Get requirements for a specific method"""
        if method_id not in self.methods:
            raise KeyError(f"Method not found: {method_id}")
        return self.methods[method_id]
    
    def get_methods_by_family(self, family: str) -> Mapping[str, MethodRequirements]:
        """Get all methods in a family"""
        return {
            mid: method 
            for mid, method in self.methods.items() 
            if method.family == family
        }