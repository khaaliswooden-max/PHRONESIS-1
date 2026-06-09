# Changelog

All notable changes to VBX-ISPS · PHRONESIS-M are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), with extensions for cryptographic ledger commits and epistemic markers. Each release links to a ledger entry that cryptographically binds the artifacts included in that release.

This project follows a falsification-first version discipline:
- The **benchmark** is the binding artifact and is versioned independently from the substrate
- The **substrate** is versioned independently and may iterate against a fixed benchmark
- Each release produces a **ledger entry** with a merkle root over the included files
- The current ledger head is **LEDGER #0005** with root `e77e79a02d836345cc35d9105862f0fb8c42b1c64fdd2af32c4646b53389e655`

---

## [Unreleased] — v0.2-β candidate

### Planned (see ROADMAP.md for full)

- Lean 4 machine-checkable proof of Mercury kernel WCET=5 cycle bound
- HF-10 full closure (replacing v0.2-α informal proof)
- OpenTimestamps anchor + ground replication of chain witness
- Standalone chain integrity replay CLI
- ACI live-pipeline integration (off demo mode)
- C-3 closure (AIBOM CycloneDX 1.6 + SPDX 2.3 schema validation)

### Epistemic posture

- All v0.2-β items have VERIFIED scope. Implementation is in flight.
- v0.2-β is pure software work; no external dependencies.

---

## [v0.2-α] — 2026-06-09 · LEDGER #0005

### Added — LLM inference integration

- **Civium LLM adapter** `CiviumLLMAdapter` abstraction with two concrete implementations:
  - `OllamaMistralAdapter` — canonical production adapter (Ollama + Mistral-7B-Instruct Q4). Not exercised in test suite; production-deployment-ready
  - `TransformersHFAdapter` — sandbox adapter using HuggingFace transformers + Qwen2.5-0.5B-Instruct. Used in test suite to demonstrate the architecture without production-class hardware
- **Real teacher-forced log-probability extraction.** For each of 8 decision-class options, the adapter computes log P(option | prompt) by teacher-forcing the option text through the model and summing token log-probs. The 8 log-probs are softmaxed to a posterior; the argmax is the recommendation; the top probability is the confidence.
- **AIBOM provenance fields** added to chain `INFERENCE_RECOMMENDATION` entries: model_hash, prompt_hash, logprob_summary, sampler_config, adapter_version. Aligns with OMB M-25-22 Annex C AI Bill of Materials.
- **Defense-in-depth Tier 1 / Tier 2 architecture.** Tier 1 floors (physical-validity, safety-critical thresholds) are deterministic and unconditional. Tier 2 (LLM-driven) operates only in the nuanced band. LLM cannot override emergencies. VERIFIED v0.2-α.

### Changed

- **HF-12 re-measurement** with stratified 6-scenario nuanced-band test. Sandbox confidences in narrow band (0.430–0.443) due to small-model artifact. Threshold load-bearing: 0.40→1.000 autonomy share, 0.50→0.000.
- **Civium ACI** path remains demo-only in v0.2-α; live-pipeline integration deferred to v0.2-β.

### Documented

- **Sandbox latency:** 33.5 s/inference on CPU (test environment).
- **Production projection:** 1–3 s on Jetson Orin NX + Mistral-7B-Instruct Q4_K_M (PLAUSIBLE planning estimate; benchmark TBD).
- **PHI encryption** posture: Fernet symmetric encryption in v0.2-α. HSM/KMS gated on v0.3.

### Test coverage

- 51/51 tests passing
- 43 baseline tests from v0.1.1
- 8 new LLM integration tests covering adapter abstraction, teacher-forcing correctness, AIBOM population, and defense-in-depth invariant under LLM-driven decisions

### Ledger entry

- LEDGER #0005 root: `e77e79a02d836345cc35d9105862f0fb8c42b1c64fdd2af32c4646b53389e655`
- Artifacts: substrate v0.2-α tarball, V02_ALPHA_REPORT.md, hf12_remeasure_results.json
- Predecessor: LEDGER #0004

### Reports

- `reports/V02_ALPHA_REPORT.md` — full v0.2-α design and measurement
- `substrate/v02_alpha/hf12_remeasure_results.json` — re-measurement raw data

---

## [v0.1.1] — 2026-06-08 (later) · LEDGER #0004

### Phase 6 vertical-integration attack — 13 findings; 12 closed in this release; 2 deferred

The substrate v0.1 was attacked at the integration boundary. 13 findings were identified (8 HIGH, 5 MEDIUM). 12 architecture-level mitigations are included in v0.1.1.

### Fixed (Phase 6 architecture-level findings)

- **S-1 — Unknown decision class.** Gate now refuses to evaluate an unknown decision class and dispatches SAFE_PASSIVE_FALLBACK with an UNKNOWN_DECISION_CLASS chain entry.
- **S-2 — Policy mutation between load and evaluation.** Per-decision policy file hash check. POLICY_INTEGRITY_VIOLATION chain entry on mismatch; hard safe-passive dispatch.
- **S-3 — Bus state mutability.** Internal bus state name-mangled (`__state`) to prevent direct mutation; bus.write requires privilege token.
- **S-4 — Token namespace.** Privilege token generated at boot time via `secrets.token_hex(32)`. Deprecated module-level constant fails verification.
- **S-5 — Concurrency.** `threading.Lock` on chain append to prevent interleaved writes; tested with concurrent injection.
- **S-6 — Timestamp gaming.** Chain entry records *two* timestamps: `chain_ingress_ts` (substrate-issued) and `sensor_reported_ts` (sensor-provided). Sensor cannot game the chain ts.
- **S-7 — NaN/Inf propagation.** Sensor reading sanitization at ingress; NaN/Inf trips SENSOR_FAULT_SUSPECTED.
- **C-1 — PHI plaintext.** Fernet-encrypted PHI in biomedical alert chain entries. Plaintext PHI no longer possible.
- **C-3 — AIBOM fields (partial).** Civium recommendation includes model_hash, prompt_hash, logprob_summary on chain. Schema validation deferred to v0.2-β.
- **O-1 — Sensor fault routing.** Sensor faults route to SAFE_PASSIVE_FALLBACK with SENSOR_FAULT_SUSPECTED chain entry, not silently dropped.
- **O-2 — Multi-fault dispatch.** Multiple simultaneous safety floors deterministically dispatch to the most-restrictive outcome with all chain entries logged.
- **O-3 — Chain truncation witness.** Witness file (`chain.witness`) written on every append. Truncation produces witness-vs-head mismatch detectable in linear time.

### Deferred

- **C-2 — Filesystem ACL.** Custody of `chain.db` and `key.pem` ACLs is operator responsibility, not enforced by code. Documented in SECURITY.md.
- **FTO-1 — Patent FTO snapshot.** Pending patent practitioner engagement (per 90-day plan).

### Test coverage

- 43/43 tests passing (up from 31 in v0.1)
- 12 new tests directly exercising Phase 6 findings

### Ledger entry

- LEDGER #0004 root: `b123bc28b0f23a65ec9ce221ac07f714e5a3a6cd7e340c408245d2957fff9bfe`
- Artifacts: substrate v0.1.1 tarball, PHASE6_REPORT.md, phase6_findings.json (round 1 + round 2)
- Predecessor: LEDGER #0003

### Reports

- `reports/PHASE6_REPORT.md` — full attack and closure report
- `substrate/phase6_attacks/` — attack scripts (reproducible)

---

## [v0.1] — 2026-06-08 · LEDGER #0003

### Initial substrate implementation against benchmark v1.1

First substrate that passes the substrate-scope hard-fail floors of VBX-ISPS-BENCH v1.1.

### Added

- **Aletheia chain.** Ed25519-signed, hash-linked, SQLite-backed append-only chain. Genesis entry; subsequent entries link to predecessor hash.
- **MVCI gate.** Three-level classification (AUTONOMOUS_ELIGIBLE / REQUIRES_HUMAN / SAFETY_CRITICAL) driven by policy file. Routing logic by level + comm state.
- **Mercury kernel.** Subleq single-instruction-set VM. Deterministic 5-cycle WCET informal proof. Bus actuation under privilege token.
- **Civium adapter scaffolding.** Abstract LLM adapter interface; placeholder concrete implementation. (Real LLM integration in v0.2-α.)
- **Bus isolation.** Privileged-write safety bus. Software surrogate for v1.0 hardware silicon.
- **Biomedical alert pipeline.** HF-13 path: sensor → chain ingress → encrypted PHI payload → HUD alert. Latency budget 5 s.
- **Runner.** `process_event` top-level pipeline tying all components.
- **Policy file v0.1.** `policy/isps_policy_v0_1.json` with 8 decision classes mapped to levels.

### Test coverage

- 31/31 tests passing
- Tests cover: chain integrity, gate routing, kernel determinism, bus privilege, biomedical encryption

### Ledger entry

- LEDGER #0003 root (substrate v0.1 commit)
- Predecessor: LEDGER #0002

### Reports

- `reports/BENCHMARK_RESULTS_v0_1.md` — measured results
- `reports/GAP_ANALYSIS.md` — honest gaps documented

---

## [Benchmark v1.1] — 2026-06-08 (earlier) · LEDGER #0002

### Hardened benchmark with 15 scope-partitioned hard-fail floors

After the v1.0 benchmark was attacked in Phase 3, 15 hard-fail floors were defined with explicit scope partition (7 substrate + 8 shell). v1.1 is the version that the substrate is built against in v0.1 and beyond.

### Added

- 15 hard-fail floors HF-1 through HF-15
- Scope partition annotations (substrate vs shell)
- Reference-system scoring metadata (xEMU/AxEMU baselines)
- Cryptographic commitment

### Frozen for v1.x major version

- SHA-256: `58bf8744d3cc78b1cb7bb88464edb7df796187c45cea1ae483e936249803c1c5`
- This hash is verified in CI on every commit
- Changes require a new minor version (v1.2) with documented delta and fresh ledger commit

### Ledger entry

- LEDGER #0002 root (benchmark v1.1 commit)
- Predecessor: LEDGER #0001

### Reports

- `benchmark/VBX_ISPS_DELTA_v1_0_to_v1_1.md` — delta from v1.0
- `benchmark/VBX_ISPS_BASELINES_v1_1.md` — reference-system scoring

---

## [Benchmark v1.0] — 2026-06-08 (earliest) · LEDGER #0001

### Initial benchmark · Phase 2 falsification artifact

The originating commitment. v1.0 is the cryptographically committed benchmark from which all subsequent work flows. Per the ZCS-6 methodology, the benchmark must precede the solution.

### Added

- Initial 12 floors covering the substrate-scope decision-substrate properties
- Problem statement: an interplanetary-class spacesuit decision substrate
- Cryptographic commitment

### Ledger entry

- LEDGER #0001 root (genesis benchmark commit)
- Predecessor: none (genesis)

### Note

v1.0 was attacked in Phase 3 and discovered to have scope-partition ambiguity (substrate vs shell). v1.1 hardened this. v1.0 is preserved in the repository for completeness but is **not the current binding benchmark**.

---

## Versioning policy

- **Benchmark versions** (v1.0, v1.1, v1.2, …): major version increment requires a Phase 1 re-entry with a documented deficiency in the prior major. Minor versions are refinements within the same problem framing.
- **Substrate versions** (v0.1, v0.1.1, v0.2-α, v0.2-β, v0.3, v1.0, …): semantic versioning with the convention that v0.x is research/development, v1.0 is the first flight-credible substrate, v2.0 is the first mission-credible substrate.
- **Greek letter suffixes** (α, β, γ): pre-release within a substrate minor version. v0.2-α is the first iteration of v0.2; v0.2-β is the next, etc.

Each release produces a new ledger entry. Each ledger entry's root binds the version cryptographically.

---

## How to read a ledger entry

A ledger entry (`ledger/VBX_ISPS_LEDGER_NNNN.json`) contains:

```json
{
  "ledger_seq": NNNN,
  "ts_utc": "2026-MM-DDTHH:MM:SSZ",
  "predecessor_root": "<sha-256 of LEDGER NNNN-1>",
  "version_tag": "v0.2-alpha",
  "artifacts": [
    { "path": "substrate/", "manifest_sha256": "..." },
    { "path": "reports/V02_ALPHA_REPORT.md", "sha256": "..." }
  ],
  "merkle_root": "<sha-256 over the entries above>",
  "signed_by": "A. Khaalis Wooden, Sr.",
  "signature_alg": "Ed25519",
  "signature": "<base64>"
}
```

To verify a ledger entry:
1. Compute the SHA-256 of each listed artifact.
2. Reconstruct the merkle root from the artifacts.
3. Verify the Ed25519 signature against the project's public key.
4. Verify that `predecessor_root` matches the SHA-256 of LEDGER NNNN-1.

This is the cryptographic spine of the version history.

— A. Khaalis Wooden, Sr.
— Visionblox LLC / Zuup Innovation Lab
