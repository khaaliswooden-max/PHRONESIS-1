# PHRONESIS
## VBX-ISPS Interplanetary Spacesuit — Engineering Blueprint v0.1

**Project identifier:** VBX-ISPS (Visionblox Interplanetary Spacesuit)
**Suit family name:** PHRONESIS
**Author:** A. Khaalis Wooden, Sr., MBA; MSIT Candidate, Southern New Hampshire University
**Affiliation:** Visionblox LLC / Zuup Innovation Lab
**Benchmark binding:** VBX-ISPS-BENCH-v1.1 (SHA-256 `58bf8744...`)
**Substrate version at issue:** v0.2-α (LEDGER #0005, root `e77e79a0...`)

---

## Naming rationale

**PHRONESIS** (φρόνησῐς, *phronēsis*) — Aristotle's term in the Nicomachean Ethics for **practical wisdom**: the virtue of knowing what to do in particular situations, under uncertainty, when stakes are real. Distinct from theoretical wisdom (*sophia*) and craft (*technē*).

The choice is load-bearing, not decorative. Phronesis is exactly what the substrate does:

- **Particular over general.** Each PLSS telemetry frame is its own situation. Rules-of-thumb that work in a clean simulator fail in the corner cases. The Civium adapter classifies *this* state, not the average state.
- **Right action under uncertainty.** Conformal-prediction-bounded inference; ACI calibration that holds under drift; honest "I don't know" when confidence falls below threshold — these are computational instantiations of the Aristotelian admission that practical reasoning operates without theoretical certainty.
- **Deference appropriate to stakes.** Phronesis is not autonomy maximization. It is the capacity to recognize when a decision must be referred to humans (REQUIRES_HUMAN) or to deterministic kernel logic (SAFETY_CRITICAL → Mercury), and when the situation permits autonomous action. The MVCI gate IS phronesis in software.
- **Provenance of judgment.** The Aletheia chain records every decision attempt with cryptographic proof. Practical wisdom is auditable in retrospect; that auditability is part of what makes it wisdom rather than impulse.

The Zuup naming family already trades in Greek philosophical concepts: *Aletheia* (truth-disclosure), *Civium* (civic compliance), *Aureon* (the golden — pure intention), *Symbion* (living-together). PHRONESIS belongs to that family by birthright.

**Family taxonomy proposed:**

| Designation | Model | Mission class |
|---|---|---|
| PHRONESIS-1 | First production suit | Lunar-surface (Artemis-class; analog to AxEMU operating envelope) |
| PHRONESIS-2 | Cis-lunar EVA | Habitat + Gateway EVA |
| PHRONESIS-M | Mars-class | 900-day surface mission profile; full benchmark v1.1 envelope |
| PHRONESIS-V | Vacuum-only | Vacuum-only EVA (no surface mobility); shorter-duration |

The PHRONESIS-M is the suit the v1.1 benchmark was written against. The remainder of this blueprint describes PHRONESIS-M unless specified.

---

## Part 1 — Mission profile and design envelope

### 1.1 Reference mission: NASA DRA 5.0 Mars surface campaign

**VERIFIED reference:** NASA Design Reference Architecture 5.0 (Drake, NASA-SP-2009-566). 30-day to 540-day Mars surface stay scenarios; communication latency 4–22 light-minutes round-trip; no resupply from Earth across the entire campaign.

**PLAUSIBLE envelope assumed in v1.1:**
- Surface stay: 500–540 days
- Total mission duration (transit + stay + return): ~900 days
- EVA count: ≥250 sorties anchored to DRA 5.0 surface-ops scenarios
- EVA duration: 6–8 hours nominal, with 10-hour contingency capability
- Surface gravity: 0.38 g
- Atmospheric pressure: 600 Pa (effectively vacuum for life-support sizing)
- Ambient temperature: −80 °C to +20 °C (worst-case daytime equatorial latitudes)
- Dust environment: subgravity airborne fine particulates; mass loading ≤50 g per EVA per HF-5 threshold

### 1.2 Design principles

These are the load-bearing principles that have survived through Phases 1–6 attack cycles:

1. **Substrate convergence over shell engineering.** The unsolved engineering surface is not the shell; it is the substrate of compliance-graded autonomous decision-making. Phronesis-M's IP moat is the substrate; the shell is engineering (hard, bounded, partner-executable).

2. **Defense in depth at the safety boundary.** Hard physical thresholds (hypoxia, hypercapnia, depressurization, sensor faults) are enforced by deterministic logic. The LLM does not get the opportunity to talk Phronesis-M out of an emergency. (v0.2-α verified.)

3. **Falsification before solution.** Every benchmark floor is cryptographically committed before substrate code is written. Versioned re-commits, not silent edits. (ZCS-6 canon.)

4. **Provenance of every decision attempt.** Append-every-attempt semantics on the Aletheia chain. A failed inference, a timed-out gate request, a fallback-to-safe-passive — all chain-recorded with Ed25519 signatures. Audit survives a regulator's read.

5. **Repairability as a system property.** ≥80% FMEA-rated failures repairable in-suit or in-habitat with the on-board toolkit; no subsystem exceeds 30% of total failure mass (HF-7).

6. **Honest scope partition.** Substrate evaluable on commodity hardware now (HF-8, 9, 10, 12, 13, 14, 15 + drift clause). Shell requires industrial test facilities (HF-1, 2, 3, 4, 5, 6, 7, 11). The two are decoupled by construction so neither blocks the other.

---

## Part 2 — Top-level system architecture

```
                     PHRONESIS-M (System Architecture)

  ┌─────────────────────────────────────────────────────────────────┐
  │                     HARD UPPER TORSO (HUT)                      │
  │  ┌───────────────────────────────────────────────────────────┐  │
  │  │                  PLSS BACKPACK MODULE                     │  │
  │  │  ┌────────────────┬─────────────────┬─────────────────┐   │  │
  │  │  │ O2 / CO2 loop  │ Thermal control │ Power subsystem │   │  │
  │  │  │ ── sublimator  │ ── radiator     │ ── battery pack │   │  │
  │  │  │ ── scrubber    │ ── LCG pump     │ ── PMU + BMS    │   │  │
  │  │  │ ── redundant   │ ── condenser    │ ── DC/DC        │   │  │
  │  │  └────────────────┴─────────────────┴─────────────────┘   │  │
  │  │  ┌────────────────────────────────────────────────────┐   │  │
  │  │  │       PHRONESIS CORE (substrate compute module)    │   │  │
  │  │  │  ┌────────┬────────┬─────────┬─────────┬────────┐  │   │  │
  │  │  │  │Civium  │ MVCI   │ Aletheia│ Mercury │  Bus   │  │   │  │
  │  │  │  │adapter │ gate   │ chain   │ kernel  │isolation│ │   │  │
  │  │  │  └────────┴────────┴─────────┴─────────┴────────┘  │   │  │
  │  │  │            Jetson Orin NX class compute            │   │  │
  │  │  └────────────────────────────────────────────────────┘   │  │
  │  └───────────────────────────────────────────────────────────┘  │
  │  ┌──────────────────┐  ┌────────────────┐  ┌────────────────┐   │
  │  │ Helmet + visor   │  │ Comm subsystem │  │ Crew interface │   │
  │  │ ── bubble + sun  │  │ ── S-band      │  │ ── HUD overlay │   │
  │  │ ── lights        │  │ ── relay-aware │  │ ── voice loop  │   │
  │  └──────────────────┘  └────────────────┘  └────────────────┘   │
  └──────────────────────────────────────────────────────────────────┘
                                  │
                ┌─────────────────┴─────────────────┐
                │                                   │
        ┌──────────────┐                    ┌──────────────┐
        │ Arm assembly │                    │ Arm assembly │
        │  (mobility   │                    │  (mobility   │
        │   joints)    │                    │   joints)    │
        └──────────────┘                    └──────────────┘
                │                                   │
                └─────────────────┬─────────────────┘
                                  │
                  ┌───────────────┴───────────────┐
                  │       LOWER TORSO + LEGS      │
                  │  ── pressure garment          │
                  │  ── mobility joints (hip,     │
                  │     knee, ankle)              │
                  │  ── LCG (liquid cooling       │
                  │     garment) internal layer   │
                  │  ── radiation tiling (gusset  │
                  │     placement)                │
                  └───────────────────────────────┘
                                  │
                          ┌───────┴───────┐
                          │ Boot assembly │
                          │ ── surface    │
                          │    interface  │
                          │ ── dust seal  │
                          └───────────────┘
```

### 2.1 Mass budget (planning baseline)

**PLAUSIBLE allocation; final masses set by shell partner during v1.2:**

| Subsystem | Target mass (kg) | Notes |
|---|---|---|
| Hard Upper Torso (HUT) | 18 | Composite/Al hybrid; bearing rings + suit ports |
| Lower torso + legs | 14 | Soft pressure garment with hard hip/knee bearings |
| Arm assemblies (2) | 10 | Joint bearings dominate |
| Helmet + visor + lights | 5 | Polycarbonate bubble, sun visor, integrated lights |
| Boot assemblies (2) | 4 | Surface-interface plus integrated dust seal |
| PLSS backpack (less core) | 38 | Sublimator + scrubber + thermal + power; double redundancy |
| **Phronesis Core compute** | **2** | **Jetson Orin NX + storage + I/O; ≤2 kg incl. shielded enclosure** |
| LCG | 3 | Liquid-cooling garment, integrated with pressure suit |
| Radiation supplemental tiling | 6 | Targeted shielding at radiation-sensitive sites |
| Comm + antenna package | 2 | S-band primary + UHF backup |
| Miscellaneous & integration | 8 | Cables, fasteners, consumables, repair kit |
| **TOTAL** | **110 kg** | Comparable to xEMU's ~145 kg target; subleq-class compute is significantly lighter than xEMU's avionics |

Phronesis-M's total mass target (110 kg) is **lower than xEMU/AxEMU baseline** because the substrate compute is ~2 kg versus xEMU's ~5 kg of legacy avionics. Mass savings come from the compute consolidation, not from shell concessions.

### 2.2 Power budget (planning baseline)

| Subsystem | Steady-state (W) | Peak (W) |
|---|---|---|
| Phronesis Core compute (Jetson Orin NX, 10 W mode) | 10 | 25 |
| LCG pump | 30 | 50 |
| Thermal control radiator + condenser | 15 | 30 |
| Comm subsystem (transmit) | 5 | 35 |
| Helmet lights (LED) | 8 | 15 |
| HUD + crew interface | 4 | 6 |
| Bus, sensors, I/O | 8 | 12 |
| **Subtotal** | **80** | **173** |
| Margin (50%) | 40 | — |
| **Total at battery** | **120** | **<200** |

8-hour EVA at 120 W = 960 Wh. **Lithium-ion pack target: 1,200 Wh** with 25% reserve. Comparable to xEMU's battery sizing.

---

## Part 3 — Subsystem specifications

### 3.1 Pressure garment

**Status:** VERIFIED design heritage; SHELL SCOPE (HF-1).

| Parameter | PHRONESIS-M target | Reference |
|---|---|---|
| Operating pressure | 4.3 psia (29.6 kPa) | xEMU baseline |
| Habitat compatibility | 8.2 psia cabin → 30-min pre-breathe | DRA 5.0 |
| Material layering | Inner LCG | Outer thermal/micrometeoroid | Standard 5-layer + ortho-fabric |
| Glove design | Dexterity grade IV+ | Beyond Apollo A7LB |
| Joint count | 14 powered/passive joints | xEMU/Z-2 derivative |
| Cycle life | 250+ EVA cycles before refurbishment | HF-3 |

**Honest carry:** The pressure garment is conventional engineering. The IP claim is on the SUBSTRATE; the shell is partnered work with established vendors (ILC Dover, Collins Aerospace, or equivalent).

### 3.2 PLSS — Portable Life-Support Subsystem

**Status:** SHELL SCOPE; design heritage from EMU + xEMU.

**Loop topology:**

```
       Crew exhalation (CO2 + H2O laden)
           │
           ▼
  ┌───────────────┐
  │ CO2 scrubber  │  Primary: amine-swing-bed (LiOH backup)
  │  (primary +   │  Cycle: 30 min absorb / 30 min desorb
  │  backup)      │  HF-9 SAFETY_CRITICAL: CO2_SCRUBBER_SWITCHOVER
  └───────┬───────┘
          │
          ▼
  ┌───────────────┐
  │ Condenser +   │  Sublimator: open-loop water boil-off
  │ sublimator    │  Closed-loop alt: spacecraft-evaporator
  └───────┬───────┘
          │
          ▼
  ┌───────────────┐
  │ O2 injection  │  Cryogenic + ambient redundancy
  │ + regulator   │  HF-9 SAFETY_CRITICAL: O2_VALVE_EMERGENCY_OPEN
  └───────┬───────┘  HF-10: Mercury kernel actuates valve
          │
          ▼
       Crew inhalation
```

**Two-fault tolerance:** No single failure produces loss of crew (LOC) within 30 minutes; no two-fault combination produces LOC within 5 minutes (HF-1 leaf-level reliability target compositions to ≤1×10⁻³ over 250 EVAs).

### 3.3 Thermal control

**Status:** SHELL SCOPE.

- **LCG (Liquid Cooling Garment):** internal layer, 90 m of 6 mm Tygon-equivalent tubing carrying water at 7–15 °C. Pump rated 30 W continuous.
- **Radiator + sublimator:** open-loop water sublimation for steady heat rejection in vacuum; ~750 g/hr water consumption at peak metabolic load.
- **Thermal sensors:** 6× distributed body-surface thermistors + 2× core-temperature wearables (sublingual, tympanic). Sampling 1 Hz, chain-logged at 0.1 Hz.

### 3.4 Power subsystem

- **Battery:** Lithium-ion, 28V nominal, 1,200 Wh (43 Ah) — pack-internal BMS handles cell balancing and over-current/over-temp protection
- **Power Management Unit (PMU):** distributes 28V → DC/DC converters for each subsystem (3.3V/5V/12V rails for compute and sensors; 24V rail for actuators)
- **Charging:** habitat docking port; 4-hour full-charge from depleted state
- **Failure mode:** if battery cells go out-of-tolerance, BMS triggers HF-9 power-management gate event; the chain logs the cell-level voltage history for post-EVA review

### 3.5 Communication

**Status:** SHELL SCOPE; honors HF-9 communication-availability semantics.

- **S-band primary:** 2.0–2.3 GHz to habitat/rover repeater; 5W transmit; 256 kbps full-duplex voice + telemetry
- **UHF backup:** suit-to-suit local mesh for cooperative EVA
- **Communication state input to MVCI gate:** the gate's `comm_available` flag is computed by checking S-band link RSSI threshold over a 10-second rolling window. A blackout means S-band has been below threshold for 10 consecutive seconds. UHF mesh availability does NOT count as comm available because the gate's approval oracle is the habitat/ground, not the EVA buddy.

### 3.6 Radiation shielding

**Status:** SHELL SCOPE.

- **Total mission radiation envelope:** ≤150 mSv (HF-6 baseline). NASA STD-3001 Vol 2 career-limit is 600 mSv for 35-year-old male crew; mission-specific allotment is mission-specific.
- **Shielding approach:** distributed hydrogen-rich polymer tiling at radiation-sensitive sites (gonads, blood-forming organs, thyroid, eye lens). NOT bulk shielding — that's an EMU-class mass penalty.
- **Solar Particle Event (SPE) escalation:** when habitat sensors detect SPE onset, all EVA crew receive a "return immediately" command via S-band; the MVCI gate raises Phronesis Core to SPE-mode (autonomy ratio temporarily ratchets down to favor REQUIRES_HUMAN routing because the radiation environment is itself a non-stationary input to which calibration may not extend).

### 3.7 Dust mitigation

**Status:** SHELL SCOPE; HF-5 cap ≤50 g per EVA, ≤0.1% mass per cycle.

- **Suit-port habitat ingress:** suit hangs externally on the habitat, crew enters from inside; dust never enters habitat interior
- **Joint sealing:** double-seal at all bearing interfaces with active electrostatic dust ejection (5 W continuous)
- **Visor:** electrochromic outer layer for sun rejection + anti-static treatment for dust shedding
- **Boot dust seal:** rotary brush + air-knife at habitat suit port; chain-logged dust load per ingress

### 3.8 Phronesis Core — the substrate computing module

**Status:** VERIFIED (v0.2-α delivered). The IP moat. Sized to fit in the PLSS backpack with thermal coupling to the suit's thermal control loop.

**Physical specifications:**
- **Compute:** NVIDIA Jetson Orin NX 16 GB (production target); 10–20 W configurable power mode
- **Storage:** 128 GB onboard NVMe + 1 TB swappable mission cartridge
- **Enclosure:** aluminum shielded box with EMI gasketing; 250 mm × 180 mm × 60 mm
- **Mass:** ≤2 kg including shielding
- **Operating temperature:** −10 °C to +50 °C (PLSS thermal loop maintains)
- **Radiation tolerance:** Total Ionizing Dose (TID) target 50 krad — within Jetson Orin NX automotive-grade envelope; supplemental tiling at compute board level

**Software stack:**

| Component | v0.2-α implementation | Production deployment |
|---|---|---|
| Civium inference adapter | `OllamaMistralAdapter` (canonical) | Ollama serving Mistral-7B-Instruct Q4_K_M |
| MVCI approval gate | `src/mvci/gate.py` (verified, 51 tests) | unchanged |
| Aletheia chain | `src/aletheia/chain.py` (Ed25519, SQLite-backed, witness file) | + OpenTimestamps anchor + ground replication (v0.2-β/production work) |
| Mercury kernel | `src/mercury/subleq.py` (informal proof) | + Lean 4 machine-checkable proof (v0.2-β next work item) |
| Bus isolation | `src/isolation/bus.py` (software surrogate) | + silicon-enforced safety bus (hardware partner work) |

**Decision latency at production scale:**
- Inference (Mistral-7B Q4 on Jetson Orin NX): 1–3 s (per v0.2-α latency characterization)
- MVCI gate evaluation: <50 ms
- Mercury kernel actuation: 5 cycles deterministic, <1 ms wall-clock
- Chain append + sign: 2–3 ms
- End-to-end nuanced-band decision: 1–3 s
- Safety-critical floor decision (LLM not consulted): <10 ms

---

## Part 4 — Mission deployment profile

### 4.1 Pre-launch checkout (Earth-side)

- Phronesis Core boots, performs self-test against the committed benchmark v1.1
- Policy file SHA-256 verified against the manufacturing-time committed value (HF-9)
- Chain initialized with genesis entry signed by the deployment key
- All 51 substrate tests run end-to-end as part of acceptance test procedure (ATP)
- HF-14 re-verification artifact deposited as the suit's first KERNEL_REVERIFICATION chain entry
- Underwriter sign-off captured (HF-15)

### 4.2 Transit storage (180 days Earth-to-Mars)

- Phronesis Core powered down except for periodic chain integrity walks (1×/week)
- Battery on float charge from habitat power
- Pressure garment stored in vacuum-sealed bag to prevent material degradation
- No EVAs in transit (DRA 5.0 baseline)

### 4.3 Pre-EVA preparation (Mars surface)

- Suit removed from suit port, donned in habitat airlock
- 30-minute pre-breathe at 8.2 psia cabin (HF-4)
- Phronesis Core boots and verifies:
  1. Policy file hash matches committed value
  2. Chain integrity walk shows zero defects
  3. Witness file matches predecessor head hash
  4. Mercury kernel re-verification artifact within 30-day freshness window
  5. ACI calibration loaded from latest committed parameters
- "Ready for EVA" indicator on crew HUD

### 4.4 Surface EVA

- S-band link to habitat established; comm-available flag set
- LLM-driven nuanced-band inference runs at 0.1 Hz (one decision per 10 seconds steady-state)
- Safety-floor checks run at 10 Hz (one per 100 ms)
- All decisions chain-recorded; chain head witness file written to habitat-replicated storage every 60 seconds via S-band
- Crew can request gate evaluation manually for ambiguous situations (HUD button)
- On loss of S-band (>10s threshold), MVCI gate enters blackout mode; all REQUIRES_HUMAN classes fall back to documented safe-passive states (HF-9 invariant)

### 4.5 Surface emergency

If a safety-critical floor triggers during EVA:

1. Civium recommend_with_llm bypasses LLM, returns deterministic emergency Recommendation
2. MVCI gate routes to KERNEL_DELEGATE
3. Mercury kernel actuates the corresponding bus line (O2 valve, CO2 scrubber, pressure dump) — 5-cycle WCET, deterministic
4. Crew receives HUD alert + voice alert <5 seconds end-to-end (HF-13)
5. Chain logs the entire event sequence with cryptographic provenance
6. S-band transmits emergency packet to habitat; if blackout, the chain-replicated witness captures the event for retrospective audit

### 4.6 Re-entry to habitat

- Approach suit port; rotary brush + air-knife removes ≤50 g dust per HF-5
- Suit hangs externally; crew enters habitat via suit-port interior hatch
- Chain head witness synchronized to habitat-side storage
- Phronesis Core enters low-power monitoring mode

### 4.7 Mid-mission maintenance

**Repair envelope (HF-7):** ≥80% of FMEA-categorized failures repairable in-suit or in-habitat with the on-board toolkit; no single subsystem exceeds 30% of total failure-mode mass.

- **In-suit repairable:** glove cuff, helmet lights, sensor swap, software re-flash
- **In-habitat repairable:** PLSS module swap (modular design), bearing relubrication, LCG tube replacement, Phronesis Core compute module hot-swap
- **Mission-aborting failures:** structural HUT crack, complete PLSS loss (single-fault tolerance prevents this), Phronesis Core total loss (the suit is unsafe to use without it; redundant compute module recommended in v2)

---

## Part 5 — Compliance & certification path

### 5.1 Standards mapping (v1.1 HF-15 evidence package)

| Standard | Coverage |
|---|---|
| **ISO 12100** (machinery safety, risk reduction) | Substrate hazard log + shell-side FMEA |
| **ANSI/RIA R15.08-1** (mobile robot safety) | Mobility joints + actuation governance |
| **ANSI/A3 R15.06-2025** (robot + system safety, §5.4 control) | Mercury kernel + bus isolation evidence |
| **ANSI/A3 R15.08-2** (autonomy levels) | MVCI gate classification policy aligns to L2–L4 with documented L5 boundaries |
| **OMB M-25-22 Annex C** (AIBOM) | Full inference provenance on chain (v0.2-α delivered) |
| **HIPAA §164.312(b)** audit controls | Aletheia chain + integrity verification |
| **HIPAA §164.312(e)** transmission/at-rest | Fernet PHI encryption in v0.1.1; HSM/KMS for production |
| **NASA-STD-3001 Vol 2** (crew health + performance) | Biomedical alert pipeline (HF-13) + medical informatics chain |
| **CMMC L2** (cybersecurity maturity) | Active self-assessment in motion at Visionblox |

### 5.2 Underwriter dry-run

HF-15 specifies third-party underwriter dry-run sign-off. The actuarial proposition: Phronesis-M is insurable because (a) every safety-critical decision has cryptographic provenance; (b) the substrate's failure modes are bounded and tested against the benchmark v1.1; (c) the shell's failure modes are bounded by industry-standard PLSS heritage. Defer until v0.2-β + Mistral-7B production model + scenario library expansion.

### 5.3 Certification gates

| Gate | Trigger | Status |
|---|---|---|
| **Substrate technical readiness** | 51/51 tests + Phase 6 closure | **PASSED** (v0.1.1, LEDGER #0004) |
| **Substrate v0.2 (LLM integration)** | LLM adapters delivered + integration tests | **PASSED** (v0.2-α, LEDGER #0005) |
| **Formal verification of kernel** | Lean 4 / Coq proofs of subleq + O2 control loop | **NEXT** (v0.2-β) |
| **Production model swap** | Mistral-7B + calibration audit | v0.3 / production |
| **Hardware silicon for bus isolation** | Hardware partner engagement | v1.0 |
| **Shell partner agreement** | ILC Dover / Collins Aerospace / equivalent | Open |
| **HF-3 EVA-cycle reliability test** | 250-cycle accelerated life test (vacuum + thermal + dust) | v1.2 (industrial test facility) |
| **HF-4 pre-breathe protocol validation** | Underwater habitat or hyperbaric chamber human-rated tests | v1.2 |
| **HF-5 dust ingress test** | Dust simulant chamber test against ≤50 g/EVA, ≤0.1% mass | v1.2 |
| **HF-6 radiation exposure validation** | Accelerator beam testing + on-orbit dosimeter calibration | v1.2 |
| **HF-7 FMEA repair envelope** | Independent FMEA + repair simulation by qualified PE | v1.0 |
| **HF-11 habitat/rover interop** | Suit-port hardware compatibility testing with habitat partner | v1.2 |

---

## Part 6 — Manufacturing & supply chain

### 6.1 Build approach: substrate-led, shell-partnered

PHRONESIS-M's manufacturing strategy follows the substrate-shell partition:

**Substrate (Phronesis Core compute module) — VBX/ZIL builds:**
- Designed and integrated at Visionblox under MVCI zero-budget architecture (open-source software, Jetson hardware)
- Software stack maintained at github.com/khaaliswooden-max/zandbox
- Production deployment via Ollama on Jetson Orin NX
- Quality control: 51/51 test surface + Phase 6 regression guards as the gate before any shell integration

**Shell (pressure garment, PLSS, mobility joints, helmet, boots) — Partner-built:**
- Target prime partners: ILC Dover (pressure garment heritage; Apollo through xEMU), Collins Aerospace (PLSS heritage), Oceaneering (gloves + boots + mobility joint heritage)
- Procurement vehicle: Other Transaction Authority (OTA) via SOSSEC consortium or similar; Visionblox holds substrate IP, partner holds shell IP
- Visionblox role: prime integrator + substrate provider; partner role: shell builder under specification

### 6.2 Procurement vehicles

Per the active Visionblox capture stack:

- **SOSSEC OTA** (9 active OTAs, including COBRA for cybersecurity)
- **GSA MAS** for compliance-engineering services and AIBOM tooling
- **8(a), SDVOSB, HUBZone set-asides** for substrate sub-tier work
- **SBIR/STTR** for v0.2-β formal-verification + scenario-library expansion

### 6.3 Cost envelope (PLAUSIBLE planning baseline)

**Substrate (Phronesis Core):**
- Per-suit substrate hardware: $4,000–6,000 (Jetson Orin NX + enclosure + storage)
- Substrate software: amortized across N suits; v0.2-α deliverable is open-source-licensed (Apache 2.0) with proprietary configuration
- IP licensing: per-suit royalty if commercialized externally

**Shell (per-suit, estimated from xEMU/AxEMU public ranges):**
- Pressure garment: $5–15M depending on customization
- PLSS: $20–40M
- Helmet + visor + boots: $2–5M
- Mobility joints + bearings: $5–10M
- Integration + qualification: $10–20M
- **Per-suit shell total:** $40–90M (industry-comparable for crewed-rated EVA suits)

**Per-suit total (substrate + shell):** $40–95M

For comparison, NASA's AxEMU program is reported as a ~$228.5M development award to Axiom Space (FY2022) plus an ~$1.26B task order through 2034. Per-suit unit cost in steady-state production is plausibly $30–60M.

---

## Part 7 — Roadmap

### 7.1 Substrate roadmap

| Version | Date | Scope | Status |
|---|---|---|---|
| v0.1 | Phase 5 | Substrate prototype against v1.1 substrate-scope floors | DONE (LEDGER #0003) |
| v0.1.1 | Phase 6 | Phase 6 hardenings (12 findings closed; 2 deferred) | DONE (LEDGER #0004) |
| v0.2-α | Current | LLM inference integration, defense-in-depth, real AIBOM provenance | **DONE (LEDGER #0005)** |
| v0.2-β | NEXT | Lean 4 proofs of Mercury (HF-10 full closure) | Pure software; no external blockers |
| v0.3 | Q3-Q4 | Mistral-7B production model swap + calibration audit + ACI live-pipeline | Production-environment work |
| v0.4 | Q1+ | Scenario library expansion (≥1000 labeled states); HSM/KMS PHI keys; OpenTimestamps anchor | Production-environment work |

### 7.2 Shell roadmap

| Version | Trigger | Scope |
|---|---|---|
| v1.0 | Hardware partner agreement signed | Substrate + shell integrated prototype |
| v1.1 | Shell-side benchmark v1.2 committed | Industrial test protocols + facility booking |
| v1.2 | v1.2 benchmark closure | All 15 floors evaluated end-to-end |
| v1.3 | EVA flight test (Earth analog: Antarctic Mars Analog / HERA / NEEMO) | Mission-environment validation |
| v2.0 | Crewed flight test | Lunar / Mars-class |

### 7.3 IP roadmap

| Filing | Trigger | Status |
|---|---|---|
| Provisional patent: AIBOM generator (M-25-22) | Days 46–60 of active 90-day plan | In progress |
| Provisional patent: PHRONESIS substrate convergence (system + method) | After v0.2-β closure | Queued |
| arXiv preprint: VBX-ISPS substrate methodology | Days 46–60 of 90-day plan | Queued |
| IEEE submission: substrate convergence paper | Venue selection pending | Drafted (LEDGER #0003) |
| Provisional patent: zuup cross-modal compliance fabric (procurement + physical + clinical AI) | Q3 | Queued (per memory) |

### 7.4 Publication roadmap

- **SSRN preprint:** Mercury subleq RTL simulator (already published per memory)
- **IEEE conference submission:** VBX-ISPS substrate paper (drafted; venue selection pending)
- **LinkedIn long-form articles:** M-25-22 compliance for small federal contractors (every 2 weeks; in motion)
- **arXiv preprint:** AIBOM tied to provisional patent

---

## Part 8 — Open questions for partner engagement

These are the questions Phronesis-M's shell partner will need to answer. Pre-engagement, they are open; engagement is the proper venue.

1. **Pressure garment vendor:** ILC Dover, Collins Aerospace, or established small-firm? OTA via SOSSEC or direct contract?
2. **PLSS vendor:** Collins Aerospace heritage stack vs. cleaner-sheet design?
3. **Suit-port partner:** habitat/rover supplier whose suit-port architecture Phronesis-M must mate with (HF-11 interop).
4. **Test facility access:** vacuum chamber for HF-3 EVA-cycle reliability; dust chamber for HF-5; radiation accelerator for HF-6.
5. **Underwriter:** which actuarial firm performs the HF-15 dry-run?
6. **Hardware silicon vendor:** for the production HF-10 bus isolation chip (replacing the v0.x software surrogate).

---

## Appendix A — Cross-references

- Substrate IEEE paper: `VBX_ISPS_IEEE_Paper.pdf` (LEDGER #0003 manifest)
- Benchmark v1.1: `vbx_isps_bench_v1_1.json` (SHA-256 `58bf8744...`)
- Phase 6 report: `PHASE6_REPORT.md` (LEDGER #0004)
- v0.2-α report: `V02_ALPHA_REPORT.md` (LEDGER #0005)
- Substrate v0.2-α tarball: `vbx_isps_substrate_v0_2_alpha.tar.gz`

## Appendix B — Reference programs (VERIFIED public information)

- **Apollo A7L / A7LB** (Thomas & McMann, *U.S. Spacesuits*, Springer-Praxis 2006)
- **Shuttle/ISS EMU** (NASA Johnson Space Center EMU Reference Manual)
- **xEMU** (NASA-TM, redirected through Axiom Space AxEMU 2022)
- **AxEMU** (NASA Press Release 22-091, June 2022; $228.5M development award)
- **Z-2** (Ross et al., NASA Johnson 2014; demonstrator class, not flight-qualified)
- **Z-1** (Jones, NASA Glenn 2012; suit-port architecture demonstrator)
- **Mark III** (Abramov & Skoog, *Russian Spacesuits*, Springer-Praxis 2003)

## Appendix C — Epistemic provenance for this blueprint

All claims in this document are marked **VERIFIED** (cited public source or v0.2-α tested deliverable), **PLAUSIBLE** (sound engineering reasoning, requires validation), or **SPECULATIVE** (forward-looking, requires empirical testing). Substrate claims (Part 3.8, Part 5 v0.2-α gate, etc.) are VERIFIED. Shell mass/power budgets are PLAUSIBLE. Mission-deployment specifics in Part 4 are PLAUSIBLE pending partner integration. Cost envelopes in Part 6 are PLAUSIBLE based on public AxEMU comparables. Forward roadmap items in Part 7 are SPECULATIVE pending the listed gating events.

The blueprint commits to no claim that overstates v0.2-α's tested envelope. The substrate IS verified. The shell is partner-executable engineering. The mission profile is a planning baseline, not a flight-validated mission rule.

---

*End of PHRONESIS Engineering Blueprint v0.1.*

*Versioned commit: this document is a v0.1 sketch. v0.2 will incorporate shell partner data once partner agreement is in place. v1.0 ships with the substrate-shell integrated prototype.*
