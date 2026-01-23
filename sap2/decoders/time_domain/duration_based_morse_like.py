"""
sap2/decoders/time_domain/duration_based_morse_like.py

Duration-based "Morse-like" structural decoder.

This decoder is a structural transformer:
- Consumes Δ (intervals) produced by the grammar builder.
- Applies explicit duration thresholds to map intervals to a symbol stream.
- Produces a secondary bitstream artifact via an explicit symbol->bit mapping.
- Produces an ExperimentResult containing artifacts + factual diagnostics.

No interpretation is performed. Output is only structural artifacts.

Expected input shape:
- bundle.get("Δ").data == {"intervals": [float, float, ...]}
  (as produced by sap2/grammar/builders/intervals.py)
"""

from __future__ import annotations

from typing import Any, Dict, List

from sap2.decoders.base import Decoder, DecoderParams, refused, failure
from sap2.model.experiment import ExperimentResult, ExperimentStatus
from sap2.model.inputs import InputBundle


class DurationBasedMorseLikeDecoder(Decoder):
    """
    Maps each interval duration to:
      - "."  if interval <= dot_max
      - "-"  if interval >= dash_min
      - "?"  otherwise (ambiguous region between dot_max and dash_min)

    Optionally, can emit separators when an interval is large:
      - "|"  if interval >= letter_gap_min
      - "/"  if interval >= word_gap_min

    Also produces a bitstream artifact from the symbol stream:
      - "." -> dot_bit (default 0)
      - "-" -> dash_bit (default 1)
      - "?" / separators -> None

    Notes:
    - This is simplistic duration binning. It does not claim Morse decoding.
    - It consumes Δ only (interval durations). Any other structure is out of scope here.
    """

    method_id = "duration_based_morse_like"
    version = "0.1.0"

    def decode(self, bundle: InputBundle, params: DecoderParams) -> ExperimentResult:
        delta = bundle.get("Δ")

        if not delta.available:
            return refused(
                method_id=self.method_id,
                version=self.version,
                reason="Δ input unavailable (intervals builder reported available=False).",
            )

        if delta.data is None or not isinstance(delta.data, dict):
            return refused(
                method_id=self.method_id,
                version=self.version,
                reason="Δ.data missing or invalid; expected a dict with key 'intervals'.",
            )

        intervals = delta.data.get("intervals")
        if not isinstance(intervals, list):
            return refused(
                method_id=self.method_id,
                version=self.version,
                reason="Δ.data['intervals'] missing or invalid; expected a list of numbers.",
            )

        if len(intervals) == 0:
            return failure(
                method_id=self.method_id,
                version=self.version,
                reason="Δ.data['intervals'] is empty; nothing to transform.",
            )

        # Explicit parameters (declared defaults live here; no hidden behavior)
        dot_max = float(params.get("dot_max", 0.12))
        dash_min = float(params.get("dash_min", 0.20))

        # Optional separators (disabled by default)
        letter_gap_min = params.get("letter_gap_min", None)
        word_gap_min = params.get("word_gap_min", None)

        letter_gap_min_f = float(letter_gap_min) if letter_gap_min is not None else None
        word_gap_min_f = float(word_gap_min) if word_gap_min is not None else None

        # Bit mapping parameters (explicit)
        dot_bit = int(params.get("dot_bit", 0))
        dash_bit = int(params.get("dash_bit", 1))

        # Structural parameter sanity checks
        if dot_max <= 0.0:
            return refused(
                method_id=self.method_id,
                version=self.version,
                reason=f"Invalid parameter: dot_max must be > 0 (got {dot_max}).",
            )
        if dash_min <= 0.0:
            return refused(
                method_id=self.method_id,
                version=self.version,
                reason=f"Invalid parameter: dash_min must be > 0 (got {dash_min}).",
            )
        if dot_max >= dash_min:
            return refused(
                method_id=self.method_id,
                version=self.version,
                reason=f"Invalid parameters: dot_max ({dot_max}) must be < dash_min ({dash_min}).",
            )

        if (letter_gap_min_f is not None) and (letter_gap_min_f <= 0.0):
            return refused(
                method_id=self.method_id,
                version=self.version,
                reason=f"Invalid parameter: letter_gap_min must be > 0 (got {letter_gap_min_f}).",
            )
        if (word_gap_min_f is not None) and (word_gap_min_f <= 0.0):
            return refused(
                method_id=self.method_id,
                version=self.version,
                reason=f"Invalid parameter: word_gap_min must be > 0 (got {word_gap_min_f}).",
            )
        if (letter_gap_min_f is not None) and (word_gap_min_f is not None) and (letter_gap_min_f >= word_gap_min_f):
            return refused(
                method_id=self.method_id,
                version=self.version,
                reason=(
                    f"Invalid parameters: letter_gap_min ({letter_gap_min_f}) must be < "
                    f"word_gap_min ({word_gap_min_f})."
                ),
            )

        # Core transformation: intervals -> symbols
        symbol_stream: List[str] = []
        n_dot = 0
        n_dash = 0
        n_ambiguous = 0
        n_letter_sep = 0
        n_word_sep = 0

        for x in intervals:
            try:
                d = float(x)
            except Exception:
                symbol_stream.append("?")
                n_ambiguous += 1
                continue

            # Optional separators for large gaps (if enabled)
            # Word gap has priority over letter gap.
            if (word_gap_min_f is not None) and (d >= word_gap_min_f):
                symbol_stream.append("/")
                n_word_sep += 1
                continue
            if (letter_gap_min_f is not None) and (d >= letter_gap_min_f):
                symbol_stream.append("|")
                n_letter_sep += 1
                continue

            # Duration binning
            if d <= dot_max:
                symbol_stream.append(".")
                n_dot += 1
            elif d >= dash_min:
                symbol_stream.append("-")
                n_dash += 1
            else:
                symbol_stream.append("?")
                n_ambiguous += 1

        # Secondary artifact: symbols -> bits
        bitstream: List[int | None] = []
        n_bits = 0
        n_none = 0

        for s in symbol_stream:
            if s == ".":
                bitstream.append(dot_bit)
                n_bits += 1
            elif s == "-":
                bitstream.append(dash_bit)
                n_bits += 1
            else:
                bitstream.append(None)
                n_none += 1

        diagnostics: List[str] = [
            f"Intervals transformed: {len(intervals)}",
            f"dot_max={dot_max}, dash_min={dash_min}, letter_gap_min={letter_gap_min_f}, word_gap_min={word_gap_min_f}",
            f"symbol counts: dot={n_dot}, dash={n_dash}, ambiguous={n_ambiguous}, letter_sep={n_letter_sep}, word_sep={n_word_sep}",
            f"bitstream mapping: dot_bit={dot_bit}, dash_bit={dash_bit}",
            f"bitstream counts: bits={n_bits}, none={n_none} (ambiguous + separators map to None)",
        ]

        artifacts: Dict[str, Any] = {
            "symbol_stream": symbol_stream,
            "bitstream": bitstream,
        }

        inputs_prov: Dict[str, Any] = {
            "Δ": {
                "provenance": delta.provenance.__dict__ if getattr(delta, "provenance", None) else None,
                "metrics": delta.metrics,
            }
        }

        return ExperimentResult(
            method_id=self.method_id,
            decoder_version=self.version,
            status=ExperimentStatus.SUCCESS,
            parameters_used={
                "dot_max": dot_max,
                "dash_min": dash_min,
                "letter_gap_min": letter_gap_min_f,
                "word_gap_min": word_gap_min_f,
                "dot_bit": dot_bit,
                "dash_bit": dash_bit,
            },
            artifacts=artifacts,
            diagnostics=diagnostics,
            inputs_provenance=inputs_prov,
        )
