"""
Bundle Builder - sap2/grammar/bundle_builder.py

Orchestrates all 6 grammar builders to produce complete InputBundle.
"""


from sap2.io.load_sat import SatResults
from sap2.model.inputs import InputBundle
from sap2.grammar.builders.events import build_events
from sap2.grammar.builders.intervals import build_intervals
from sap2.grammar.builders.symbols import build_symbols
from sap2.grammar.builders.vectors import build_vectors
from sap2.grammar.builders.matrices import build_matrices
from sap2.grammar.builders.relations import build_relations


def build_input_bundle(sat: SatResults, channel: str) -> InputBundle:
    """
    Build complete InputBundle for a channel.
    
    Runs all 6 grammar builders and assembles their outputs.
    Each builder observes and documents without judgment.
    
    Args:
        sat: SatResults instance
        channel: Channel name ('left', 'right', 'difference', etc.)
        
    Returns:
        InputBundle with all 6 families (E, Δ, S, V, M, R)
    """
    
    return InputBundle(
        inputs={
            'E': build_events(sat, channel),
            'Δ': build_intervals(sat, channel),
            'S': build_symbols(sat, channel),
            'V': build_vectors(sat, channel),
            'M': build_matrices(sat, channel),
            'R': build_relations(sat, channel)
        },
        channel=channel
    )


def build_all_channels(sat: SatResults) -> dict:
    """
    Build InputBundles for all available channels.
    
    Returns:
        Dict mapping channel_name -> InputBundle
    """
    return {
        channel: build_input_bundle(sat, channel)
        for channel in sat.channels
    }