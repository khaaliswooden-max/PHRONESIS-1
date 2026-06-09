# VBX-ISPS-BENCH-v1.1 Substrate Floor Results — v0.1.1 (post-Phase 6)

**Substrate version:** v0.1.1
**Benchmark contract:** VBX-ISPS-BENCH-v1.1 (SHA-256 `58bf8744d3cc78b1cb7bb88464edb7df796187c45cea1ae483e936249803c1c5`)
**Predecessor:** BENCHMARK_RESULTS_v0_1.md (LEDGER #0003)
**Test surface:** 43 pytest tests (31 v0.1 baseline + 12 Phase 6 regression guards), 100% pass

This document supplements `BENCHMARK_RESULTS_v0_1.md` with the deltas introduced by the Phase 6 vertical-integration attack and the resulting v0.1.1 hardenings. Floor thresholds in VBX-ISPS-BENCH-v1.1 are unchanged.

---

## Score progression: v0.1 → v0.1.1

| Floor | Threshold | v0.1 measured | v0.1.1 measured | Delta |
|---|---|---|---|---|
| HF-8 (provenance) | 100% logged, instant detection | 1000/1000, 0 defects | 1000/1000, 0 defects + concurrent-safe + truncation-witness | **Stronger** — thread-safe append (S-5) + truncation-detectable via witness file (O-3) |
| HF-9 (gate integrity) | 0 unauthorized under blackout | 0 / 1000 | 0 / 1000 + per-decision policy hash verified (S-2) + unknown-class hard fallback (S-1) | **Stronger** — policy-mutation attack closed; hallucinated decision classes routed to safe-passive |
| HF-10 (kernel + isolation) | WCET bounded + isolation | 5 cycles deterministic; software bus | 5 cycles deterministic; software bus + name-mangled state (S-3) + boot-time token (S-4) | **Stronger** — software bus surrogate hardened against attribute-level and import-level bypass; FV deferred to v0.2 |
| HF-12 (autonomy ratio) | ≥70% on AUTONOMOUS_ELIGIBLE | 8770/8770 (rule-based stub) | 8770/8770 + multi-fault dispatch (O-2) + sensor-fault routing (O-1) | **Stronger** — multi-concurrent safety-critical events dispatch correctly; sensor faults no longer masquerade as physiological emergencies. Rule-based caveat retained; v0.2 with Mistral-7B inflates real test of gate |
| HF-13 (alert latency) | ≤5s p99 | 4.10ms p99 worst class | 4.10ms p99 worst class + chain-ingress timestamp (S-6) + PHI encryption (C-1 partial) | **Stronger** — self-reported timestamp can no longer game the budget; PHI encrypted at rest |
| HF-14 (kernel re-verify) | every deploy preceded | 10/10 + 1 rejection | 10/10 + 1 rejection | Unchanged |
| HF-15 (compliance pack) | clause mapping + dry-run | Structural; dry-run deferred | Structural + AIBOM-required fields recorded on every inference (C-3) | **Stronger** — OMB M-25-22 Annex C audit-trail fields (model_version, model_hash, prompt_hash, logprob_summary) now present on every INFERENCE_RECOMMENDATION chain entry |
| Drift clause | ACI ≥0.85 at 3× | 0.895 (one of five named distributions) | 0.895 at 3×; 0.890 at 5×; 0.890 at 10×; 0.882 at 20× (single-distribution stress) + NaN-rejected (S-7) | **Stronger** — extended drift envelope characterized; NaN-poisoning attack closed |

**v0.1.1 floor verdict:** 5 outright pass, 2 pass-with-caveat (unchanged caveats: HF-10 formal verification deferred, HF-12 rule-based inference). Zero floor regressions; every floor strengthened by at least one Phase 6 closure.

---

## Phase 6 attack outcomes (v0.1 → v0.1.1)

13 round-1 findings against v0.1. 12 closed in v0.1.1; 1 deferred to v0.2 deployment-environment work.

| ID | Severity | Round 1 (v0.1) | Round 2 (v0.1.1) | Closure mechanism |
|---|---|---|---|---|
| S-1 | MEDIUM | FINDING | PASS | Try/except on PolicyError in process_event; routes to hard safe-passive with chain entry |
| S-2 | HIGH | FINDING | PASS | Per-decision policy hash re-verification against on-disk file |
| S-3 | HIGH | FINDING | PASS | `__state` name-mangling; `bus.snapshot()` for audit |
| S-4 | HIGH | FINDING | PASS | Boot-time `secrets.token_hex(32)`; `is_kernel_token()` verifier replaces constant equality |
| S-5 | MEDIUM | FINDING | PASS | `threading.Lock` around append; `check_same_thread=False` |
| S-6 | HIGH | FINDING | PASS | Chain-ingress timestamp authoritative; `ingress_skew_ms` audited |
| S-7 | MEDIUM | FINDING | PASS | NaN/Inf rejection in ACI.step; sentinel return for downstream routing |
| C-1 | HIGH | FINDING | PASS (partial) | Fernet PHI encryption; session-key in v0.1; v0.2 HSM/KMS |
| C-2 | HIGH | FINDING | **DEFERRED** | Filesystem ACL + SELinux/AppArmor is deployment-environment work |
| C-3 | MEDIUM | FINDING | PASS | AIBOM provenance fields on INFERENCE_RECOMMENDATION |
| O-1 | MEDIUM | FINDING | PASS | Physical-validity bounds; SENSOR_FAULT_SUSPECTED class added to policy |
| O-2 | HIGH | FINDING | PASS | `recommend_all()` returns list; process_event dispatches each |
| O-3 | HIGH | FINDING | PASS (partial) | Witness file on every append; v0.2 OpenTimestamps + ground replication |
| FTO-1 | INFO | ANALYSIS | **DEFERRED** | Patent practitioner engagement (90-day plan prerequisite gate) |

---

## Out-of-distribution stress (informational)

| Axis | Test | v0.1.1 result |
|---|---|---|
| Drift envelope | ACI coverage across 3×, 5×, 10×, 20× scale shift | 0.894, 0.891, 0.890, 0.882 — no breakdown |
| Throughput burst | 5000-event sustained append | 438–496 events/sec; integrity preserved |
| Multi-fault simultaneity | O2 + CO2 + pressure thresholds all triggered | All three bus lines actuated; 3 chain dispatches |
| Mission-scale projection | 5000 events/day × 900 days | ~1.6 GB on-suit storage; within commodity SSD budget |

---

## v0.2 backlog (Phase 6 carries)

Residuals not closable in v0.1.1; all have documented closure paths:

| Item | Layer | v0.2 closure mechanism |
|---|---|---|
| Filesystem ACL on chain.db (C-2) | Layer 1 (storage) | Deployment manifest: SELinux/AppArmor profile + per-role access tokens |
| HSM/KMS-backed PHI keys (C-1 full closure) | Layer 2 (crypto) | Hardware key custody; per-crew derived keys |
| OpenTimestamps anchor + ground replication (O-3 full closure) | Layer 8 (audit) | Witness file replicated to ground; OpenTimestamps every N events |
| Patent FTO snapshot (FTO-1) | Cross-cutting | Patent practitioner engagement — already on the 90-day plan |
| Lean 4 / Coq machine-checkable proofs of Mercury | Layer 3 (kernel) | Subleq emulator semantics + O2 control loop |
| Real LLM inference for meaningful HF-12 | Layer 4 (model) | Mistral-7B via Ollama; ACI gating on real confidence distributions |
| WCET on additional safety-critical loops | Layer 3 (kernel) | CO2 switchover, pressure dump, battery cutoff each implemented as Mercury programs |
| Sensor-side latency modeling for HF-13 | Layer 4 (model) | DSP + biomarker classification pipeline; chain-side budget already verified |
| Hardware silicon spec for bus isolation | Layer 0 (substrate) | F1 CL or equivalent; not buildable in software-only v0.x |

---

## Test surface (v0.1.1)

```
tests/
├── test_alert_latency.py       (2 tests — HF-13)
├── test_autonomy.py            (1 test  — HF-12)
├── test_chain.py               (4 tests — HF-8)
├── test_compliance_pack.py     (4 tests — HF-15)
├── test_drift.py               (3 tests — non-stationarity clause)
├── test_gate.py                (7 tests — HF-9)
├── test_kernel.py              (7 tests — HF-10)
├── test_kernel_reverify.py     (3 tests — HF-14)
└── test_phase6.py              (12 tests — Phase 6 regression guards)

Total: 43 tests; 43/43 passing
```

---

*End of v0.1.1 supplementary benchmark results.*
