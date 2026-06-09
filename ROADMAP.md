# Roadmap

This roadmap lists planned versions in temporal order with concrete deliverables, gate criteria, and the epistemic status of each line item. Items marked **VERIFIED** are scheduled work with concrete artifacts already specified. Items marked **PLAUSIBLE** are well-grounded but their concrete artifacts are not yet specified in detail. Items marked **SPECULATIVE** are directional indications subject to revision based on what earlier versions reveal.

Current head: **v0.2-α** (LEDGER #0005, 2026-06-09, 51/51 tests, Phase 6 closed with 12/13 findings resolved).

---

## v0.2-β — Formal verification and chain anchoring · 4–8 weeks

The next minor version. Scope is pure software work; no new dependencies on external partners or hardware.

| Deliverable | Description | Status |
|---|---|---|
| **Mercury formal proof** | Lean 4 machine-checkable proof of WCET=5 cycle bound, deterministic semantics, and bus-write authorization invariant. Coq acceptable as alternative; F* or Why3 considered. | VERIFIED scope; build pending |
| **HF-10 closure (full)** | Replace v0.2-α's informal proof with the machine-checkable artifact; ledger entry KERNEL_FORMAL_VERIFICATION includes the proof's hash | VERIFIED scope |
| **OpenTimestamps anchor** | Chain witness file periodically anchored to Bitcoin via OpenTimestamps for external verifiability. Replication path to a paired ground witness file | VERIFIED scope |
| **Chain integrity replay tool** | Standalone CLI that walks a chain database + key + witness file, returns pass/fail + report. Distributable to auditors and partners | VERIFIED scope |
| **ACI live-pipeline integration** | Wire Civium's conformal calibration band to the live pipeline instead of demo-only | PLAUSIBLE — requires sandbox-to-production schema alignment |
| **C-3 closure** | Validate AIBOM metadata in chain entries against CycloneDX 1.6 + SPDX 2.3 schemas | VERIFIED scope |
| **C-2 closure** | Make filesystem ACL enforcement explicit in the substrate (currently operator responsibility) | PLAUSIBLE |

**Exit gate for v0.2-β:** Mercury Lean 4 proof checked by the Lean kernel, ledger entry committed, OpenTimestamps anchor demonstrated against a public Bitcoin block, all 51 tests still passing.

---

## v0.3 — Production inference + HSM-backed PHI · 8–12 weeks after v0.2-β

The first version intended to be operationally credible (still not flight, but operationally credible for a high-stakes terrestrial deployment partner).

| Deliverable | Description | Status |
|---|---|---|
| **Mistral-7B production swap** | Default Civium adapter becomes `OllamaMistralAdapter` instead of `TransformersHFAdapter`. Sandbox Qwen-0.5B retained as test-only | VERIFIED scope; adapter exists in v0.2-α |
| **Calibration audit** | Empirical study of Civium's confidence distribution on Mistral-7B against a labeled scenario library (≥1000 states). HF-12 thresholds re-validated. Audit packaged into `reports/V03_CALIBRATION_AUDIT.md` | VERIFIED scope; dataset construction needed |
| **HSM/KMS-backed signing key** | Ed25519 signing key migrates from local filesystem to a NIST-validated HSM (FIPS 140-3 Level 3 minimum). v0.3 supports both modes via a CryptoBackend abstraction | PLAUSIBLE — HSM vendor selection pending |
| **HSM/KMS-backed PHI key** | Fernet PHI key migrates to HSM with access logging. Satisfies HIPAA §164.312(a)(2)(iv) | PLAUSIBLE |
| **HF-15 underwriter dry-run** | Package the compliance evidence (chain replay + AIBOM + risk reduction trace) for a real insurance underwriter dry-run. Documented response, not necessarily a binding policy | PLAUSIBLE — partner conversation needed |
| **Scenario library v1** | ≥1000 labeled state vectors covering nuanced band, safety floor, sensor fault, validity violation, comm-loss, multi-fault dispatch. Used for calibration audit and for ongoing HF-12 regression | VERIFIED scope |
| **Provisional patent filing** | Cross-modal compliance fabric filed via engaged practitioner. Covers Aletheia + MVCI + Mercury + Civium + bus isolation as unified system-and-method | PLAUSIBLE — practitioner engagement is the prerequisite |
| **GSA M-25-22 compliance resource repository submission** | Submission of the AIBOM-generator track per 90-day plan. Days 61–90. | VERIFIED scope per published plan |
| **arXiv preprint** | Public preprint of the IEEE paper (post-patent filing) for community discussion | VERIFIED scope |
| **Two external pilot partners** | Real organizations running the substrate against their own scenarios. Likely: CAH (Critical Access Hospital) pilot under HIPAA framing; SOSSEC consortium pilot under federal framing | PLAUSIBLE — partner conversations underway |

**Exit gate for v0.3:** Mistral-7B production inference with calibration audit complete; HSM-backed keys for signing and PHI; underwriter dry-run completed with documented response; provisional patent on file; at least one external pilot running.

---

## v1.0 — Hardware silicon for bus isolation · 12–24 weeks after v0.3

The first version intended to be flight-credible for the substrate component (still not full-suit flight — that requires shell partner v1.2). v1.0 is the substrate's transition from "software running on a Jetson dev kit" to "substrate running on a flight-credible compute module."

| Deliverable | Description | Status |
|---|---|---|
| **Hardware bus isolation** | Privileged-write bus authority enforced in silicon, not in software. Likely: dedicated MCU running the kernel + bus, with the AI compute (Mistral-7B inference) on a separate AP processor connected via a controlled message bus | PLAUSIBLE — hardware partner needed |
| **Anti-tamper enclosure** | Physical enclosure for the Phronesis Core with tamper-evident sealing and chain-of-custody logging | SPECULATIVE — partner-dependent |
| **TPM-backed boot** | Boot chain measured into a TPM 2.0; chain entries cross-reference boot measurement | PLAUSIBLE |
| **Radiation-tolerant compute** | Jetson Orin NX is consumer-grade. Flight requires either: NASA Class B parts (preferred) or COTS with documented mitigation (TMR, watchdog reset, ECC, ...). v1.0 documents the chosen path | SPECULATIVE — depends on mission class and risk posture |
| **Flight-credible test campaign** | Substrate compute module subjected to accelerator beam test (proton + heavy ion), thermal vacuum cycle, vibration to NASA-STD-7003A | PLAUSIBLE — test facility access needed |
| **Three external pilot partners** | Scaling from v0.3's two pilots to three; introducing a second domain (likely federal or rural-infrastructure) alongside the original | PLAUSIBLE |
| **HF-10 full closure** | The benchmark's HF-10 ("kernel + isolation") is finally fully closed with hardware silicon, replacing the software-surrogate posture | VERIFIED gate |

**Exit gate for v1.0:** Substrate compute module passes a flight-credible test campaign; HF-10 closed in hardware; three pilots running.

---

## v1.2 — Shell partner integration · concurrent with v1.0

The first version that has a shell — i.e., the substrate inside an actual pressure garment with a real PLSS, supplied by an industry partner.

This version requires a partnership with a spacesuit OEM (ILC Dover, Collins Aerospace, Axiom, or equivalent). The substrate's role is to integrate with the shell partner's life-support and biomedical telemetry. The shell partner's role is to provide the rest of the suit.

| Deliverable | Description | Status |
|---|---|---|
| **Partner agreement** | LOI or contract with a shell OEM. Defines IP boundaries, integration interfaces, test responsibilities | SPECULATIVE — pre-contractual |
| **Shell-scope HF closure** | The benchmark's HF-1 (reliability), HF-2 (multi-mode), HF-3 (250 EVA cycle), HF-4 (pre-breathe), HF-5 (dust), HF-6 (radiation tiles), HF-7 (repair), HF-11 (interop) are closed by the partner under documented integration spec | SPECULATIVE |
| **Integration test campaign** | Combined substrate + shell tested as a single article. Includes manned chamber tests if partner provides facility | SPECULATIVE |
| **End-to-end EVA simulation** | Substrate makes live decisions during a simulated EVA (NBL or analog facility), chain captures full provenance, ground replication demonstrated | SPECULATIVE |

**Exit gate for v1.2:** Combined article passes a manned chamber test (vacuum, thermal, biomedical) with substrate operating as decision authority. Chain replicates to ground in real-time. All 15 benchmark hard-fail floors closed.

---

## v2.0 — Mission-credible · 24+ months out

The first version targeting an actual interplanetary deployment context. This is the version that would be considered for an artemis-class lunar surface mission or a Mars-analog surface trial.

This version is **SPECULATIVE** in its entirety. It depends on:

- Successful v1.0 (substrate compute module flight-credible)
- Successful v1.2 (combined article integration-credible)
- Mission opportunity (lunar surface mission selection, Mars-analog trial, etc.)
- Sustained mission-class partner relationships
- Regulatory engagement (NASA flight readiness review, mission-specific safety case)

v2.0 deliverables will be defined when v1.0 and v1.2 exit gates are passed and a mission opportunity is identified. The benchmark may be re-issued as v2.0-BENCH at that point to reflect mission-specific constraints (e.g., specific destination environment, specific crew profile, specific mission duration).

---

## Parallel track: research and publication

Independent of the substrate version progression, the following research deliverables are scheduled:

| Deliverable | Target | Status |
|---|---|---|
| IEEE paper venue selection | After v0.2-β | PLAUSIBLE — multiple candidate venues identified |
| RCA whitepaper Layer 5+ empirical grounding | Independent track | SPECULATIVE — gating on grounded scenarios |
| QAWM companion paper | Separate IEEE submission | PLAUSIBLE |
| arXiv preprint of substrate paper | v0.3 (post-patent) | VERIFIED scope |
| LinkedIn long-form M-25-22 articles | Every two weeks | VERIFIED — running in parallel |
| Erdős Problem #912 (Er82c) follow-up | Independent track | PLAUSIBLE — pending Pomerance correspondence |

---

## Risk register

Risks that could change the roadmap, with epistemic confidence in their likelihood:

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Lean 4 proof of Mercury harder than expected | PLAUSIBLE | Slips v0.2-β | Coq, F*, Why3 acceptable as alternative formalisms |
| Mistral-7B Q4 production performance insufficient on Jetson Orin NX | PLAUSIBLE | Forces hardware up-spec (DGX-class) | DGX Spark pairing baseline already planned |
| HSM vendor selection takes longer than expected | PLAUSIBLE | Slips v0.3 | Multiple FIPS 140-3 L3 vendors available |
| Calibration audit reveals systematically miscalibrated confidence | PLAUSIBLE | Forces HF-12 threshold rework + benchmark v1.2 candidate | Documented in benchmark version process |
| Patent practitioner engagement delays filing | PLAUSIBLE | Delays public disclosure | Already on 90-day plan |
| Shell partner conversation does not close | SPECULATIVE | Blocks v1.2 indefinitely | Multiple candidate partners; secondary plan to issue partial v1.2 with substrate-only deliverables |
| Compute hardware roadmap shifts (Jetson Orin discontinued) | SPECULATIVE | Forces port to successor part | Architecture is portable; Mercury is bitwidth-agnostic |
| External funding required earlier than expected | SPECULATIVE | Forces compression of timeline | Federal capture pipeline (SOSSEC, GSA) already active |

---

## Non-goals

For clarity, things this roadmap does **not** commit to:

- A consumer/commercial product. The substrate is research/development; productization is a separate decision gated on regulatory and commercial signals.
- A general-purpose AI safety framework. The substrate is a *specific* falsification-first decision substrate for one application class. Generalization is interesting but is not on this roadmap.
- An open-source community in the typical sense. Contributions are welcome under CONTRIBUTING.md; the project is not designed for distributed maintainership at this stage.
- AGI claims. The substrate is "practical wisdom" in Aristotle's sense — bounded, gated, falsifiable. Not a step toward general intelligence.

---

## How this roadmap is updated

The roadmap is updated:

1. After each version's exit gate is met — items shift forward and the next version's scope is firmed up
2. When a Phase 6 attack reveals a gap that requires re-prioritization — the gap is documented in `reports/` and the roadmap is updated with a fresh ledger commit
3. When a partner conversation closes — relevant SPECULATIVE items are upgraded to PLAUSIBLE or VERIFIED with a partner-specific deliverable
4. When the IEEE paper is accepted — the publication track is updated

Updates are made via pull request, reviewed by the principal investigator, and committed to the ledger.

— A. Khaalis Wooden, Sr.
— Visionblox LLC / Zuup Innovation Lab
