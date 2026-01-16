# SAP² — Limits, Failures, and Non-Results

## Purpose of this document

This document describes the **explicit limits** of SAP² and the many situations
in which it is expected to **produce no actionable decoding outcome**.

These cases are not errors.
They are essential to the methodological integrity of the project.

---

## 1. Absence of required inputs

Many decoding methods require specific input families
(events, intervals, symbols, matrices, relations).

If one or more **required inputs are absent**, the method is considered
**not applicable**, without further analysis.

This is the most common outcome.

---

## 2. Structural ambiguity

An input may exist but be:

- unstable,
- weakly defined,
- highly sensitive to parameter changes,
- or compatible with multiple incompatible interpretations.

SAP² does **not** resolve such ambiguity automatically.

Ambiguity is explicitly reported as such.

---

## 3. Overlapping compatibility

It is possible for multiple decoding methods to appear structurally compatible
with the same set of inputs.

SAP² does not:
- rank methods,
- vote between methods,
- or select a “best” interpretation.

Simultaneous compatibility is treated as a **non-decisive state**.

---

## 4. Insufficient constraints

Some decoding methods require:
- strong invariants,
- repetition,
- or synchronization.

If observed structures do not sufficiently constrain the decoding space,
SAP² considers the method **under-constrained** and therefore unusable.

---

## 5. Parameter sensitivity

If the existence of an input depends critically on:
- a narrow threshold,
- a fragile discretization,
- or fine-tuned parameters,

SAP² treats the input as **methodologically weak**.

Such cases are flagged rather than promoted.

---

## 6. False positives by construction

Many signal structures can arise from:
- physical processes,
- rendering artifacts,
- compression,
- or deterministic systems,

without carrying intentional information.

SAP² does not attempt to distinguish intent from structure.

Structure alone is insufficient.

---

## 7. No convergence guarantee

SAP² does not assume that:
- multiple compatible observations imply a shared cause,
- or that convergence across analyses implies decodability.

Any perceived convergence remains a **human interpretation**.

---

## 8. Non-results are results

Producing outcomes such as:

- “no applicable decoding method”
- “inputs insufficient or ambiguous”
- “structural compatibility inconclusive”

is not a failure of the tool.

It is the expected behavior in most real-world cases.

---

## 9. Explicit refusal cases

SAP² explicitly refuses to:

- infer meaning from structure alone,
- label signals as encoded or non-encoded,
- suggest hidden communication,
- automate hypothesis validation.

These refusals are design choices, not missing features.

---

## 10. Summary

SAP² is designed to fail often, and fail clearly.

By documenting its limits and non-results,
the project avoids narrative bias
and preserves analytical rigor.

Understanding **where SAP² cannot help**
is as important as understanding where it can.
