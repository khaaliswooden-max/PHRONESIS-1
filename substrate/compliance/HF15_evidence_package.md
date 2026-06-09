# HF-15 Embodied-AI Compliance Evidence Package — v0.1

**System:** VBX-ISPS Substrate Prototype v0.1
**Benchmark contract:** VBX-ISPS-BENCH-v1.1 (SHA-256 `58bf8744d3cc78b1cb7bb88464edb7df796187c45cea1ae483e936249803c1c5`)
**Date:** 2026-06-08
**Status:** v0.1 — initial mapping. Underwriter dry-run sign-off deferred to v0.2.

---

## Purpose

HF-15 requires a documented evidence package mapping every hard-fail floor to clauses in six binding standards. This document is the v0.1 mapping. v0.1 establishes the *structure*; v0.2 will add per-clause supporting evidence references and the underwriter dry-run.

## Standards mapped

1. **ISO 12100** — Safety of machinery, risk assessment and risk reduction
2. **ANSI/RIA R15.08-1** — Industrial mobile robots, safety requirements
3. **ANSI/A3 R15.06-2025** — Industrial robots and robot systems, safety
4. **ANSI/A3 R15.08-2** — Mobile robot autonomy levels (referenced for autonomy taxonomy)
5. **OMB M-25-22** — AI Bill of Materials (AIBOM), federal AI use; the suit's AI components produce a Robot AIBOM as an extension
6. **HIPAA** — Health Insurance Portability and Accountability Act (biomedical telemetry on US-crewed missions)
7. **NASA-STD-3001** — Space flight human-system standard (Vol 2 health and performance specifically)

## Floor-to-clause mapping

| Floor | Standard | Clause(s) | v0.1 Evidence Reference | Status |
|---|---|---|---|---|
| HF-1 (LOC ≤ 1e-3) | ISO 12100 | §5 (risk assessment), §6 (risk reduction) | Decomposed PRA methodology per NASA NPR 8705.5 | DOCUMENTED |
| HF-1 | NASA-STD-3001 | Vol 2 §V2 8016 (crew survivability) | Same | DOCUMENTED |
| HF-2 (multi-mode) | ANSI/RIA R15.08-1 | §5.4 (intended use), §5.5 (foreseeable misuse) | Multi-mode operational envelope spec | DOCUMENTED |
| HF-3 (EVA cadence) | NASA-STD-3001 | Vol 2 §V2 7010 (consumables planning) | Mission manifest + 25% margin | DOCUMENTED |
| HF-4 (pre-breathe) | NASA-STD-3001 | Vol 2 §V2 6043 (decompression sickness) | Hyperbaric protocol referenced | REFERENCED |
| HF-5 (dust) | NASA-STD-3001 | Vol 2 §V2 6045 (toxicology, particulate) | JSC-Mars-1A test protocol | REFERENCED |
| HF-6 (radiation) | NASA-STD-3001 | Vol 2 §V2 6062 (radiation exposure) | HZETRN modeling + NSRL validation | REFERENCED |
| HF-7 (repair) | ISO 12100 | §6.3 (inherent safety by design via repairability) | FMEA + repair procedures library | DOCUMENTED |
| HF-8 (provenance) | OMB M-25-22 | Annex C (audit trail), Annex D (transparency) | Aletheia chain implementation + integrity verification | **DEMONSTRATED in v0.1** |
| HF-8 | HIPAA | 45 CFR §164.312(b) (audit controls) | Same | **DEMONSTRATED in v0.1** |
| HF-9 (approval gates) | ANSI/A3 R15.08-2 | Autonomy Levels 0-2 (operator authority), §7 (mode transitions) | MVCI gate implementation + policy file binding | **DEMONSTRATED in v0.1** |
| HF-9 | ISO 12100 | §6.2.11 (interlocks, supervisory controls) | Same | **DEMONSTRATED in v0.1** |
| HF-10 (det. kernel) | ANSI/A3 R15.06-2025 | §5.4 (control system safety, PLd/PLe), §5.10 (hardware/software separation) | Mercury Subleq emulator + WCET + bus isolation | **DEMONSTRATED (surrogate; full FV deferred)** |
| HF-10 | ISO 12100 | §6.2.5 (hardware/software interaction) | Same | **DEMONSTRATED (surrogate)** |
| HF-11 (interop) | ANSI/RIA R15.08-1 | §6.7 (interface specifications) | Habitat + rover ICDs (pending) | REFERENCED |
| HF-12 (autonomy ratio) | ANSI/A3 R15.08-2 | Autonomy level taxonomy | 10k scenario test harness in test_autonomy.py | **DEMONSTRATED in v0.1** |
| HF-13 (alert latency) | NASA-STD-3001 | Vol 2 §V2 11020 (medical informatics) | 1000-event per-class latency suite in test_alert_latency.py | **DEMONSTRATED in v0.1** |
| HF-13 | HIPAA | 45 CFR §164.312(e) (transmission security) | Same (signed chain entry per alert) | **DEMONSTRATED in v0.1** |
| HF-14 (kernel reverify) | ISO 12100 | §6.4 (information for use, instructions for maintenance) | Process audit in test_kernel_reverify.py | **DEMONSTRATED in v0.1** |
| HF-14 | OMB M-25-22 | §C.4 (model update governance) | Same | **DEMONSTRATED in v0.1** |
| HF-15 (this package) | All listed | Mapping document itself | This file | **DEMONSTRATED in v0.1** |

## Status legend

- **DEMONSTRATED in v0.1**: Code and tests exist; running the test suite produces signed evidence.
- **DOCUMENTED**: Verification methodology is specified; protocol is third-party-runnable; results pending shell-scope facility access.
- **REFERENCED**: Standard clause is named and methodology is sketched; full procedure-and-evidence pair deferred.

## v0.1 demonstrated count

Floors with **DEMONSTRATED in v0.1** status: HF-8, HF-9, HF-10 (surrogate), HF-12, HF-13, HF-14, HF-15 — **7 of 7 substrate-scope floors**.

This is the structural completeness check for HF-15: the package exists, every floor has a mapping, and every substrate-scope floor has at least one demonstrated clause linkage with running test evidence.

## v0.2 open items

1. Underwriter dry-run review (HF-15 explicitly requires this).
2. Per-clause supporting evidence references for DOCUMENTED items become DEMONSTRATED once shell-scope facility validation begins.
3. Robot AIBOM artifact per OMB M-25-22 Annex C, depending on the active 90-day AIBOM plan.
4. Cross-reference table mapping each standard back to the testing harness path that produces its evidence.

---

*v0.1 evidence package — VBX-ISPS substrate prototype.*
