# From decoding requirements to measurement protocols (conceptual mapping)

## Purpose of this document

This document describes a **conceptual relationship** between:

- decoding requirements expressed in SAP²,
- the input grammar used to formalize those requirements,
- and the kinds of **measurement protocols** that may be useful upstream in Small Audio Toolkit (SAT).

This document is **not prescriptive**.
It does not mandate features, implementations, or priorities for SAT.

Its sole purpose is to clarify **how requirements expressed downstream can inform understanding upstream**, in a human-driven and non-binding way.

---

## Context and scope

SAP² operates on measured outputs.
It never processes raw audio and never influences measurement execution.

However, SAP² decoders and models make their requirements explicit:
- required input families (E, Δ, S, V, M, R),
- stability expectations,
- structural constraints.

By inspecting these requirements, one can already gain insight into
**which kinds of measurements would be necessary** *if* one wanted to support certain classes of reasoning.

This is a **pedagogical and architectural observation**, not a dependency.

---

## Key principle

> Decoding requirements describe *what would be needed*,
> not *what should be measured*.

All mappings described below are:
- optional,
- contextual,
- human-interpreted,
- reversible.

SAT remains free to ignore any of them.

---

## Input grammar as an intermediate abstraction

The SAP² input grammar acts as a **neutral abstraction layer** between:

- decoding methods (downstream),
- and measurement protocols (upstream).

It defines *forms of observable structure*, not meaning.

The six input families are:

- **E** — Event-based inputs  
- **Δ** — Interval and duration inputs  
- **S** — Symbolic sequence inputs  
- **V** — Vector and statistical inputs  
- **M** — Matrix and field inputs  
- **R** — Relational and inter-channel inputs  

Each family corresponds to **observable properties**, not interpretations.

---

## Conceptual mapping: input families → measurement tendencies

The following mappings are **illustrative**, not exhaustive.

### Event-based inputs (E)
Typically require measurements capable of:
- detecting transients or threshold crossings,
- segmenting signals into discrete occurrences,
- preserving precise temporal indices.

Examples of useful protocol tendencies:
- transient detection,
- envelope thresholding,
- onset detection.

---

### Interval and duration inputs (Δ)
Require:
- stable time references,
- consistent event ordering,
- reproducible duration measurements.

Examples:
- inter-onset interval extraction,
- silence duration measurement,
- normalized timing ratios.

---

### Symbolic sequence inputs (S)
Require:
- explicit discretization rules,
- documented thresholds or clustering strategies,
- reversibility when possible.

Examples:
- binary or categorical mappings derived from E or Δ,
- duration class assignment,
- quantized state transitions.

---

### Vector and statistical inputs (V)
Require:
- numerical descriptors aggregated over time, bands, or regions,
- explicit aggregation methods,
- reproducible statistics.

Examples:
- energy per band,
- entropy measures,
- modulation indices,
- stability metrics.

---

### Matrix and field inputs (M)
Require:
- structured measurements over multiple axes,
- explicit resolution and normalization parameters,
- inspectable representations.

Examples:
- spectrograms (STFT),
- time–frequency stability maps,
- multi-scale transforms.

---

### Relational and inter-channel inputs (R)
Require:
- multiple synchronized channels or components,
- explicit reference definitions,
- stable alignment strategies.

Examples:
- cross-correlation,
- inter-channel delay estimation,
- phase difference analysis.

---

## What this mapping does NOT imply

This document does **not** imply that:

- any decoding method is applicable,
- any measurement protocol should be implemented,
- any signal contains encoded information,
- any interpretation is justified.

It merely explains **why certain measurements exist at all** in rigorous analytical pipelines.

---

## Pedagogical value

This mapping is useful as a learning aid because it:

- makes hidden assumptions visible,
- explains why measurement diversity exists,
- clarifies the relationship between observation and reasoning,
- helps avoid ad-hoc or narrative-driven protocol design.

It can be read without running any code.

---

## Architectural consistency

The relationship described here preserves:

- the independence of SAT,
- the non-prescriptive role of SAP²,
- the separation between measurement, reasoning, and interpretation.

The feedback loop is **conceptual only** and always mediated by human judgment.

---

## Summary

Decoders express structural needs.  
Models formalize those needs.  
Input grammar abstracts them.  
Measurement protocols may respond — or not.

Understanding this chain is part of learning how to design
**rigorous, falsifiable signal analysis systems**.
