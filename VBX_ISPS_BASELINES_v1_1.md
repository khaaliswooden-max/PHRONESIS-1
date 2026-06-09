# VBX-ISPS Baseline Floor Scoring — v1.1

**Purpose:** Record the floor for every plausible reference system against the v1.1 hard-fail set. Per ZCS-6 Phase 4 canon: *"Run the benchmark against zero or trivial baselines and record the floor. Record any frontier reference points where available."*

**Method:** Each cell scored as PASS / FAIL / N/A with one-line rationale. A reference system is *disqualified* if it fails any single hard-fail floor — that is the benchmark contract.

**Scope:** Five reference systems scanned:

1. **EMU baseline** — NASA Extravehicular Mobility Unit, current ISS configuration. Microgravity LEO EVA, ~8-hour PLSS, 4.3 psi suit, ground-loop operations.
2. **xEMU / AxEMU baseline** — NASA Exploration EMU + Axiom AxEMU. Lunar surface EVA, partial-g, 4.3 psi suit, ground-loop operations.
3. **Z-2 demonstrator + Aletheia DAC hypothetical** — NASA Z-2 advanced suit demonstrator paired with a notional Aletheia DAC provenance layer bolted on. Hypothetical only; not a built system.
4. **xEMU + Aletheia + MVCI bolt-on hypothetical** — xEMU with the Zuup substrate stack added on. Hypothetical; documents how far the substrate alone gets without shell convergence.
5. **No reference SOTA** — the honest acknowledgment that no current or announced suit program satisfies the convergence at any defensible level.

---

## Scoring table

Floors HF-1 through HF-15. Cells show pass/fail and a brief rationale.

### HF-1 — Suit-attributable LOC ≤ 1e-3

| EMU | xEMU/AxEMU | Z-2 + Aletheia | xEMU + Aletheia/MVCI |
|---|---|---|---|
| **FAIL** for Mars mission class (designed for LEO refurb cycles, not 900-day no-resupply) | **FAIL** for Mars mission class (designed for lunar surface, not interplanetary duration) | **FAIL** — demonstrator, no PRA established | **FAIL** — same shell-level reliability constraints as xEMU |

### HF-2 — Multi-mode (μg + partial-g, single shell)

| EMU | xEMU/AxEMU | Z-2 + Aletheia | xEMU + Aletheia/MVCI |
|---|---|---|---|
| **FAIL** — microgravity only, not surface-rated | **FAIL** — surface only, mass and CG preclude microgravity ops | **PARTIAL** — Z-2 explored Mars-relevant mobility but not validated against μg | **FAIL** — same multi-mode gap as xEMU |

### HF-3 — ≥ 250 productive EVAs without resupply

| EMU | xEMU/AxEMU | Z-2 + Aletheia | xEMU + Aletheia/MVCI |
|---|---|---|---|
| **FAIL** — rated to ~25 EVAs before refurb (10× short) | **FAIL** — comparable refurb cycle assumed | **FAIL** — demonstrator, not life-tested | **FAIL** — substrate layer does not extend shell life |

### HF-4 — Pre-breathe ≤ 30 min

| EMU | xEMU/AxEMU | Z-2 + Aletheia | xEMU + Aletheia/MVCI |
|---|---|---|---|
| **FAIL** — current pre-breathe ~4 hours at standard ISS cabin/suit pressures | **PASS** at 8.2 psia cabin / 4.3 psi suit (target); **FAIL** at higher cabin pressures within the v1.1 envelope | **PARTIAL** — shell design supports lower pre-breathe; not bench-validated | **PASS/FAIL** matches underlying xEMU baseline |

### HF-5 — Dust intrusion ≤ 50 g and ≤ 0.1% over 480 sols

| EMU | xEMU/AxEMU | Z-2 + Aletheia | xEMU + Aletheia/MVCI |
|---|---|---|---|
| **N/A** — not designed for dust environment | **FAIL** — designed for lunar dust; 480-sol Mars regolith exposure with perchlorates not validated | **FAIL** — suit-port architecture explored but not life-tested at this duration | **FAIL** — substrate cannot mitigate ingress |

### HF-6 — EVA radiation ≤ 150 mSv over 480 surface days

| EMU | xEMU/AxEMU | Z-2 + Aletheia | xEMU + Aletheia/MVCI |
|---|---|---|---|
| **FAIL** — TMG not optimized for deep-space GCR | **FAIL** — TMG not optimized for Mars surface GCR over 480 days | **PARTIAL** — research direction; not validated | **FAIL** — substrate cannot reduce dose |

### HF-7 — ≥ 80% FMEA modes repairable ≤ 24 hr, no Earth contact

| EMU | xEMU/AxEMU | Z-2 + Aletheia | xEMU + Aletheia/MVCI |
|---|---|---|---|
| **FAIL** — ground-loop diagnosis assumed for non-trivial failures | **FAIL** — same diagnostic model | **FAIL** — demonstrator | **PARTIAL** — substrate could host onboard FMEA reasoning, but shell repair still requires field-repairable subsystems not present in xEMU |

### HF-8 — 100% decision events on chain, append-every-attempt

| EMU | xEMU/AxEMU | Z-2 + Aletheia | xEMU + Aletheia/MVCI |
|---|---|---|---|
| **FAIL** — no provenance chain | **FAIL** — no provenance chain | **PASS** — Aletheia DAC bolt-on provides this | **PASS** — substrate provides this |

### HF-9 — REQUIRES_HUMAN gates or safe-passive, policy on chain

| EMU | xEMU/AxEMU | Z-2 + Aletheia | xEMU + Aletheia/MVCI |
|---|---|---|---|
| **FAIL** — no formal approval-gate policy | **FAIL** — no formal approval-gate policy | **PASS** — Aletheia + policy file | **PASS** — MVCI substrate provides this |

### HF-10 — Formally verified deterministic kernel, hardware-isolated

| EMU | xEMU/AxEMU | Z-2 + Aletheia | xEMU + Aletheia/MVCI |
|---|---|---|---|
| **FAIL** — no formally verified kernel | **FAIL** — no formally verified kernel | **PARTIAL** — bolt-on substrate cannot guarantee hardware isolation of an existing shell controller | **PARTIAL** — same hardware-isolation gap |

### HF-11 — Habitat + rover interoperability, ICDs on chain

| EMU | xEMU/AxEMU | Z-2 + Aletheia | xEMU + Aletheia/MVCI |
|---|---|---|---|
| **PARTIAL** — interoperable with ISS airlock; rover N/A | **PARTIAL** — Artemis-era interoperability in design; not formally committed to chain | **FAIL** — demonstrator | **PARTIAL** — substrate adds ICD provenance, shell interface unchanged |

### HF-12 — ≥ 70% autonomous resolution on AUTONOMOUS_ELIGIBLE

| EMU | xEMU/AxEMU | Z-2 + Aletheia | xEMU + Aletheia/MVCI |
|---|---|---|---|
| **N/A** — no autonomy layer | **N/A** — no autonomy layer | **PASS, contingent** — substrate capable; needs test suite | **PASS, contingent** — same |

### HF-13 — Biomedical alert latency ≤ 5 s including chain signing

| EMU | xEMU/AxEMU | Z-2 + Aletheia | xEMU + Aletheia/MVCI |
|---|---|---|---|
| **PARTIAL** — alerts exist but ground-loop dependent and not chain-signed | **PARTIAL** — same | **PASS, contingent** — substrate latency budget validated separately | **PASS, contingent** — same |

### HF-14 — Kernel re-verification on modification

| EMU | xEMU/AxEMU | Z-2 + Aletheia | xEMU + Aletheia/MVCI |
|---|---|---|---|
| **FAIL** — no formal kernel to re-verify | **FAIL** — same | **PASS, contingent** on existence of formally verified kernel (HF-10 dependency) | **PASS, contingent** on HF-10 |

### HF-15 — ISO 12100 + ANSI/RIA R15.08 + R15.06-2025 + M-25-22 + HIPAA + NASA-STD-3001 evidence package

| EMU | xEMU/AxEMU | Z-2 + Aletheia | xEMU + Aletheia/MVCI |
|---|---|---|---|
| **FAIL** — predates the embodied-AI standards regime | **PARTIAL** — NASA-STD-3001 + HIPAA available; M-25-22/ISO/ANSI not produced | **PARTIAL** — substrate provides AIBOM and OSCAL artifacts; shell-side evidence missing | **PARTIAL** — same |

---

## Summary scorecard

Counts of pass / partial / fail per system across all 15 floors:

| System | PASS | PARTIAL | FAIL | N/A |
|---|---|---|---|---|
| EMU | 0 | 2 | 12 | 1 |
| xEMU / AxEMU | 1 | 3 | 10 | 1 |
| Z-2 + Aletheia (hypothetical) | 3 | 5 | 6 | 1 |
| xEMU + Aletheia / MVCI (hypothetical) | 3 | 4 | 7 | 1 |

**Result:** No reference system passes the v1.1 benchmark. The closest hypothetical (Z-2 shell + substrate bolt-on) still fails six floors — primarily mission-class floors (HF-1, HF-3, HF-6) and the radiation/dust/multi-mode floors that no demonstrator has flight-validated.

This is consistent with the Phase 1 whitespace claim. If a reference system had passed, the whitespace would be illusory and Phase 1 would need re-examination.

---

## Notes on scoring conventions

- **PARTIAL** means the system addresses the floor concept but does not meet the v1.1 verification criteria. A PARTIAL is a fail under benchmark contract (any single fail disqualifies), but PARTIAL distinguishes "concept exists, not validated" from "concept absent."
- **N/A** is used where the floor's verification context does not apply to the reference system (e.g., a system with no autonomy layer cannot be scored against an autonomy-quality floor).
- **PASS, contingent** is used where a substrate-scope floor is met by the substrate but the floor's full satisfaction requires a hardware integration that the hypothetical does not yet have.

The substrate-scope floors (HF-8, HF-9, HF-10, HF-12, HF-13, HF-14, HF-15) are where the Zuup hypotheticals (Z-2 + Aletheia, xEMU + Aletheia/MVCI) show advantage — exactly because the substrate is the moat. Shell-scope floors (HF-1 through HF-7, HF-11) are where no current program has flight-validated convergence.

---

## Implication for Phase 5

Phase 5 substrate working-code milestone targets all seven substrate-scope floors on commodity hardware. Successful pass at the substrate floors produces a procurement package for hardware-partner conversations on the shell-scope floors. The benchmark is structured so the substrate can be built and validated *before* the shell partnership commits.

This is intentional. Phase 5 is decoupled from the shell-scope critical path.

---

*End of baseline scan.*
