"""
SAP² Engine package.

This package contains orchestration logic only.

Responsibilities:
- Coordinate the execution order of SAP² stages
- Enforce explicit gating rules (e.g. applicability before decoding)
- Aggregate results produced by other layers

Non-responsibilities:
- No decoding logic
- No applicability judgment
- No heuristics or interpretation
"""
