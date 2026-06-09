# VBX-ISPS Substrate Prototype

**Compliance-graded autonomous decision substrate for an interplanetary spacesuit life-support system.**

Version: 0.1 (first runnable, ZCS-6 Phase 5)
Author: A. Khaalis Wooden, Sr., MBA; MSIT Candidate, Southern New Hampshire University
Entity: Visionblox LLC / Zuup Innovation Lab
Contract: VBX-ISPS-BENCH-v1.1 (SHA-256 `58bf8744d3cc78b1cb7bb88464edb7df796187c45cea1ae483e936249803c1c5`)

---

## What this is

A working substrate prototype that demonstrates the seven substrate-scope hard-fail floors of the VBX-ISPS-BENCH-v1.1 benchmark can be addressed on commodity hardware. It is the result of ZCS-6 Phase 5 ("build the solution") executed against a Phase 4 committed benchmark (LEDGER #0002).

The substrate is the IP moat. The shell is engineering. v0.1 ships the substrate; v1.2 of the benchmark engages a hardware partner for shell-scope floors.

## Architecture

Five layered components, all runnable in Python on a Jetson-class or laptop-class device:

```
   PLSS telemetry
        |
        v
   [Civium]      compliance-graded inference (rule-based stub in v0.1; Mistral-7B in v0.2)
        |
        v
   [MVCI Gate]   policy-driven approval classification
        |
        +--> AUTONOMOUS_ELIGIBLE --> autonomous execution -----+
        |                                                      |
        +--> REQUIRES_HUMAN ----- approved/rejected/blackout -+
        |                            |                         |
        |                            v                         |
        |                       safe-passive fallback ---------+
        |                                                      |
        +--> SAFETY_CRITICAL --> [Mercury Subleq kernel] ---> [Bus]
                                  formally bounded WCET         |
                                  hardware-isolated             |
                                                                v
                                                          actuation
        |
        v
   [Aletheia]    append-only Ed25519-signed hash-chained ledger
                 every decision attempt, signed, replay-verifiable
```

| Module | Path | Role |
|---|---|---|
| Aletheia | `src/aletheia/chain.py` | Append-only Ed25519-signed ledger, SQLite-backed |
| Mercury | `src/mercury/subleq.py` | Single-instruction VM + O2 control loop + WCET harness |
| MVCI | `src/mvci/gate.py` | Policy-driven gate with safe-passive fallbacks |
| Civium | `src/civium/aci.py`, `src/civium/inference.py` | Adaptive Conformal Inference + inference layer (v0.1 stub) |
| Biomedical | `src/biomedical/alerts.py` | Latency-budget alert pipeline |
| Isolation | `src/isolation/bus.py` | Software surrogate for hardware safety-bus enforcement |
| Runner | `src/runner/simulate.py` | End-to-end PLSS event pipeline |

## ZCS-6 frame

This repo is a Phase 5 artifact:

- **Phase 1 (whitespace):** Substrate convergence (compliance-graded autonomous decisions under deep-space latency, with cryptographic provenance, hardware-isolated kernel, and drift-aware confidence) is unsolved across xEMU, AxEMU, EMU, Z-2, and all announced suit programs.
- **Phase 2 (benchmark v1.0):** LEDGER #0001 — `4b64f9d6…`
- **Phase 3 (attack):** Five trivial-pass holes in v1.0, five new floors from cross-investigator attacks.
- **Phase 4 (re-commit v1.1):** LEDGER #0002 — `f15f68fc37f8026d0b3ef31759b25a2bf77e4a268089985f094595a5c1902d08`
- **Phase 5 (this repo):** v0.1 substrate. 31/31 tests passing against substrate-scope floors. Two real bugs surfaced and fixed during build (subleq control flow; ACI sign error).
- **Phase 6 (pending):** Vertical-integration attack — seam analysis, out-of-distribution behavior, FTO re-check.

## Build and run

Tested on Python 3.12 / Linux. Dependencies are minimal: `cryptography`, `numpy`, `pytest`. SQLite is in stdlib.

```bash
pip install --break-system-packages cryptography numpy pytest
cd substrate
python -m pytest tests/ -v
```

Expected: 31 passed.

For deeper inspection of any single floor:

```bash
# HF-8 chain integrity, red-team injection, tamper detection
python -m pytest tests/test_chain.py -v

# HF-9 approval gate including 1000-scenario adversarial blackout
python -m pytest tests/test_gate.py -v

# HF-10 kernel correctness, WCET, bus isolation, penetration test
python -m pytest tests/test_kernel.py -v

# HF-12 autonomy ratio on 10k stratified scenarios
python -m pytest tests/test_autonomy.py -v

# HF-13 biomedical alert latency
python -m pytest tests/test_alert_latency.py -v

# HF-14 kernel re-verification process audit
python -m pytest tests/test_kernel_reverify.py -v

# HF-15 compliance evidence package structural check
python -m pytest tests/test_compliance_pack.py -v

# Drift clause: static CI collapse vs ACI hold
python -m pytest tests/test_drift.py -v
```

## Confidence markers on v0.1

Per ZCS-6 epistemic discipline, every component carries a marker:

| Component | Marker | Notes |
|---|---|---|
| Aletheia chain | **VERIFIED** | Production-grade signing + integrity; 0 defects across 1000-event runs |
| MVCI gate | **VERIFIED** | All adversarial cases pass; policy file binding by SHA-256 |
| Mercury Subleq | **PLAUSIBLE** | WCET measured deterministic; formal verification deferred to v0.2 |
| Hardware isolation | **PLAUSIBLE** | Software surrogate; silicon enforcement deferred to v0.2 |
| Civium ACI | **PLAUSIBLE** | Reproduces Aletheia headline on one of five named distributions |
| Civium inference | **SPECULATIVE** | Rule-based stub; Mistral-7B integration is v0.2 work |
| Biomedical alerts | **VERIFIED** | p99 latency 1300× under budget |
| HF-15 evidence package | **PLAUSIBLE** | Structural mapping complete; underwriter dry-run deferred |

## Where v0.1 passes the benchmark

| Floor | Status |
|---|---|
| HF-8 — Decision provenance | **PASS** |
| HF-9 — Approval gate integrity | **PASS** |
| HF-10 — Deterministic kernel + HW isolation | **PASS-WITH-CAVEAT** (FV deferred; isolation = software surrogate) |
| HF-12 — Effective autonomy ratio | **PASS-WITH-CAVEAT** (rule-based inference inflates rate) |
| HF-13 — Biomedical alert latency | **PASS** |
| HF-14 — Kernel re-verification | **PASS** |
| HF-15 — Compliance evidence package | **PASS** (structural; underwriter dry-run deferred) |
| Drift clause | **PASS** (1 of 5 distributions; extension deferred) |

5 outright pass + 2 pass-with-caveat. 0 fail. See `BENCHMARK_RESULTS_v0_1.md` for measured numbers and `GAP_ANALYSIS.md` for v0.2 prerequisites.

## Related artifacts

Outside this repo, the ZCS-6 chain comprises:

- `vbx_isps_bench_v1_0.json` — originating benchmark (LEDGER #0001)
- `vbx_isps_bench_v1_1.json` — operational contract (LEDGER #0002)
- `VBX_ISPS_DELTA_v1_0_to_v1_1.md` — Phase 3 hardening justification
- `VBX_ISPS_BASELINES_v1_1.md` — systematic baseline scan (no reference system passes)
- `VBX_ISPS_LEDGER_0001.json`, `VBX_ISPS_LEDGER_0002.json` — chain commits
- (this repo's chain commit) — `VBX_ISPS_LEDGER_0003.json` covering v0.1 substrate

## Epistemic discipline

This work follows ZCS-6 falsification-first methodology. The benchmark was cryptographically committed before the solution existed. Bugs surfaced in v0.1 (Mercury control flow, ACI sign error) were fixed at the architecture level, not by softening floors. Every claim about v0.1 carries a confidence marker. Honest revisions downward are features, not failures.

Public substrate code is shareable under Apache 2.0 (v0.2 will add explicit LICENSE). Pre-commercial IP claims for the cross-modal compliance fabric (procurement AI / physical AI / clinical AI as unified system-and-method) remain with Visionblox LLC.

---

*VBX-ISPS Substrate v0.1 — Visionblox LLC / Zuup Innovation Lab.*
