# VBX-ISPS — Interplanetary Spacesuit, ZCS-6 Application v1.0

**Author:** A. Khaalis Wooden, Sr., MBA; MSIT Candidate, Southern New Hampshire University
**Framework:** ZCS-6 (Zuup Creative Stack, six-phase falsification-first methodology)
**Date:** 2026-06-08
**Status:** Phase 1–4 complete and committed. Phase 5 architecture sketched. Phase 6 seam attacks enumerated; iteration deferred to working-code milestone.

---

## Phase 0 — Frame

The phrase "interplanetary spacesuit" is doing a lot of buzzword work. Strip it.

**What "interplanetary" actually constrains** (first principles, stripped):

1. **Latency.** Earth-Mars round trip is up to 44 minutes one-way at conjunction; ~22 min round-trip average. Ground-loop operations are dead. Suit autonomy is mandatory.
2. **No resupply.** Mass and volume to Mars surface is approximately $54,500 / kg payload at currently demonstrated cadence. Every consumable, spare, and tool travels with the crew or is ISRU-produced.
3. **Multi-mode.** Microgravity transit (~210 days each way) + Mars surface (0.376 g, ~480 days). Two regimes, one suit fleet — current incumbents (EMU for μg, xEMU/AxEMU for partial g) do not span both.
4. **Radiation.** Outside the magnetosphere. GCR baseline plus SPE risk. Multi-year integrated dose dominates lifetime career limits.
5. **Duration.** ~900 days total mission. Current EVA-rated EMU is certified for ~25 EVAs before refurb cycle. A 10× cadence improvement is the minimum.
6. **Dust.** Mars regolith is perchlorate-laden, sub-micron, electrostatically active. Apollo 17 documented severe LEM contamination in 72 hours. Mars surface stay is 480 days.
7. **Liability and oversight.** Autonomous life-support decisions made 22 light-minutes from any human reviewer require cryptographic post-hoc auditability — for medical review, insurance, regulatory clearance, and crew family disclosure.

**The reframing.** What is unsolved is not the pressure shell. ILC Dover, Collins, Axiom, and NASA have collectively shipped or prototyped solutions across most shell-and-PLSS engineering problems for one regime at a time. The **unsolved** part — the convergence vector that does not exist in any current program — is:

> *A compliance-graded, cryptographically-audited autonomous decision substrate for life-support, embodied in a multi-mode pressure shell rated for both microgravity and surface partial-gravity operation, supporting field-repairable autonomy across 900 days with no Earth resupply and no ground-loop dependency.*

That is the actual ZCS-6 problem. The shell engineering is a constraint on the substrate, not the goal.

This frame also makes the problem **Zuup-native**: it is a Civium (compliance-graded edge inference) problem with an Aletheia DAC (drift-aware provenance) backbone and an MVCI (approval-gate) policy layer, embodied in space-rated hardware. The same thesis as Khaalis's space robotics analysis, now wearing the pressure shell.

---

## Phase 1 — Whitespace

### Whitespace claim (one sentence)

*No current or announced spacesuit program produces a single pressure-shell platform that operates across both microgravity and partial-gravity regimes while embedding a cryptographically auditable, compliance-graded autonomous life-support decision substrate capable of multi-year operation under deep-space latency without ground-loop dependency.*

### Nearest prior work and stated gaps

| Reference | Closest claim | Gap |
|---|---|---|
| NASA xEMU / Collins (Artemis lunar EVA) | Partial-g surface EVA suit, ~8 hour PLSS, 4.3 psi suit pressure target | Lunar surface only; not microgravity-rated; no autonomous decision substrate; decision loop is ground-operator-mediated |
| Axiom AxEMU (commercial Artemis suit) | Same envelope as xEMU; commercial supplier | Same scope gap; same decision-loop posture |
| NASA Z-2 / Mark III demonstrators | Mars-relevant mobility experiments, rear-entry suit-port architecture | Demonstrators, not flight-rated; no integrated decision substrate; no multi-year deployment validation |
| ISS EMU and Russian Orlan | Microgravity EVA platform | Microgravity only; refurb-dependent; ground-loop operations |
| SpaceX IVA suit | Pressure-backup-only intravehicular suit | Not EVA-rated; not life-support autonomous |
| Aletheia DAC (Zuup) | Drift-aware claim substrate with hash-chained provenance and adaptive conformal inference | Not embodied; not space-rated; the convergence target, not an existing competitor |
| MVCI (Zuup) | 12-agent zero-budget approval-gated AI stack | Not embodied; substrate exists, application to suit decisioning is novel |
| Civium (Zuup) | Compliance-graded edge inference platform | Targeted at regulated terrestrial environments; deep-space extension is the convergence |

### FTO assessment

**Clear, with internal prior art on the substrate side.** External prior art on EVA suits (NASA, Axiom, Collins, ILC Dover, SpaceX) does not cover the autonomous compliance-graded decision substrate. Zuup's internal prior art (Aletheia DAC, MVCI, Civium) is owned by the same entity proposing the convergence, so it is FTO-clear *and* a defensible IP moat — the substrate is the moat, not the shell.

The PPA filing strategy that follows from this: claim the **embodied compliance-graded life-support decision substrate** as the load-bearing claim, with the multi-mode pressure shell as a dependent claim. This mirrors the Aletheia + Robot AIBOM convergence pattern from the active 90-day plan.

### Confidence marker

**Whitespace claim: PLAUSIBLE.**
The four whitespace conditions (structural demand + visible incumbent failure + real technical barrier + high re-entry cost) all hold, but the *commercial* whitespace depends on whether crewed Mars architecture materializes on a 10–15 year horizon. The *technical* whitespace is VERIFIED; the *market* whitespace is PLAUSIBLE.

---

## Phase 2 — Benchmark (VBX-ISPS-BENCH-v1.0)

The benchmark is committed *before* design work begins. The machine-readable spec is the companion file `vbx_isps_bench_v1_0.json` (10,540 bytes). What follows is the human-readable summary; the JSON is the contract.

### Mission scope (frozen for v1.0)

- Mars conjunction-class crewed mission
- 900 days total, 210 days transit each way, 480 days surface
- Crew of 4
- Max Earth round-trip latency: 2,640 s (~44 min one-way at conjunction)
- Max comm blackout window: 336 hours (14 days, e.g., solar conjunction)
- No resupply
- Operational modes: microgravity transit EVA + Mars surface EVA

### Hard-fail floors (any single failure disqualifies the design)

| ID | Floor | Threshold | Confidence |
|---|---|---|---|
| HF-1 | Suit-attributable LOC probability | ≤ 1.0e-3 per mission | PLAUSIBLE |
| HF-2 | Multi-mode operation | Single shell, μg + 0.30–0.40 g | PLAUSIBLE |
| HF-3 | EVA cadence | ≥ 250 productive EVAs (≥ 4 hr each) with no resupply | SPECULATIVE |
| HF-4 | Pre-breathe | ≤ 30 min cabin-to-EVA-ready across 8.2–14.7 psia cabin | PLAUSIBLE |
| HF-5 | Dust intrusion | ≤ 0.1% suit dry mass over 480 simulated sols | PLAUSIBLE |
| HF-6 | Radiation dose from EVAs | ≤ 150 mSv across 480 surface days (excl. SPE) | PLAUSIBLE |
| HF-7 | Repair autonomy | ≥ 80% of FMEA modes repairable ≤ 24 hr, onboard only | SPECULATIVE |
| HF-8 | Decision provenance | 100% of safety-critical decisions signed and chained | PLAUSIBLE |
| HF-9 | Approval gate integrity | 100% of REQUIRES_HUMAN decisions gated or safe-passive | VERIFIED |
| HF-10 | Safety-critical deterministic kernel | Formally verified, WCET-bounded, ML-isolated | SPECULATIVE |

### Soft scoring (0–10 per criterion)

Mass, donning time, joint torque deviation, FOV, acoustic isolation, biomedical channels, MTTR, training time, NASA TLX workload, comm bandwidth tolerance.

### Non-stationarity clause

All assertions evaluated under both stationary and drift conditions. Static conformal coverage tested at 1×, 2×, 3× distribution shift on crew metabolic, thermal, and CO2-load distributions. Pass requires Adaptive Conformal Inference coverage ≥ 0.85 under 3× shift. This is the Aletheia DAC headline test brought into life-support: static intervals collapse to ~0.40 coverage under 3× shift; ACI holds. A life-support PLSS that uses static intervals fails the drift clause.

### Trivial-pass strategies flagged for Phase 3

Seven gameable patterns flagged in the JSON (HF-3 via short EVAs, HF-5 via heavy-suit ratio trick, HF-6 via SPE exclusion, HF-7 via FMEA spacing, HF-8 via silent-failure non-logging, HF-9 via reclassification, HF-10 via kernel-stub bypass). All become Phase-3 attack targets.

---

## Phase 3 — Attack the Benchmark Objectively

Each attack class against v1.0. Findings → v1.1.

### Trivial-pass attacks

- **HF-3 short-EVA cheat.** 250 EVAs of 4 hours each — but a "productive" 4-hour EVA could be a stationary inspection task. **Mitigation:** add sub-floor — task completion validated against per-EVA acceptance criteria; the mission EVA manifest (drilling, deployment, sample collection) must close.
- **HF-5 mass-ratio cheat.** Make the suit arbitrarily heavy; intrusion ratio falls. **Mitigation:** add absolute intrusion floor of 50 g across 480 sols, *and* keep the 0.1% ratio.
- **HF-8 silent-failure cheat.** Sign only successful decisions; failures unlogged. **Mitigation:** the ledger is append-only and logs every *attempt* — including rejections, timeouts, and safe-passive fallbacks. Audit metric is fraction-unlogged at ledger replay, not fraction-signed.
- **HF-10 kernel-stub cheat.** Formally verify a kernel that is then proxied around at bus level. **Mitigation:** hardware-isolated kernel with bus-level enforcement; the kernel cannot be bypassed by design, not by policy.

### Coverage attacks (what is *not* tested)

- **Psychological / human-factors gap.** No metric for crew acceptance over 900 days. Add: NASA TLX subjective workload becomes a *floor* (currently soft), with threshold derived from EMU baseline + parity tolerance.
- **Suit-port / habitat / rover integration gap.** Suit does not exist in isolation. Add: HF-11 — interoperability with at least one habitat suit-port and one rover suit-port specification, documented as a published interface spec.
- **Comm degradation graceful-fall gap.** Tests assume 14-day blackout. Add: graceful degradation curve must be characterized continuously across 1 s → 14 day comm gaps, not only at the 14-day endpoint.

### Goodhart attacks

*If a team optimized purely against v1.0 for six months, what does the pathological optimum look like?*

A suit with a heavy outer shell (passes HF-5 trivially via ratio), a small, fixed FMEA tree (passes HF-7), a verbose ledger that logs everything but actuates nothing autonomously (passes HF-8 and HF-9 by collapsing all decisions to safe-passive), and a kernel that handles only a narrow set of decisions (passes HF-10).

**Counter-floor:** HF-12 — *Effective autonomy ratio.* Of all safety-critical decision events during the 480-surface-day simulation, at least 60% must be resolved *autonomously* (not safe-passive fallback) with crew survival and mission task continuity. The system cannot pass by abdicating.

### Drift / distribution attacks

The non-stationarity clause covers this in principle, but it must be sharpened: which distributions are tested?

- Crew metabolic rate (drift across deconditioning, age, illness episodes)
- Thermal load (drift across solar irradiance, surface vs. cave, season)
- CO2 partial pressure profile (drift across crew exertion patterns)
- Dust load on filters (monotonic accumulation, not drift in the stationary sense — but the *rate* drifts with surface activity profile)
- Bearing wear (monotonic, but rate-drift)

**Refinement:** the drift clause names these five distributions explicitly. ACI must hold across all five under 3× shift.

### Cross-investigator attack

If three skeptical reviewers — a NASA flight surgeon, an FAA certification engineer, and an actuarial underwriter — read v1.0:

- **Flight surgeon:** "Where is the biomedical telemetry latency floor? A 30-second delay on an arrhythmia alert can kill a crew member." → Add HF-13: biomedical alert latency ≤ 5 s end-to-end including chain signing.
- **Certification engineer:** "Where is the configuration-management requirement on the kernel firmware? Field updates to a formally verified kernel invalidate the verification." → Add HF-14: any post-flight kernel modification requires re-verification artifact prior to deployment, signed and committed.
- **Actuarial underwriter:** "What is the ISO 12100-equivalent evidence package for the autonomous decision system? Without it, I cannot price the policy." → Add HF-15: a documented evidence package mapping HF-1 through HF-14 to ISO 12100, ANSI/RIA R15.08-1, and ANSI/A3 R15.06-2025 clauses (the binding standards from the active robotics whitespace work — the same evidence frame applies to embodied life-support autonomy).

### Composition attack

Do the assertions interact? Yes: HF-9 (approval gating) and HF-12 (effective autonomy ratio) are in tension. A design that maximizes HF-12 by minimizing the REQUIRES_HUMAN set passes HF-12 and fails HF-9 in spirit. Resolution: the REQUIRES_HUMAN policy is itself an artifact in the Phase-4 commit, and its content (which actions are gated) is part of the benchmark, not a design choice. Reclassifying actions out of REQUIRES_HUMAN constitutes a benchmark revision and requires a new version.

### v1.1 revisions summary

- HF-11 (interoperability), HF-12 (effective autonomy), HF-13 (biomedical alert latency), HF-14 (kernel re-verification on modification), HF-15 (ISO/ANSI evidence package) added.
- HF-5 gets absolute mass floor + ratio.
- HF-3 gets task-validity sub-floor.
- HF-8 gets append-every-attempt clarification.
- Drift clause names five specific distributions.

v1.1 will be re-committed at Phase 4. v1.0 remains in the chain as the originating commit.

---

## Phase 4 — Defend Deterministically

### Cryptographic commit on v1.0

The benchmark JSON has been frozen and hashed. The commit record:

```
benchmark_id   : VBX-ISPS-BENCH
version        : 1.0
artifact       : vbx_isps_bench_v1_0.json
size_bytes     : 10540
sha256         : ac6114a4c0a025f86926fe2d3f95d36a5a8b4796b2893ce58e22df488f7fd861
timestamp_utc  : 2026-06-08T14:03:04Z
author         : A. Khaalis Wooden, Sr.
signing_key    : <Ed25519 public key fingerprint — placeholder until production key custody>
ots_proof      : <OpenTimestamps proof — to be appended on chain anchor>
chain_position : VBX-ISPS-LEDGER#0001 (genesis for this benchmark family)
```

The commit hash is the goalpost. Any future result claimed against VBX-ISPS-BENCH-v1.0 must verify against this hash. v1.1 (post-Phase-3) will be a sibling commit at chain position 0002, with a delta justification record (which floors changed, which were added, why) signed and appended. This is the Aletheia DAC pattern — hash-chained provenance with delta accountability — applied to a benchmark's own evolution.

**The goalpost cannot move quietly.** If, eight months from now, a solution underperforms HF-3 and someone proposes relaxing 250 EVAs to 200, that relaxation lives as v1.2 in the chain with an explicit justification, signed by an authorized human, with the v1.0 and v1.1 records intact. Goodhart's Law's failure mode — silent goalpost migration — is structurally prevented.

### Baseline scores (recorded floor)

- **Trivial baseline.** A current xEMU configured at conjunction-class duration: fails HF-2 (no microgravity capability), HF-3 (refurb-dependent), HF-7 (Earth-loop diagnosis assumed), HF-8 (no provenance ledger), HF-10 (no formally verified kernel). 5 of 10 hard-fails. Disqualified.
- **Aspirational baseline.** A hypothetical xEMU + Aletheia DAC bolted on: still fails HF-2, HF-3, HF-7 at minimum. 3 of 10. Still disqualified.
- **No reference SOTA.** No current or announced suit program is a candidate baseline. The benchmark currently has no passing system. This is consistent with the whitespace claim.

### Reproducibility

The JSON spec, the markdown rationale (this document), and the per-floor verification protocols form the reproducibility bundle. A third-party team can implement the verification harness without further clarification, per the Phase-4 exit criterion.

---

## Phase 5 — Solution Architecture (Sketch)

Phase 5 outputs are working code. This document does not deliver a finished suit. It delivers the **architecture commitment** that a working substrate prototype will target, and identifies what is genuinely buildable today versus what requires hardware that does not yet exist.

### Three-layer model

```
┌─────────────────────────────────────────────────────────────┐
│  SHELL LAYER                                                │
│  Pressure garment, PLSS, TMG, suit-port interfaces          │
│  — Engineering exercise; well-bounded by prior art          │
│  — Multi-mode via boot/glove/thermal cassettes              │
│  — Buildable in 5–8 years with industrial-scale program     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  SUBSTRATE LAYER                                            │
│  Compliance-graded autonomous decision system               │
│  ── Civium edge inference (compliance-graded LLM/agent)     │
│  ── Aletheia DAC (drift-aware claim chain + ACI bands)      │
│  ── MVCI (12-agent approval-gate policy substrate)          │
│  ── Mercury Subleq core (formally verified safety kernel)   │
│  — Buildable in software today on terrestrial bench         │
│  — This is the load-bearing claim and IP moat               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  SOVEREIGNTY LAYER                                          │
│  Crew-suit covenant: who decides what, when, under what     │
│  ── Policy file: REQUIRES_HUMAN actions enumerated, signed  │
│  ── Approval-cascade definition: crew → mission → ground    │
│  ── Safe-passive fallback definitions per failure mode      │
│  ── Post-hoc audit interface for medical/insurance/regulator│
│  — Buildable today; binding for HF-8, HF-9, HF-15           │
└─────────────────────────────────────────────────────────────┘
```

### Why this architecture maps to the hard-fails

- **HF-8 (provenance):** Aletheia DAC's existing Ed25519-signed hash-chained substrate is the direct mechanism. No new cryptography required — only space-qualified hardware to host it.
- **HF-9 (approval gates):** MVCI's existing 12-agent approval-gate pattern, ported. The novelty is the *policy file* (sovereignty layer), not the gate mechanism.
- **HF-10 (deterministic kernel):** Mercury Subleq's single-instruction architecture is uniquely suited to formal verification. The entire ISA is one instruction; verification surface is correspondingly small. The SSRN paper on Mercury already establishes the ISA; the suit application requires a WCET-bounded subset, formally verified for the specific control loops (O2, CO2, pressure, thermal, power).
- **HF-12 (effective autonomy):** Civium's compliance-graded inference handles the gray-zone decisions that should *not* default to safe-passive. ACI bands on the inference output drive the gate decision: high-confidence → autonomous; out-of-band → REQUIRES_HUMAN with fallback.
- **HF-13 (5 s biomedical alert):** The kernel handles alert detection deterministically; the LLM does not gate alerts. ML in the suit is for context and explanation, not life-critical actuation.

### What is buildable today (Phase 5 working-code milestone)

A terrestrial substrate prototype, runnable on commodity hardware plus a Jetson AGX Orin or Orin Nano Super, demonstrating:

1. A simulated PLSS telemetry stream feeding a Civium inference layer.
2. Aletheia DAC chain capturing every decision (autonomous + gated + safe-passive).
3. MVCI approval-gate policy enforcing HF-9.
4. A Mercury Subleq kernel emulator handling the safety-critical control loops with WCET measurement.
5. Red-team test suite injecting falsified telemetry, induced blackouts, and drift to validate HF-8, HF-9, HF-12, the non-stationarity clause.

This is approximately three months of focused work on the existing MVCI substrate with Aletheia DAC and Mercury as imported dependencies. It would not be a suit; it would be the *substrate's bench prototype*, which is the actually-defensible IP and the actually-novel piece. Hardware partners (Collins, Axiom, ILC Dover, or a new entrant) would consume the substrate spec as a procurement item.

### What requires hardware partnership

The shell layer requires space-qualified manufacturing, accelerated life-testing at scale, and human-factor validation in parabolic flight + lunar analog facilities. This is a 5–8 year industrial program. The substrate is the entry point; the shell is the integration.

### Confidence markers on the architecture

- Substrate layer: PLAUSIBLE to VERIFIED. Components exist; integration is engineering.
- Shell layer: PLAUSIBLE. Industrial program. Major risk is multi-mode validation (HF-2) — no precedent.
- Sovereignty layer: PLAUSIBLE. Policy authoring is straightforward; the binding novelty is making it cryptographically committed and version-tracked.

---

## Phase 6 — Attack Until Vertically Integrated

The Phase 6 pass is enumerated here in advance, as a forward-looking attack surface for the working-code milestone. Each seam will be re-attacked once code exists.

### Layer enumeration

1. Physical substrate (pressure shell, PLSS, sensors, actuators, comm)
2. Compute (kernel, inference accelerator, persistent storage)
3. Data (telemetry, ledger, policy files, FMEA)
4. Model (Civium inference, calibration, drift-aware bands)
5. Application (decision loops, approval cascades, alert handling)
6. Integration (suit-port, habitat, rover, ground)
7. Interface (crew display, audio, voice, biomedical sensing)
8. Governance (policy versioning, sign-off authority, change control)
9. Audit (post-hoc review for medical, regulatory, insurance, legal)

### Seam attacks enumerated

- **Substrate ↔ Compute.** What happens when an actuator stalls and the kernel cannot meet its WCET? Hardware watchdog must trip; the system must enter safe-passive. Verifiable.
- **Compute ↔ Data.** What happens when the ledger storage fills? Append-only ledgers are unbounded; storage budget is bounded. Must specify ledger compaction policy that preserves audit integrity.
- **Data ↔ Model.** What happens when training/calibration data drifts beyond ACI envelope? Model must declare out-of-band and fall to REQUIRES_HUMAN. Tested under non-stationarity clause.
- **Model ↔ Application.** What happens when the LLM hallucinates a recommendation? Recommendation passes through MVCI gate; gate enforces approval policy; hallucination does not actuate. Validated by red-team injection.
- **Application ↔ Integration.** What happens when habitat suit-port spec drifts from suit-as-built? Configuration management requirement (HF-14 sibling): integration spec is itself versioned and committed.
- **Integration ↔ Interface.** What happens when crew physiology drifts (deconditioning) and HMI calibration becomes wrong? Sensors must recalibrate; recalibration events are themselves ledger entries.
- **Interface ↔ Governance.** What happens when a crew member overrides an approval gate to act faster? Override is logged with explicit acknowledgment; the policy file may or may not permit it; if not permitted, override is rejected at the kernel.
- **Governance ↔ Audit.** What happens when a policy was modified mid-mission? Versioning chain shows when, by whom, with what signed justification. Audit can reconstruct decision context at any timestamp.

### Stress attacks

- **Load.** 1,000 decision events per minute during emergency descent? Substrate must absorb without queue overflow; document the queue depth and overflow behavior.
- **Drift.** Crew metabolic rate at 3× baseline during high-exertion EVA? ACI band widens; gate triggers REQUIRES_HUMAN; safe-passive available.
- **Latency.** Ground link drops mid-decision? Default to safe-passive unless pre-authorized template fires.
- **Adversarial input.** Compromised sensor injects false leak signal? Ledger detects within 1 s (HF-8); cross-sensor validation kicks in; if validation fails, crew alerted; emergency pressure dump remains gated unless multi-sensor consensus.
- **Resource exhaustion.** Battery low + comm low + sensor failing simultaneously? Pre-defined degradation priority list executes deterministically on the Mercury kernel.

### Compliance attack

The HF-15 evidence package is the binding requirement here. Maps:

- **ISO 12100** (machine safety risk assessment) — applies to the kernel + gate architecture.
- **ANSI/RIA R15.08-1** and **ANSI/A3 R15.06-2025** — the embodied-AI standards from Khaalis's robotics whitespace work; the suit is an embodied autonomous system and these are the binding standards.
- **HIPAA** for biomedical telemetry on US-crewed missions.
- **OSCAL** for the policy + audit artifacts (the existing Civium → Aletheia bridge pattern).
- **OMB M-25-22** (AIBOM) — the suit's AI components must produce a Robot AIBOM (extension of M-25-22 to embodied systems, currently in the 90-day plan).

A Phase 6 audit produces this evidence package as a deliverable. The active 90-day AIBOM plan is therefore the *prerequisite* to a defensible interplanetary suit Phase-6 sign-off. The ordering matters.

### FTO re-check

No drift into others' claimed whitespace. The substrate moat (Aletheia DAC + MVCI + Civium + Mercury) is Zuup-internal. Shell prior art is consumed as engineering, not claimed.

### Bench-maxing self-audit

Out-of-distribution behavior: send the substrate decisions on scenarios not in any FMEA (e.g., a Marsquake-induced cascade failure not in the FMEA library). If the system collapses to safe-passive and logs the event for post-hoc human review, that is correct behavior — not a fail. If the system invents a confident-but-wrong autonomous action, the gate failed and the ACI band was miscalibrated. The benchmark itself must include at least one OOD scenario per family in the test suite.

### Honest statement of remaining limitations

1. **No working hardware.** Phase 5 is currently a substrate prototype path, not a built suit. A built suit requires industrial partnership.
2. **HF-3 (250 EVAs without resupply) is SPECULATIVE.** No accelerated-life precedent at this cadence. The 10× improvement target is plausible but not validated; this may be the floor that forces a v1.2 revision in 12–24 months.
3. **HF-10 (formally verified kernel) is SPECULATIVE.** Mercury's ISA is verifiable in principle; a flight-rated implementation is research-grade work. The path is real, but the engineering is non-trivial.
4. **HF-15 evidence package is contingent on the 90-day AIBOM plan.** The robotics-AIBOM extension is required before the suit's compliance evidence package is producible at standard.
5. **SPE shelter assumption (HF-6).** If operational reality precludes an external shelter, the floor is invalid and a sub-meter polyethylene shielding capability must be added — large mass impact.

These are named so they are not absorbed silently. The discipline is to flag, not to hide.

---

## Forward Edges and Loop Triggers

Per ZCS-6 canon, the legal back-edges are:

- **Phase 6 → Phase 5.** Any seam attack producing an actionable finding triggers a substrate code revision.
- **Phase 6 → Phase 2.** If the Phase-6 pass surfaces a benchmark dimension that v1.1 missed, v1.2 is committed with delta justification. No silent floor revisions.
- **Phase 5 → Phase 1.** Reserved for the (currently unlikely) discovery that the substrate convergence whitespace is occupied by undisclosed prior art. Low probability but non-zero.

Forward edge from here: Phase 5 working-code milestone — a terrestrial substrate prototype with red-team test suite, runnable on Jetson-class hardware. ~3-month build on the existing MVCI + Aletheia + Mercury stack. This becomes the IP demonstration and the procurement-package input for hardware partner conversations.

---

## Summary

The interplanetary spacesuit problem, after first-principles deconstruction, is not a shell engineering problem. It is a **compliance-graded autonomous decision substrate problem embodied in a pressure shell.** The shell engineering is real but bounded by prior art; the substrate is the unclaimed convergence vector.

ZCS-6 applied:
- **Phase 1 (Whitespace, PLAUSIBLE):** Multi-mode shell + compliance-graded autonomous substrate + cryptographic provenance — unclaimed convergence, FTO-clear, internal prior art on the substrate side.
- **Phase 2 (Benchmark):** VBX-ISPS-BENCH-v1.0 with 10 hard-fail floors and a drift clause, machine-readable JSON, trivial-pass strategies flagged.
- **Phase 3 (Attack):** 5 attack classes executed; 5 new floors added (HF-11 through HF-15); 3 existing floors hardened. v1.1 ready for re-commit.
- **Phase 4 (Defend):** v1.0 cryptographically committed at SHA-256 `ac6114a4c0a025f86926fe2d3f95d36a5a8b4796b2893ce58e22df488f7fd861`. Goalpost frozen. No passing system among current incumbents.
- **Phase 5 (Build):** Three-layer architecture (Shell / Substrate / Sovereignty) committed. Substrate buildable today on existing MVCI + Aletheia + Mercury stack; shell is a 5–8 year industrial program. Working-code milestone defined.
- **Phase 6 (Vertical attack):** 8-seam attack surface enumerated; 5 stress dimensions specified; compliance evidence map drawn; 5 honest limitations named.

The discipline holds. The benchmark precedes the solution. The chain is auditable. The seams are named.

When you say *proceed to substrate prototype*, Phase 5 begins.

---

*End of VBX-ISPS ZCS-6 v1.0 application document.*
