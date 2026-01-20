# SAP² — Architecture

## Purpose of this document

This document defines the **software architecture** of SAP² (Small Audio Post-Processor).

It explains:
- the intended module boundaries,
- the data contracts between components,
- the execution pipeline,
- and the constraints that preserve methodological rigor.

This is an architecture document, not an implementation guide.

---

## 1. Core idea

SAP² operates **only on measurements** produced by upstream tools (primarily Small Audio Toolkit / SAT).

SAP² is responsible for:
1. Loading structured measurement outputs (`results.json`)
2. Building **typed intermediate inputs** (the "input grammar")
3. Checking **structural applicability** of decoding methods
4. Attempting decoding **only when justified** (Phase 3)
5. Producing transparent outputs (reports + machine-readable artifacts) (Phase 3)

SAP² does not:
- process raw audio,
- generate measurements,
- infer meaning or intent.

---

## 2. Separation of concerns

SAP² is designed around strict separation of responsibilities:

- **I/O**: load, validate, normalize inputs
- **Model**: typed in-memory representations of SAT results and SAP² inputs
- **Grammar builders**: construct input families (E, Δ, S, V, M, R)
- **Applicability**: decide whether a decoding method can be attempted (with reasons)
- **Decoders**: attempt decoding, producing experiments and diagnostics (Phase 3)
- **Engine**: orchestrate the pipeline and enforce ordering (Phase 3)
- **Render**: produce reports and exports (Phase 3)
- **Tests**: verify contracts, reproducibility, and refusal cases

No component should "reach across" layers.

---

## 3. Repository layout

Current implementation (Python package `sap2`):

```
SAP2/
├── README.md
├── docs/
│   └── (documentation set)
├── CONTRIBUTING
├── LICENSE
├── sap2/
│   ├── __init__.py
│   ├── io/
│   │   ├── __init__.py
│   │   └── load_sat.py
│   ├── model/
│   │   ├── __init__.py
│   │   ├── inputs.py
│   │   └── applicability.py
│   ├── grammar/
│   │   ├── __init__.py
│   │   ├── bundle_builder.py
│   │   └── builders/
│   │       ├── __init__.py
│   │       ├── events.py
│   │       ├── intervals.py
│   │       ├── symbols.py
│   │       ├── vectors.py
│   │       ├── matrices.py
│   │       └── relations.py
│   └── applicability/
│       ├── __init__.py
│       ├── matrix.py
│       ├── matrix_loader.py
│       ├── params.py
│       ├── checks.py
│       └── matrices/
│           ├── _index.yaml
│           ├── matrix.schema.json
│           ├── time_domain.yaml
│           ├── frequency_domain.yaml
│           ├── time_frequency.yaml
│           ├── modulation.yaml
│           ├── inter_channel.yaml
│           └── statistical.yaml
└── tests/
    └── (unit tests)
```

**Future modules** (Phase 3):
- `sap2/decoders/` - actual decoding implementations
- `sap2/engine/` - pipeline orchestration
- `sap2/render/` - output generation

---

## 4. Data model contracts

### 4.1 `SatResults` (normalized measurement input)

Defined in: `sap2/io/load_sat.py`

`SatResults` is a typed wrapper around the upstream `results.json`.

It provides typed methods and properties for accessing measurements, while the measurements themselves remain as flexible dictionaries (to accommodate SAT's evolving output format).

Responsibilities:
- hold metadata (sample rate, channels, duration)
- expose method results by name and channel via `get_method(name, channel)`
- expose method parameters via `get_method_metrics(name)`
- provide a stable access API even if SAT output evolves

It supports both:
- `path/to/results.json`
- `path/to/output_dir/` (where results.json is found inside)

### 4.2 `Provenance` (traceability)

Defined in: `sap2/model/inputs.py`

Documents the origin of an Input:

```python
@dataclass(frozen=True)
class Provenance:
    sat_methods: List[str]              # SAT methods used
    sat_params: Dict[str, Dict]         # Parameters/metrics from SAT
    builder_version: str                # Builder version
    timestamp: str                      # ISO timestamp
    
    @classmethod
    def create(...) -> Provenance:      # Factory with auto-timestamp
```

### 4.3 `Input` (single input family)

Defined in: `sap2/model/inputs.py`

Represents one input family instance (E, Δ, S, V, M, or R):

```python
@dataclass(frozen=True)
class Input:
    family: str                         # E, Δ, S, V, M, or R
    available: bool                     # Factual presence/absence
    data: Optional[Any]                 # Optional payload
    provenance: Provenance              # Complete traceability
    metrics: Dict[str, float]           # Factual numeric descriptors
    notes: List[str]                    # Factual observations
```

Each family supports explicit states:
- **available=True** with data and metrics
- **available=False** with reason in notes

No judgment occurs in Input creation — only factual observation.

### 4.4 `InputBundle` (complete input set)

Defined in: `sap2/model/inputs.py`

`InputBundle` aggregates all six input families:

```python
@dataclass(frozen=True)
class InputBundle:
    inputs: Mapping[str, Input]         # Must contain E, Δ, S, V, M, R
    channel: str                        # Channel identifier
```

All six families (E, Δ, S, V, M, R) must be present, even if unavailable.

### 4.5 `ApplicabilityParams` (explicit thresholds)

Defined in: `sap2/applicability/params.py`

Explicit, documented, overridable thresholds for applicability evaluation:

```python
@dataclass
class ApplicabilityParams:
    min_regularity: float = 0.1
    max_cv: float = 1.0
    min_symbol_balance: float = 0.2
    min_vector_sources: int = 3
    min_matrix_windows: int = 10
    accept_matrix_proxies: bool = False
    min_relation_types: int = 1
```

All thresholds are visible and adjustable by the user.

### 4.6 `MethodRequirements` (method specification)

Defined in: `sap2/applicability/matrix.py`

Describes requirements for a single decoding method:

```python
@dataclass(frozen=True)
class MethodRequirements:
    method_id: str                      # Unique identifier
    family: str                         # time_domain, frequency_domain, etc.
    label: str                          # Human-readable name
    requires: Mapping[str, str]         # E/Δ/S/V/M/R → required/optional/not_applicable
    source_file: str                    # Which YAML defined it
```

Requirements are loaded from YAML files, not hardcoded.

### 4.7 `ApplicabilityMatrix` (all methods)

Defined in: `sap2/applicability/matrix.py`

Collection of all method requirements:

```python
@dataclass(frozen=True)
class ApplicabilityMatrix:
    schema_version: str
    methods: Mapping[str, MethodRequirements]
```

Loaded via `load_applicability_matrix(matrices_dir)` from YAML files in `matrices_dir/` (`_index.yaml` declares family-specific YAMLs: `time_domain.yaml`, `frequency_domain.yaml`, etc.).

### 4.8 `ApplicabilityReport` (evaluation result)

Defined in: `sap2/model/applicability.py`

Result of evaluating whether a method can be applied:

```python
@dataclass(frozen=True)
class ApplicabilityReport:
    method_id: str
    family: str
    label: str
    status: str                         # applicable/missing_inputs/underconstrained/not_applicable
    required_inputs: List[str]
    missing_inputs: Dict[str, str]      # family → reason
    unstable_inputs: Dict[str, str]     # family → reason
    diagnostics: List[str]              # Factual observations
    provenance: Dict[str, str]          # Evaluation context
```

Status values:
- `applicable`: all required inputs present and stable
- `missing_inputs`: at least one required input unavailable
- `underconstrained`: required inputs exist but unstable
- `not_applicable`: structural incompatibility (reserved; not emitted by current implementation)

### 4.9 `ExperimentResult` (Phase 3)

Represents a decoding attempt (to be implemented in Phase 3):

- decoder name + version
- parameters used
- inputs referenced (provenance)
- output artifacts (symbol streams, frames, bits, etc.)
- diagnostics (instability, sensitivity, failure explanations)
- outcome classification

No experiment result may claim semantic meaning.

---

## 5. Pipeline (execution order)

Current implementation (Phases 1-2):

1. **Load**
   - load `results.json` via `SatResults.load()`
   - normalize to `SatResults`
2. **Build inputs**
   - run 6 grammar builders via `build_input_bundle()`
   - produce `InputBundle` (one per channel)
3. **Load requirements**
   - load `ApplicabilityMatrix` from YAML via `load_applicability_matrix()`
4. **Check applicability**
   - for each method, call `evaluate_applicability(method, bundle, params)`
   - produce `ApplicabilityReport`

Future (Phase 3):
5. **Attempt decoding**
   - only for `applicable` (and optionally `underconstrained` if user forces)
6. **Render outputs**
   - write machine artifacts + human report

The pipeline is deterministic given the same inputs and parameters.

---

## 6. Grammar builders

### 6.1 Builder contract

Each builder implements:

```python
def build_<family>(sat: SatResults, channel: str) -> Input:
    """Build input family from SAT measurements."""
```

Builders:
- **observe** measurements without judgment
- report **factual metrics** (no thresholds applied)
- document **complete provenance**
- return `Input` with `available=True/False`

### 6.2 Builder orchestration

`build_input_bundle()` orchestrates all 6 builders:

```python
def build_input_bundle(sat: SatResults, channel: str) -> InputBundle:
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
```

No registry pattern in v1 — direct function calls.

---

## 7. Applicability system

### 7.1 Requirements (YAML)

Method requirements are defined in multiple YAML files organized by family.

The `matrices_dir/` contains:
- `_index.yaml` - declares which YAML files to load
- `matrix.schema.json` - validation schema
- Family-specific YAMLs (`time_domain.yaml`, `frequency_domain.yaml`, etc.)

Example of a family YAML:

```yaml
# time_domain.yaml
schema_version: "1.0"
family: "time_domain"

methods:
  duration_based_morse_like:
    label: "Duration-based (Morse-like)"
    requires:
      E: required
      Δ: required
      S: optional
      V: not_applicable
      M: not_applicable
      R: not_applicable
```

All requirements are:
- external to code (no hardcoding)
- organized by family in separate YAML files
- versioned (schema_version in each file)
- validated against JSON schema at load time

### 7.2 Loading requirements

```python
from sap2.applicability.matrix_loader import load_applicability_matrix

matrix = load_applicability_matrix(Path('sap2/applicability/matrices'))
# → ApplicabilityMatrix with all methods
```

### 7.3 Evaluating applicability

```python
from sap2.applicability.checks import evaluate_applicability
from sap2.applicability.params import ApplicabilityParams

params = ApplicabilityParams()  # or custom thresholds
method = matrix.methods['duration_based_morse_like']
bundle = build_input_bundle(sat, 'left')

report = evaluate_applicability(method, bundle, params)
# → ApplicabilityReport
```

Judgment happens in `checks.py` using **explicit params**, not in builders.

---

## 8. Decoders (Phase 3)

Future decoder contract:

- decoders declare required input families
- each decoder implements:
  - `decode(bundle, params) -> ExperimentResult`

Decoders must not generate missing inputs.
They may only refuse or proceed with explicit assumptions.

---

## 9. CLI (Phase 3)

A minimal CLI will support:

- `sap2 run <path>`
  - where `<path>` is `results.json` or a SAT output directory
- options:
  - `--out <dir>` output directory
  - `--only <method1,method2>` restrict to subset
  - `--channels <left,right,difference>` restrict channels
  - `--params <file>` custom ApplicabilityParams
  - `--force` allow running `underconstrained` experiments

The CLI will never hide assumptions.

---

## 10. Output structure (Phase 3)

Suggested output layout:

```
sap2_output/
├── inputs/
│   ├── events.json
│   ├── intervals.json
│   ├── symbols.json
│   ├── vectors.json
│   ├── matrices.meta.json
│   └── relations.json
├── applicability.json
├── experiments.json
└── report.md
```

Every exported artifact will include provenance fields.

---

## 11. Testing strategy

SAP² is tested primarily on **contracts and refusal behavior**.

Test categories:

- loading/normalization of SAT outputs ✓
- builders produce correct available/unavailable states ✓
- applicability matrix consistency (required inputs enforced) ✓
- builders never apply thresholds ✓
- checks correctly apply params ✓
- deterministic outputs given fixed inputs ✓
- regression tests on known SAT results fixtures

Tests prefer small fixtures to avoid heavy runtime.

---

## 12. Non-goals (architectural constraints)

Architecture explicitly prevents:

- decoding without applicability checks
- hidden scoring or probability labels
- semantic interpretation
- SAT coupling (no SAT imports or runtime dependency required)
- builders applying thresholds (only checks.py judges)

SAP² is compatible with SAT outputs, but logically independent.

---

## 13. Future integration (optional)

A later, optional integration may add a SAT-side helper that:
- generates SAT protocols to produce inputs needed by specific SAP² methods

This must remain a separate tool or optional module to preserve SAT neutrality.

---

## Summary

SAP² is a two-stage reasoning system built on top of measurement outputs:

**Current (Phases 1-2):**
- **SAT measures** → `results.json`
- **SAP² loads** → `SatResults`
- **SAP² builds typed inputs** → `InputBundle` (observation without judgment)
- **SAP² loads requirements** → `ApplicabilityMatrix` (from YAML)
- **SAP² checks applicability** → `ApplicabilityReport` (judgment with explicit params)

**Future (Phase 3):**
- **SAP² attempts decoding** → `ExperimentResult` (as constrained experiments)
- **SAP² reports outcomes** → reports + artifacts

The architecture enforces methodological boundaries by construction.