# VBX-ISPS · PHRONESIS-M

**Interplanetary Spacesuit · Compliance-Graded Autonomous Decision Substrate**

[![Substrate](https://img.shields.io/badge/substrate-v0.2--α-orange)](./CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-51%2F51-brightgreen)](./substrate/tests/)
[![Methodology](https://img.shields.io/badge/methodology-ZCS--6-blue)](./EPISTEMIC_FRAMEWORK.md)
[![Phase](https://img.shields.io/badge/phase-6%20closed-green)](./reports/PHASE6_REPORT.md)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](./LICENSE)

---

## What this is

**PHRONESIS-M** is the substrate of an interplanetary-class spacesuit decision system. The name is taken from Aristotle's φρόνησῐς — *practical wisdom*, the virtue of knowing what to do in particular situations under uncertainty when stakes are real. The substrate makes safety-critical life-support decisions on behalf of crew operating at deep-space communication latency (up to 22 light-minutes round-trip from Earth), with cryptographic provenance for every decision attempt, formally bounded deterministic actuation, drift-aware confidence calibration, and documented embodied-AI compliance evidence.

This is not a spacesuit shell — pressure garments, joint bearings, life-support thermodynamics, and dust mitigation are well-characterized engineering with vendor heritage from Apollo through xEMU/AxEMU. What this repository contains is the **substrate convergence** — the unsolved engineering surface that becomes load-bearing for any mission beyond cis-lunar space.

> **TL;DR.** Pressure garments are solved. Life-support thermodynamics is solved. What is *not* solved is autonomous compliance-graded decision-making for life support at deep-space latency, with cryptographic audit trails, formally verified safety kernels, drift-resistant confidence, and underwriter-grade evidence packages. That convergence is the IP moat. The shell is engineering; the substrate is the contribution.

## Project identity

| Field | Value |
|---|---|
| Project identifier | VBX-ISPS (Visionblox Interplanetary Spacesuit) |
| Suit family name | PHRONESIS |
| Mars-class model | PHRONESIS-M |
| Methodology | ZCS-6 (Zuup Creative Stack, six phases — falsification-first) |
| Benchmark | VBX-ISPS-BENCH v1.1 (SHA-256 `58bf8744…03c1c5`) |
| Substrate version | v0.2-α (LEDGER #0005, commit root `e77e79a0…89e655`) |
| Designer | A. Khaalis Wooden, Sr. (MBA; MSIT Candidate, SNHU) |
| Affiliation | Visionblox LLC / Zuup Innovation Lab |
| License | Apache License 2.0 |

## Architecture (Phronesis Core)

The substrate consists of five named components colocated on a single ~2 kg compute module (Jetson Orin NX in production), housed within the PLSS backpack:

| Component | Role | Status |
|---|---|---|
| **Aletheia** | Append-only cryptographically signed provenance chain (Ed25519, SHA-256, SQLite-backed, witness file) | v0.2-α VERIFIED |
| **MVCI** | Policy-driven approval gate with three-level classification (AUTONOMOUS_ELIGIBLE / REQUIRES_HUMAN / SAFETY_CRITICAL) | v0.2-α VERIFIED |
| **Mercury** | Subleq single-instruction-set VM kernel for safety-critical actuation (5-cycle deterministic WCET) | v0.2-α VERIFIED (informal proof); v0.2-β adds Lean 4 machine-checkable proof |
| **Civium** | LLM inference adapter with teacher-forced log-prob extraction + ACI calibration (Mistral-7B-Instruct production / Qwen2.5-0.5B-Instruct sandbox) | v0.2-α VERIFIED architecture; v0.3 swaps to production Mistral-7B |
| **Bus isolation** | Privileged-write safety bus with boot-time secret token (software surrogate; v1.0 silicon-enforced) | v0.2-α VERIFIED (software); hardware partner work for silicon |

The pipeline is **deterministic → probabilistic → deterministic**: hard physical-validity and safety-critical floors run first and can bypass the LLM entirely when emergencies fire. The LLM is consulted only in the nuanced decision band. Every decision attempt — including timeouts, integrity violations, and fallbacks — produces a signed chain entry.

See `blueprints/phronesis_flow_002.png` for the decision-flow architecture sketch.

## Repository layout

```
vbx-isps/
├── README.md                            ← you are here
├── LICENSE                              Apache 2.0
├── CONTRIBUTING.md                      contribution policy + IP terms
├── CODE_OF_CONDUCT.md                   behavioral expectations
├── SECURITY.md                          vulnerability disclosure
├── GOVERNANCE.md                        decision authority
├── ROADMAP.md                           version timeline v0.2-β → v2.0
├── CHANGELOG.md                         version-by-version with ledger commits
├── CITATION.cff                         citation metadata
├── EPISTEMIC_FRAMEWORK.md               ZCS-6 + VERIFIED/PLAUSIBLE/SPECULATIVE
├── CLAUDE.md                            instructions for AI collaborators
│
├── benchmark/                           cryptographically committed benchmark
│   ├── vbx_isps_bench_v1_0.json         v1.0 originating
│   ├── vbx_isps_bench_v1_1.json         v1.1 hardened (current binding)
│   ├── VBX_ISPS_DELTA_v1_0_to_v1_1.md   delta justification
│   └── VBX_ISPS_BASELINES_v1_1.md       reference-system scoring
│
├── ledger/                              chain of commit manifests
│   ├── VBX_ISPS_LEDGER_0001.json        v1.0 benchmark commit
│   ├── VBX_ISPS_LEDGER_0002.json        v1.1 benchmark commit
│   ├── VBX_ISPS_LEDGER_0003.json        v0.1 substrate commit
│   ├── VBX_ISPS_LEDGER_0004.json        v0.1.1 Phase 6 closure
│   └── VBX_ISPS_LEDGER_0005.json        v0.2-α LLM integration
│
├── substrate/                           working code (v0.2-α)
│   ├── src/
│   │   ├── aletheia/                    chain + PHI encryption
│   │   ├── mvci/                        approval gate + policy
│   │   ├── mercury/                     subleq VM + WCET
│   │   ├── civium/                      ACI + inference + adapters/
│   │   │   └── adapters/                Ollama-Mistral + transformers-HF
│   │   ├── biomedical/                  alert pipeline
│   │   ├── isolation/                   bus surrogate
│   │   └── runner/                      process_event pipeline
│   ├── tests/                           51 tests · pytest
│   ├── policy/                          isps_policy_v0_1.json
│   ├── compliance/                      HF15_evidence_package.md
│   ├── phase6_attacks/                  Phase 6 attack scripts + findings
│   └── v02_alpha/                       HF-12 re-measurement
│
├── paper/                               IEEE submission
│   ├── VBX_ISPS_IEEE_Paper.pdf          8-page conference paper
│   ├── VBX_ISPS_IEEE_Paper.tex          IEEEtran LaTeX source
│   └── references.bib                   45 citations
│
├── reports/                             phase reports + analysis
│   ├── VBX_ISPS_ZCS6_v1.md              full ZCS-6 walkthrough
│   ├── BENCHMARK_RESULTS_v0_1.md        v0.1 measured results
│   ├── BENCHMARK_RESULTS_v0_1_1.md      v0.1.1 supplementary
│   ├── GAP_ANALYSIS.md                  v0.1 honest gaps
│   ├── PHASE6_REPORT.md                 vertical-integration attack report
│   └── V02_ALPHA_REPORT.md              LLM integration report
│
└── blueprints/                          engineering drawings
    ├── PHRONESIS_Blueprint_v0_1.md      8-part comprehensive blueprint
    ├── phronesis_blueprint.svg          DWG VBX-ISPS-001 (physical)
    ├── phronesis_blueprint.png          ↑ rendered 3200×2400
    ├── phronesis_flow_002.svg           DWG VBX-ISPS-002 (decision flow)
    └── phronesis_flow_002.png           ↑ rendered 3200×2400
```

## Quickstart

### Run the test suite

```bash
cd substrate
pip install cryptography pytest numpy
python3 -m pytest tests/ -v
# Expected: 51 passed
```

For the v0.2-α LLM integration tests, also install:
```bash
pip install transformers accelerate torch --index-url https://download.pytorch.org/whl/cpu
```

First run downloads Qwen2.5-0.5B-Instruct from HuggingFace Hub (~1 GB). LLM tests take ~5 minutes wall-clock.

### Verify chain integrity

```bash
cd substrate
python3 -c "
from src.aletheia.chain import AletheiaChain
from pathlib import Path
# point to your chain.db + key.pem
chain = AletheiaChain.open_or_create(Path('chain.db'), Path('key.pem'))
result = chain.verify_integrity()
print(f'integrity_ok={result[\"integrity_ok\"]}; entries={result[\"entry_count\"]}; defects={len(result[\"defects\"])}')
"
```

### Reproduce HF-12 re-measurement (v0.2-α)

```bash
cd substrate
python3 v02_alpha/hf12_remeasure.py
# Outputs: v02_alpha/hf12_remeasure_results.json
```

### Production deployment (Ollama + Mistral-7B)

```bash
# 1. Install Ollama on target hardware (Jetson Orin NX class)
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Pull the production model
ollama pull mistral:7b-instruct-q4_K_M

# 3. Start Ollama service
ollama serve  # or systemd unit

# 4. Swap adapter at instantiation site:
#    OllamaMistralAdapter() instead of TransformersHFAdapter()
```

## Documentation map

| Document | Purpose |
|---|---|
| [README.md](./README.md) | This document |
| [CHANGELOG.md](./CHANGELOG.md) | Version history with cryptographic ledger commits |
| [ROADMAP.md](./ROADMAP.md) | Forward plan v0.2-β through v2.0 |
| [EPISTEMIC_FRAMEWORK.md](./EPISTEMIC_FRAMEWORK.md) | ZCS-6 methodology + epistemic markers |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | How to contribute (gated; IP-aware) |
| [GOVERNANCE.md](./GOVERNANCE.md) | Decision authority + benchmark discipline |
| [SECURITY.md](./SECURITY.md) | Vulnerability disclosure + signing-key custody |
| [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) | Behavioral expectations |
| [CITATION.cff](./CITATION.cff) | Citation metadata |
| [CLAUDE.md](./CLAUDE.md) | Instructions for AI collaborators |
| [blueprints/PHRONESIS_Blueprint_v0_1.md](./blueprints/PHRONESIS_Blueprint_v0_1.md) | 8-part engineering blueprint |
| [paper/VBX_ISPS_IEEE_Paper.pdf](./paper/) | IEEE conference paper |
| [reports/PHASE6_REPORT.md](./reports/) | Phase 6 vertical-integration attack |
| [reports/V02_ALPHA_REPORT.md](./reports/) | v0.2-α LLM integration report |

## Current state (one-line)

**v0.2-α**, Phase 6 closed, 51/51 tests passing, LLM-driven HF-12 routing architecture verified with defense-in-depth invariant: hard safety floors are deterministic and the LLM cannot override emergencies.

## Honest scope

**What this repository delivers (substrate scope, v0.2-α VERIFIED):**
- Cryptographically signed decision provenance (Aletheia)
- Policy-driven approval gating with three-level classification (MVCI)
- Subleq single-instruction kernel with deterministic 5-cycle WCET (Mercury — informal proof; Lean 4 in v0.2-β)
- LLM inference adapter with real per-option log-probability posterior + ACI calibration (Civium)
- Software-surrogate bus isolation with boot-time secret token
- HIPAA Fernet PHI encryption (production HSM/KMS in v0.3)
- Chain truncation witness file (production OpenTimestamps anchor in v0.2-β)
- Phase 6 hardenings: 12 of 13 findings closed; 2 deferred to v0.2-β with documented closure paths

**What this repository does NOT deliver (shell scope, partner work, or v0.2-β residuals):**
- Pressure garment, PLSS thermodynamics, mobility joints, helmet, boots, radiation tiling, dust mitigation (HF-1 through HF-7, HF-11 — shell scope, deferred to v1.2 with hardware partner)
- Mistral-7B production model (canonical adapter is ready; deployment in v0.3)
- Lean 4 machine-checkable proofs of Mercury (v0.2-β; pure software work)
- HSM/KMS-backed PHI keys (v0.3)
- OpenTimestamps anchor + ground replication (v0.2-β)
- Hardware silicon for bus isolation (v1.0 with hardware partner)
- HF-15 underwriter dry-run (gated on v0.3)
- Calibration audit on a ≥1000-state labeled scenario library (v0.2-β / v0.3)
- Formal FTO patent snapshot (engagement on 90-day plan)

This list is exhaustive of v0.2-α residuals. See [ROADMAP.md](./ROADMAP.md) for closure mechanisms.

## Safety notice

**NOT FOR FLIGHT OR LIFE-SUPPORT DEPLOYMENT.** This repository contains a falsification-first substrate prototype under active development. The benchmark v1.1 is the binding contract; the substrate v0.2-α passes the substrate-scope floors with documented caveats. Production deployment for a real crewed mission requires:

- Mistral-7B production model swap + calibration audit (v0.3)
- Lean 4 machine-checkable proofs of Mercury kernel (v0.2-β)
- Hardware silicon for bus isolation (v1.0)
- HSM/KMS for PHI keys (v0.3)
- OpenTimestamps anchor + ground replication (v0.2-β)
- Industrial test facility validation for shell-scope floors (v1.2)
- Underwriter sign-off on the HF-15 evidence package (gated on v0.3)
- Patent FTO snapshot (engagement pending)

None of these are present in v0.2-α. The repository is research/development substrate intended for academic submission, IP disclosure, and partner engagement — not flight deployment.

## Citation

If you reference this work academically, please cite the IEEE paper:

```bibtex
@inproceedings{wooden2026substrate,
  author    = {A. Khaalis Wooden, Sr.},
  title     = {Substrate Convergence Over Shell Engineering: A Falsification-First Methodology for an Interplanetary Spacesuit Decision System},
  booktitle = {(venue selection pending)},
  year      = {2026},
  publisher = {IEEE},
  note      = {VBX-ISPS-BENCH v1.1; substrate v0.2-α; LEDGER \#0005}
}
```

See [CITATION.cff](./CITATION.cff) for structured citation metadata.

## Author

**A. Khaalis Wooden, Sr.**
Director of Enterprise Capture \& Compliance, Visionblox LLC
Founder, Zuup Innovation Lab
MBA; MSIT Candidate, Southern New Hampshire University

- Visionblox: khaalis.wooden@visionblox.com
- SNHU: aldrich.wooden@snhu.edu
- GitHub: [@khaaliswooden-max](https://github.com/khaaliswooden-max)

## Acknowledgments

This work was conducted as a ZCS-6 Phase 5 (v0.1, v0.1.1) and Phase 5-redux (v0.2-α) deliverable at Visionblox LLC / Zuup Innovation Lab. The author thanks Anthropic's Claude Opus 4.7 for ZCS-6 methodology execution support, including Phase 3 attack identification, Phase 5 architecture instantiation, Phase 6 vertical-integration attack scripting, and v0.2-α LLM adapter implementation.

The substrate-shell partition framing builds on prior art in spacesuit engineering (Apollo A7L/A7LB, Shuttle EMU, xEMU/AxEMU, Z-series) and on the falsification methodology of Karl Popper as applied to recursive self-improvement contexts.

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](./LICENSE) for the full text. © 2026 Visionblox LLC.

---

*"The substrate is the IP moat; the shell is engineering. Substrate convergence is buildable on commodity hardware now. The benchmark precedes the solution."*
