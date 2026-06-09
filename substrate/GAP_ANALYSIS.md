# VBX-ISPS Substrate v0.1 — Gap Analysis

**Build:** VBX-ISPS Substrate Prototype v0.1
**Contract:** VBX-ISPS-BENCH-v1.1 (SHA-256 `58bf8744d3cc78b1cb7bb88464edb7df796187c45cea1ae483e936249803c1c5`)
**Author:** A. Khaalis Wooden, Sr., MBA; MSIT Candidate, Southern New Hampshire University
**Phase:** ZCS-6 Phase 5 closure — load-bearing v0.2 prerequisites

---

## Purpose

ZCS-6 Phase 5 requires an honest enumeration of what is missing, arbitrary, or empirically ungrounded in the first runnable version. This document is that enumeration. It is intentionally specific so a v0.2 backlog can be derived directly.

Every item is tagged with the floor or clause it gates, the v0.1 stand-in (if any), and what the v0.2 deliverable must be.

---

## Load-bearing gaps

### G-1. Real LLM inference layer (Mistral-7B via Ollama)

- **Gates:** HF-12 (autonomy ratio measurement becomes meaningful), the drift clause (ACI gates a real model's confidence, not a synthetic distribution), HF-9 (REQUIRES_HUMAN decisions surface from a model that has confidence < threshold)
- **v0.1 stand-in:** Rule-based deterministic recommender in `src/civium/inference.py`. The stub always returns confidence within the synthetic envelope, so AUTONOMOUS_ELIGIBLE decisions resolve autonomously 100% of the time — passes HF-12's 70% threshold but does not stress-test the gate.
- **v0.2 deliverable:** Mistral-7B running under Ollama, called from `inference.py`. Confidence emerges from token-level log-probabilities (or a calibrated wrapper). ACI on confidence; recommendations below the band route to safe-passive. Expected outcome: autonomous-resolution rate drops from 1.000 to a meaningful sub-1.000 value reflecting real model uncertainty under realistic input distributions.
- **Confidence on v0.2 feasibility:** PLAUSIBLE — Ollama + Mistral-7B fits the MVCI substrate spec already.

### G-2. Formal verification of the Mercury kernel (Coq/Lean proofs)

- **Gates:** HF-10 (the floor explicitly requires formally verified deterministic kernel with proven WCET)
- **v0.1 stand-in:** WCET measured empirically (5 cycles across 900 input pairs, deterministic). Correctness shown by test, not by proof.
- **v0.2 deliverable:** (a) Coq or Lean specification of the subleq emulator semantics, (b) machine-checkable proof of O2 control loop correctness (`command = setpoint - reading` after clipping), (c) WCET bound derived from the proof rather than measurement. Mathlib provides the integer arithmetic foundation; the subleq ISA's simplicity is the leverage here — the entire VM is ~30 lines of Python and maps cleanly to a Lean inductive definition.
- **Confidence on v0.2 feasibility:** PLAUSIBLE — Lean 4 with Mathlib supports this directly; subleq's single-instruction semantics make the proof tractable.

### G-3. Hardware-isolation silicon specification

- **Gates:** HF-10 (the floor requires bus-level enforcement, not policy-level)
- **v0.1 stand-in:** Software bus in `src/isolation/bus.py` with a `KERNEL_PRIVILEGE_TOKEN` check. ML-impersonation attempts are denied (1,000 / 1,000 in `test_penetration`), but the enforcement is a Python contract, not a hardware mechanism.
- **v0.2 deliverable:** A hardware-architecture document specifying: (a) which silicon enforces the kernel's exclusive write privilege to the safety bus (e.g., a dedicated MCU + isolated I/O lines with no path from the ML inference SoC), (b) the watchdog topology, (c) the penetration test methodology against a bench reference implementation. Mercury's AWS F1 CL wrapper is a candidate path for the prototype silicon.
- **Confidence on v0.2 feasibility:** SPECULATIVE — depends on hardware partner engagement; the architecture is specifiable now even without a fabricated device.

### G-4. Extended drift suite covering all 5 named distributions

- **Gates:** v1.1 non-stationarity clause
- **v0.1 stand-in:** One synthetic scalar regression proxy (metabolic-rate-analog). Static CI 0.593 (collapsed), ACI 0.895 (held) — reproduces the Aletheia DAC headline pattern but on one distribution only.
- **v0.2 deliverable:** Five distinct drift harnesses, one per named distribution: crew metabolic rate, thermal load on PLSS, CO2 partial pressure profile, dust load rate, bearing wear rate. Each evaluated at 1×, 2×, 3× drift. Each demonstrating static-collapse / ACI-hold. The dust load and bearing wear distributions are monotonic with rate drift — a different drift pattern than the noisy-stationary metabolic case — and will exercise ACI under a harder regime.
- **Confidence on v0.2 feasibility:** VERIFIED — the ACI implementation is general; the work is constructing realistic distributions per domain.

### G-5. Production-grade 10k stratified scenario library

- **Gates:** HF-12 anchor; v1.1 dependency artifact #5
- **v0.1 stand-in:** `generate_stratified_scenarios` in `tests/test_autonomy.py` produces 10,000 procedurally generated scenarios from three strata (70% nominal, 20% edge, 10% adversarial) using a uniform-random PLSS state generator. Fit for v0.1 measurement; not flight-realistic.
- **v0.2 deliverable:** A versioned scenario library committed to chain as a v1.1 dependency artifact. Scenarios drawn from: (a) published Apollo / Shuttle / ISS EVA telemetry where available, (b) Mars surface mission rehearsal data from HERA and Mauna Loa analog, (c) adversarial cases hand-crafted by flight surgeons and EVA officers. Each scenario tagged at design time with its expected policy classification and rationale.
- **Confidence on v0.2 feasibility:** PLAUSIBLE — depends on data access; NASA Lyndon B. Johnson Space Center has historically released analog mission data.

### G-6. Underwriter dry-run for HF-15

- **Gates:** HF-15 explicit verification artifact
- **v0.1 stand-in:** Structural completeness only — every floor mapped to clauses in every required standard. No third-party review.
- **v0.2 deliverable:** Engage a qualified actuarial underwriter familiar with aerospace risk pools or autonomous-systems liability lines. The dry-run is not a policy issuance; it is a letter from the underwriter confirming the evidence package is sufficient to begin a quote process. This is a procurement and legal motion as much as a technical one.
- **Confidence on v0.2 feasibility:** SPECULATIVE — depends on underwriter willingness to engage with a pre-revenue R&D artifact. AIG / Allianz / Munich Re aerospace lines are candidates.

### G-7. Robot AIBOM per OMB M-25-22 Annex C, tied to 90-day plan

- **Gates:** HF-15 OMB M-25-22 clause; HF-8 cross-reference
- **v0.1 stand-in:** OMB M-25-22 is mapped in `compliance/HF15_evidence_package.md` as a referenced clause. No AIBOM artifact produced.
- **v0.2 deliverable:** A Robot AIBOM artifact per the M-25-22 Annex C structure, covering: (a) every ML model in the inference layer (in v0.2: Mistral-7B with version, training data provenance, evaluation results), (b) every dependency in the build graph (CycloneDX 1.6 SBOM), (c) every policy file and its chain commit hash, (d) every formal verification artifact and its proof status, (e) the kernel firmware hash and re-verification record. This Robot AIBOM ties into the active 90-day AIBOM generator plan (Day 1-30 spec → Day 31-45 build on MVCI substrate → Day 46-60 provisional patent + arXiv → Day 61-90 GSA submission + SOSSEC distribution).
- **Confidence on v0.2 feasibility:** PLAUSIBLE — direct integration with the existing AIBOM workstream; v0.2 is customer-zero for the AIBOM generator on the embodied-AI case.

### G-8. v1.1 dependency artifacts not yet committed

Per the v1.1 spec, five dependency artifacts must commit alongside the operational benchmark for it to be fully self-contained. The policy file (item 2) and the simulation test suite (item 5) are partial in v0.1 (policy file committed; scenario library is procedural). The remaining three are gates on hardware-partner work, not substrate work:

- Mission EVA manifest (anchors HF-3 — shell scope; v1.2)
- Habitat suit-port ICD (anchors HF-11 — shell scope; v1.2)
- Rover suit-port ICD (anchors HF-11 — shell scope; v1.2)

v0.2 may produce a v1.1.1 policy revision and the production scenario library; the ICDs and EVA manifest are explicitly v1.2 with hardware partner.

---

## Arbitrary thresholds carried forward

Several v1.1 thresholds were defended in Phase 3 but remain ultimately arbitrary in the sense that they could shift under accelerated-life data or operational reality. v0.1 inherits these; v0.2 should re-examine.

- **HF-3 250 EVAs.** Anchored to NASA DRA 5.0 manifest + 25% margin. If the manifest revises (or if a different reference architecture displaces DRA 5.0), the number revises.
- **HF-4 30-minute pre-breathe.** Anchored to xEMU 8.2 psia / 4.3 psi spec. If cabin pressure architecture changes, the protocol expectation shifts.
- **HF-6 150 mSv.** Sized as a fraction of the 600-1200 mSv NASA career envelope. SPE escalation clause is conditional on operational SPE-shelter assumption.
- **HF-12 70% autonomous on AUTONOMOUS_ELIGIBLE.** Defended as the design intent for ACI band placement, but the precise number could move once v0.2 LLM inference produces empirical distributions.
- **HF-13 5-second alert latency.** Defended by reference to arrhythmia detection windows. Could tighten if flight surgeons argue for sub-second.

None of these are v0.1 failures. All are flags for Phase 6 attention.

---

## Empirically ungrounded claims in v0.1

- **Mercury Subleq is the right kernel substrate.** v0.1 demonstrates a working O2 control loop in 5 deterministic cycles. The claim that subleq is *the right choice* — vs. a small subset of a verified RISC-V profile, vs. a custom HDL — is SPECULATIVE. Comparative evaluation against alternative formally-verifiable kernels is a v0.2 task.
- **ACI is the right confidence-gating mechanism.** Reproducing the Aletheia headline on one synthetic distribution is supportive but not dispositive. The published ACI literature (Gibbs & Candes 2021 et seq.) supports use in stationary-with-drift settings; whether life-support telemetry profiles fit that regime cleanly is a v0.2 empirical question.
- **Rule-based inference is informative as a v0.1 placeholder.** It validates pipeline plumbing — chain append, gate evaluation, kernel dispatch, bus actuation — but tells you nothing about how the substrate behaves under real model uncertainty. The placeholder is honest; the substantive evidence comes in v0.2.

---

## v0.2 backlog summary (derived from gaps above)

| ID | Item | Gates | Owner-ready? |
|---|---|---|---|
| G-1 | Mistral-7B / Ollama inference | HF-12, drift, HF-9 | Yes — MVCI substrate already specced |
| G-2 | Lean/Coq proofs of kernel | HF-10 | Yes — subleq surface is small |
| G-3 | Hardware-isolation silicon spec | HF-10 | Pending hardware partner |
| G-4 | Five-distribution drift suite | drift clause | Yes — internal |
| G-5 | Production scenario library | HF-12 anchor | Pending data access |
| G-6 | HF-15 underwriter dry-run | HF-15 | Pending underwriter engagement |
| G-7 | Robot AIBOM per M-25-22 | HF-15 | Tied to 90-day AIBOM plan |
| G-8 | v1.1 dependency artifacts | shell scope | v1.2 with partner |

The substrate-internal items (G-1, G-2, G-4, G-7) are unblocked and constitute the v0.2 build target. The remaining items are pending partnership or data-access motions.

---

*End of gap analysis.*
