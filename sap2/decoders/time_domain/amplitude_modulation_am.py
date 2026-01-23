"""
Amplitude Modulation (AM) Decoder - sap2/decoders/modulation/amplitude_modulation_am.py

Produces decoding hypotheses from interval-based discretization.
No interpretation, no claim of correctness.

Inputs used (typical):
- Δ (intervals) required by matrix
- S (symbols) optional (binary discretization of Δ)
- V (vectors) optional (am_detection metrics for diagnostics)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from sap2.decoders.base import DecoderParams, refused, failure
from sap2.model.experiment import ExperimentResult, ExperimentStatus
from sap2.model.inputs import InputBundle, Input


def _is_printable_ascii(byte_val: int) -> bool:
    # Printable ASCII plus common whitespace: tab, newline, carriage return, space.
    return byte_val in (9, 10, 13) or 32 <= byte_val <= 126


def _bits_to_int(bits: List[int], msb_first: bool) -> int:
    if msb_first:
        value = 0
        for b in bits:
            value = (value << 1) | (b & 1)
        return value
    # LSB-first
    value = 0
    for i, b in enumerate(bits):
        value |= ((b & 1) << i)
    return value


def _decode_ascii_candidates(
    bits: List[int],
    frame_bits: int,
    msb_first: bool,
    offset: int,
) -> Tuple[str, float]:
    """
    Decode bits into an ASCII string candidate.

    Returns:
        (text, printable_ratio)
    """
    if frame_bits <= 0:
        return ("", 0.0)

    if offset < 0 or offset >= frame_bits:
        return ("", 0.0)

    usable = bits[offset:]
    n_frames = len(usable) // frame_bits
    if n_frames <= 0:
        return ("", 0.0)

    chars: List[str] = []
    printable = 0

    for i in range(n_frames):
        frame = usable[i * frame_bits : (i + 1) * frame_bits]
        val = _bits_to_int(frame, msb_first=msb_first)
        if _is_printable_ascii(val):
            printable += 1
            chars.append(chr(val))
        else:
            chars.append("�")

    ratio = printable / n_frames if n_frames > 0 else 0.0
    return ("".join(chars), ratio)


@dataclass(frozen=True)
class AmplitudeModulationAmDecoder:
    method_id: str = "amplitude_modulation_am"
    version: str = "1.0.0"

    def decode(self, bundle: InputBundle, params: DecoderParams) -> ExperimentResult:
        # --- Retrieve inputs ---
        delta: Input = bundle.get("Δ")
        sym: Input = bundle.get("S")
        vec: Input = bundle.get("V")

        if not delta.available or not delta.data or "intervals" not in delta.data:
            return refused(self.method_id, self.version, "Δ intervals missing in InputBundle (pulse_detection not available or insufficient events).")

        intervals = delta.data["intervals"]
        if not isinstance(intervals, list) or len(intervals) < 8:
            return refused(self.method_id, self.version, f"Δ intervals too short for framing hypotheses: got {len(intervals) if isinstance(intervals, list) else 'invalid'}.")

        # --- Optional diagnostics from V ---
        v_am: Optional[Dict[str, Any]] = None
        if vec.available and vec.data and isinstance(vec.data, dict):
            vectors = vec.data.get("vectors", {})
            if isinstance(vectors, dict):
                v_am = vectors.get("am_detection")

        diagnostics: List[str] = []
        if v_am is not None:
            diagnostics.append(f"V.am_detection present: keys={sorted(list(v_am.keys()))}")
        else:
            diagnostics.append("V.am_detection not present (SAT did not run am_detection or data not exported).")

        # --- Build bitstream hypotheses ---
        # Prefer S if present (already explicit median discretization).
        bitstreams: List[Dict[str, Any]] = []

        def _add_bitstream(bits: List[int], origin: str, mapping: str) -> None:
            bitstreams.append(
                {
                    "origin": origin,
                    "mapping": mapping,
                    "length_bits": len(bits),
                    "bits": bits,
                }
            )

        if sym.available and sym.data and isinstance(sym.data, dict) and "symbols" in sym.data:
            symbols = sym.data.get("symbols", [])
            if isinstance(symbols, list) and symbols:
                # Hypothesis A: short->0, long->1
                bits_a = [0 if s == "short" else 1 for s in symbols]
                _add_bitstream(bits_a, origin="S.symbols", mapping="short=0,long=1")

                # Hypothesis B: short->1, long->0 (explicit alternative)
                bits_b = [1 if s == "short" else 0 for s in symbols]
                _add_bitstream(bits_b, origin="S.symbols", mapping="short=1,long=0")
            else:
                diagnostics.append("S available but symbols list is empty or invalid.")
        else:
            # Fallback: discretize Δ by median (explicit, documented here)
            try:
                sorted_vals = sorted(float(x) for x in intervals)
                median = sorted_vals[len(sorted_vals) // 2]
            except Exception as exc:
                return failure(self.method_id, self.version, f"Failed to discretize Δ intervals: {exc}")

            diagnostics.append(f"Discretization fallback: median_threshold={median:.6f} (from Δ intervals).")

            bits_a = [0 if float(x) < median else 1 for x in intervals]
            _add_bitstream(bits_a, origin="Δ.intervals", mapping=f"<median=0,>=median=1 (median={median:.6f})")

            bits_b = [1 if float(x) < median else 0 for x in intervals]
            _add_bitstream(bits_b, origin="Δ.intervals", mapping=f"<median=1,>=median=0 (median={median:.6f})")

        # --- Generate ASCII hypotheses (structural, not interpretative) ---
        frame_bits_list = params.get("frame_bits_list", [8, 7])
        max_offsets = int(params.get("max_offsets", 8))
        msb_first_list = params.get("msb_first_list", [True, False])
        max_hypotheses = int(params.get("max_hypotheses", 10))

        candidates: List[Dict[str, Any]] = []

        for bs in bitstreams:
            bits = bs["bits"]
            for frame_bits in frame_bits_list:
                for msb_first in msb_first_list:
                    # Try a limited number of offsets to avoid brute-force explosion
                    for offset in range(min(max_offsets, max(frame_bits, 1))):
                        text, printable_ratio = _decode_ascii_candidates(
                            bits=bits,
                            frame_bits=int(frame_bits),
                            msb_first=bool(msb_first),
                            offset=int(offset),
                        )
                        candidates.append(
                            {
                                "source_bitstream": {
                                    "origin": bs["origin"],
                                    "mapping": bs["mapping"],
                                },
                                "framing": {
                                    "frame_bits": int(frame_bits),
                                    "msb_first": bool(msb_first),
                                    "offset": int(offset),
                                },
                                "printable_ratio": float(printable_ratio),
                                "text_candidate": text,
                            }
                        )

        # Keep best candidates only (by printable_ratio, then by length)
        candidates.sort(key=lambda c: (c["printable_ratio"], len(c["text_candidate"])), reverse=True)
        candidates = candidates[:max_hypotheses]

        # --- Build result ---
        artifacts: Dict[str, Any] = {
            "bitstream_hypotheses": [
                {k: v for k, v in bs.items() if k != "bits"} for bs in bitstreams
            ],
            "ascii_hypotheses": candidates,
        }

        # Provide small preview of the best candidate in diagnostics (still a hypothesis)
        if candidates:
            best = candidates[0]
            diagnostics.append(
                f"Best ASCII hypothesis: printable_ratio={best['printable_ratio']:.3f}, "
                f"frame_bits={best['framing']['frame_bits']}, msb_first={best['framing']['msb_first']}, offset={best['framing']['offset']}."
            )

        return ExperimentResult(
            method_id=self.method_id,
            decoder_version=self.version,
            status=ExperimentStatus.SUCCESS,
            parameters_used={
                "frame_bits_list": frame_bits_list,
                "msb_first_list": msb_first_list,
                "max_offsets": max_offsets,
                "max_hypotheses": max_hypotheses,
            },
            artifacts=artifacts,
            diagnostics=diagnostics,
            inputs_provenance={
                "Δ": delta.provenance.__dict__,
                "S": sym.provenance.__dict__,
                "V": vec.provenance.__dict__,
            },
        )

