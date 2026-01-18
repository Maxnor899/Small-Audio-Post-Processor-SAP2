# SAP² — Small Audio Post-Processor

## What this project is

**SAP²** (Small Audio Post-Processor) is a research-oriented tool designed to explore  
**whether known audio decoding methods *could* be applied** to a given signal   
*before* attempting any actual decoding.

SAP² does **not** analyze raw audio files.  
It operates **exclusively** on the structured outputs (`results.json`) produced by  
**Small Audio Toolkit** (SAT), which acts as the measurement instrument.

In short:

> **SAT measures.  
> SAP² reasons about decodability.**

---

## Why this project exists

The idea of “hidden messages in audio” sits at an uncomfortable crossroads between:

- legitimate signal processing techniques,
- real-world communication protocols,
- watermarking and steganography,
- and, unfortunately, a lot of speculation and narrative bias.

SAP² exists to introduce **structure, constraints, and falsifiability** into this space.

Instead of asking:

> “Is there a hidden message?”

SAP² asks:

> “Given what we measured,  
> are the *inputs required by known decoding methods* even present?”

Very often, the honest answer is **no** , and that is a perfectly valid result.

---

## What SAP² does

SAP² is built around four core ideas:

### 1. Decoding methods have *formal input requirements*

Every real, documented decoding method like morse, pulse-based binary, FSK, frame-based protocols, modulation schemes, etc. expects **specific types of inputs**:

- events,
- durations,
- ratios,
- symbol streams,
- frequency bands,
- modulation envelopes,
- inter-channel relations,
- clocks or periodic references.

SAP² starts by **explicitly describing those input contracts**.

---

### 2. Decodability comes *before* decoding

SAP² focuses first on **conditions of applicability**:

- Are the required structures present?
- Are the invariants stable?
- Are the dimensions compatible?
- Are the observations ambiguous or under-constrained?

Only if these questions have reasonable answers does decoding even become a meaningful discussion.

---

### 3. Separation of roles is mandatory

SAP² enforces a strict separation between:

- **Measurement** (Small Audio Toolkit)
- **Decodability analysis** (SAP²)
- **Interpretation** (human, external, contextual)

This project deliberately avoids:
- automatic conclusions,
- hidden thresholds,
- semantic labeling,
- “message detected” claims.

---

### 4. Failure is an expected and valid outcome

One of SAP²’s most important outputs can be:

> *“No known decoding method is compatible with the available inputs.”*

This is not a limitation : it is a **result**.

---

## What SAP² does *not* do

SAP² does **not**:

- claim the presence of hidden messages
- guarantee successful decoding
- infer meaning or intent
- replace human judgment
- act as a detector or classifier

SAP² is not a truth machine.  
It is a **reasoning aid**.

---

## Typical workflow

```
Audio file
   ↓
Small Audio Toolkit (SAT)
   ↓
Objective measurements
(results.json)
   ↓
SAP²
   ↓
• Applicable decoding spaces
• Missing or ambiguous inputs
• Possible decoding paths
• Explicit failure cases
```

Any actual decoding attempt happens **after this**, as an explicit, reversible hypothesis.

---

## Repository structure

```
SAP2/
├── README.md
├── docs/
│   ├── 00_PHILOSOPHY.md
│   ├── 01_DECODING_METHODS.md
│   ├── 02_INPUT_GRAMMAR.md
│   ├── 03_METHODS_INPUT_MATRIX.md
│   ├── 04_LIMITS_AND_FAILURES.md
│   └── 05_RELATION_TO_SAT.md
```

The documentation is **not ancillary** , it *is* the project.

---

## Intended audience

SAP² may be useful to:

- signal processing enthusiasts
- security and steganography researchers
- protocol reverse-engineers
- ARG designers and analysts (serious ones)
- anyone interested in separating evidence from narrative

If you are looking for a tool that “reveals secrets”, this is not it.

If you are looking for a tool that tells you **why a decoding attempt is unjustified**, you’re in the right place.

---

## Ethical posture

SAP² is developed with an explicit **white-hat, methodological stance**:

- transparency over spectacle
- falsifiability over persuasion
- constraints over stories

The project intentionally documents:
- its assumptions,
- its limits,
- and the many cases where it cannot say anything useful.

---

## Status

This project is currently in an **early conceptual and documentation phase**.

No decoding logic is implemented yet — by design.

The first milestone is to fully formalize:
- decoding methods,
- their required inputs,
- and the grammar of observable structures.

---

## Final note

SAP² exists because humans are very good at seeing patterns —  
sometimes **far better than reality deserves**.

This tool is an attempt to slow that process down,  
and ask, calmly and explicitly:

> *“Do we even have the right pieces to play this game?”*
