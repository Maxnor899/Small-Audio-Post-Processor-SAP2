"""
SAP² Decoder Registry - sap2/decoders/registry.py

Central lookup for decoder implementations.

This module must remain simple:
- No applicability logic
- No parameter logic
- No fallback heuristics

It only maps method_id -> Decoder instance.

Important:
- Only register decoders that are actually implemented.
- The applicability matrix may describe methods that are not yet implemented in code.
  In that case, get_decoder(method_id) must return None (handled upstream by the engine).
"""

from __future__ import annotations

from typing import Dict, Optional

from sap2.decoders.base import Decoder

# Import concrete decoders explicitly (traceability > auto-discovery)
from sap2.decoders.time_domain.duration_based_morse_like import DurationBasedMorseLikeDecoder

# NOTE: Keep future decoders commented out until they are implemented.
# from sap2.decoders.time_frequency.spectral_stability_encoding import SpectralStabilityEncodingDecoder
# from sap2.decoders.inter_channel.phase_delta_decoder import PhaseDeltaDecoder


# Registry is a pure mapping. Keys must match method_id in the applicability matrix YAML.
_DECODERS: Dict[str, Decoder] = {
    DurationBasedMorseLikeDecoder.method_id: DurationBasedMorseLikeDecoder(),
    # SpectralStabilityEncodingDecoder.method_id: SpectralStabilityEncodingDecoder(),
    # PhaseDeltaDecoder.method_id: PhaseDeltaDecoder(),
}


def get_decoder(method_id: str) -> Optional[Decoder]:
    """
    Return a decoder instance for the given method_id, or None if not implemented.

    Not implemented is not an error: the applicability matrix may contain methods
    that are described but not yet implemented in code.
    """
    return _DECODERS.get(method_id)


def list_decoders() -> Dict[str, str]:
    """
    List implemented decoders: method_id -> decoder_version.
    Useful for diagnostics and reporting.
    """
    return {method_id: dec.version for method_id, dec in _DECODERS.items()}
