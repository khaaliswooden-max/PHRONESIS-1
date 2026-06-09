# VBX-ISPS Delta Record: v1.0 → v1.1

**Predecessor:** VBX-ISPS-BENCH-v1.0 (SHA-256 `ac6114a4c0a025f86926fe2d3f95d36a5a8b4796b2893ce58e22df488f7fd861`, chain #0001, committed 2026-06-08T14:03:04Z)
**Successor:** VBX-ISPS-BENCH-v1.1 (SHA-256 computed below, chain #0002)
**Author:** A. Khaalis Wooden, Sr., MBA; MSIT Candidate, Southern New Hampshire University
**Phase:** ZCS-6 Phase 3 closure / Phase 4 re-commit

---

## Why a v1.1 commit and not a silent edit

Per ZCS-6 canon, backward edges into Phase 2 require a versioned benchmark update — never a silent edit. v1.0 contained known trivial-pass holes that Phase 3 attacks surfaced. v1.1 hardens those holes and adds floors that v1.0 missed. v1.0 remains in the chain as the originating artifact; v1.1 is the operational contract. This delta record is the auditable bridge between them.

---

## Changes by floor (v1.0 → v1.1)

### Hardenings of existing floors

| Floor | What changed | Why |
|---|---|---|
| HF-1 | Verification methodology revised from "Monte Carlo PRA, 1e6 trials" to "decomposed PRA with leaf-level flow-down" per NASA NPR 8705.5 | v1.0 assumed a complete reliability model exists. It does not. Decomposed PRA is buildable now and decomposes the problem to procurable subsystem-level reliability requirements. |
| HF-2 | Verification expanded from "parabolic flight + lunar analog facility" to three-stage protocol (parabolic μg + lunar analog partial-g + ISS suit-port comparison) plus accelerated-life testing for multi-month exposure | v1.0 implicitly claimed pre-flight validation could fully match 210-day microgravity + 480-day partial-g exposure. It cannot. Honest extrapolation methodology with uncertainty bounds replaces the implicit claim. |
| HF-3 | Added: (a) mission-manifest anchoring (250 EVAs = NASA DRA 5.0 manifest + 25% margin, not arbitrary round number); (b) task-closure sub-floor (per-EVA acceptance against manifest); (c) post-EVA suit health-check requirement | v1.0 number was unanchored. Trivial-pass via short stationary "EVAs" was open. |
| HF-5 | Added absolute mass floor (50 g total intrusion) alongside 0.1% ratio. Added SEM particle-size analysis | Ratio-only floor was gameable by arbitrarily heavy shell. Particle-size data validates dust mitigation mechanism, not just bulk mass. |
| HF-6 | Added conditional SPE-survival escalation: if operational SPE-shelter assumption fails, suit must provide ≥ 10 g/cm² hydrogen-equivalent shielding for 4-hour unsheltered SPE survival | v1.0 SPE exclusion was potentially load-bearing on an operationally fragile assumption. Conditional escalation closes the hole. |
| HF-7 | Added 30% cap on subsystem-level whole-replacement repairs | v1.0 was gameable by defining all repairs as coarse swap-the-module patterns. 30% cap forces fine-grained repair capability. |
| HF-8 | Reframed from "signed safety-critical decisions" to "append every decision attempt — autonomous resolution, gate request, gate approval, gate rejection, timeout, fallback-to-safe-passive". Audit metric is fraction-unlogged at replay, not fraction-signed | v1.0 was gameable by signing only successful decisions and letting failures go unlogged. |
| HF-9 | Added: policy file itself is a v1.1 cryptographically committed dependency artifact. Reclassification of actions out of REQUIRES_HUMAN triggers a versioned policy update + explicit human authorization on chain | v1.0 was gameable by reclassifying actions out of REQUIRES_HUMAN to evade the gate. Policy binding closes the cheat. |
| HF-10 | Added explicit hardware-isolation requirement (bus-level enforcement, not policy-level); ML subsystem cannot access safety-bus by design. Watchdog separate from kernel. Penetration testing added to verification | v1.0 was gameable by stubbing a formally verified kernel and proxying around it at bus level. Hardware isolation closes the cheat. |

### New floors added (from Phase 3 attacks)

| Floor | Source of finding | What it asserts |
|---|---|---|
| HF-11 | Phase 3 coverage attack — "suit does not exist in isolation" | Interoperability with ≥ 1 habitat suit-port + ≥ 1 rover suit-port spec; both ICDs cryptographically committed |
| HF-12 | Phase 3 Goodhart attack — pathological optimum is "abdicate everything to safe-passive" | Of AUTONOMOUS_ELIGIBLE decisions per policy, ≥ 70% resolved autonomously with mission task continuity. Anchored to ACI band design intent, not arbitrary. |
| HF-13 | Phase 3 cross-investigator attack (flight surgeon) | Biomedical alert latency ≤ 5 s end-to-end INCLUDING chain signing |
| HF-14 | Phase 3 cross-investigator attack (certification engineer) | Any post-deployment kernel modification requires signed re-verification artifact committed to chain BEFORE deployment |
| HF-15 | Phase 3 cross-investigator attack (actuarial underwriter) | Evidence package mapping all floors to ISO 12100 + ANSI/RIA R15.08-1 + ANSI/A3 R15.06-2025 + R15.08-2 + OMB M-25-22 + HIPAA + NASA-STD-3001. Underwriter dry-run sign-off required. |

### Drift clause sharpened

v1.0 said "static conformal coverage tested at 1×, 2×, 3× distribution shift on crew metabolic, thermal, and CO2-load distributions." v1.1 names **five** distributions explicitly:

1. Crew metabolic rate
2. Thermal load on PLSS
3. CO2 partial pressure profile
4. Dust load rate on filters and bearings
5. Bearing wear rate

ACI must hold across all five at 3× shift.

### Scope partition added

v1.0 implicitly treated all floors as one category. v1.1 explicitly partitions:

- **Substrate scope** (HF-8, HF-9, HF-10, HF-12, HF-13, HF-14, HF-15): evaluable on commodity hardware (Jetson + Linux + open-source). Verification protocols third-party-executable now. Governs Phase 5 working-code milestone.
- **Shell scope** (HF-1, HF-2, HF-3, HF-4, HF-5, HF-6, HF-7, HF-11): requires industrial test facilities. Specified to procurement-package level. Facility-specific protocols deferred to v1.2.

This partition lets Phase 5 begin on the substrate without blocking on hardware partnership.

### Dependency artifacts to be committed with v1.1

Five artifacts must commit alongside v1.1 to make the benchmark fully self-contained:

1. Mission EVA manifest (NASA DRA 5.0 or equivalent) — anchors HF-3
2. REQUIRES_HUMAN / AUTONOMOUS_ELIGIBLE policy file — anchors HF-9 and HF-12
3. Habitat suit-port interface specification — anchors HF-11
4. Rover suit-port interface specification — anchors HF-11
5. v1.1 simulation test suite (≥ 10,000 stratified decision scenarios) — anchors HF-12 and the non-stationarity clause

These are not yet authored. They block Phase 5 only to the extent that the substrate working-code milestone requires items 2 and 5. Items 1, 3, 4 block hardware-partner conversations, not substrate work.

### Trivial-pass strategies v1.1 (what v1.1 might still be gameable against)

Even hardened v1.1 has surfaces. Five new gaming patterns flagged for Phase 6 vigilance:

1. Sandbagging the AUTONOMOUS_ELIGIBLE classification set to evade HF-12. Counter-mechanism: classification distribution is itself audited.
2. Aggressive leaf-level reliability assignments in HF-1 PRA. Counter-mechanism: supplier evidence required at procurement.
3. Extrapolation overreach in HF-2 rationale. Counter-mechanism: uncertainty bounds required and reviewed.
4. Throttling chain signing in HF-13 to hit per-event latency while violating throughput. Counter-mechanism: throughput audited under HF-8.
5. Voluminous-but-weak HF-15 evidence package. Counter-mechanism: reviewer sign-off requires clause-to-floor mapping specificity.

These are not floors v1.1 fails; they are surfaces Phase 6 must watch.

---

## Open items for v1.2

Honest statement of what v1.1 does not yet resolve:

1. **Facility-specific verification protocols for shell-scope floors.** Deferred to hardware-partner facility selection.
2. **HF-3 may force revision in 12-24 months.** If accelerated-life data on PLSS + bearings + seals + dust mitigation shows 250 EVAs is unreachable, the manifest assumption or the cadence target must revise. This is a SPECULATIVE floor by acknowledgment.
3. **HF-6 SPE escalation may need to become primary.** If operational reality precludes external SPE shelter on early Mars missions, the conditional 10 g/cm² shielding clause becomes the primary requirement, with significant mass impact.
4. **v1.1 simulation test suite scenario library production.** ~10,000 stratified scenarios is a body of work; deferred to Phase 5 substrate prototype timeline.

---

## Phase 2 exit criteria check (per ZCS-6 canon)

> *Exit criteria: the benchmark is concrete enough that a third party could implement and run it without further clarification.*

**Substrate scope (HF-8, HF-9, HF-10, HF-12, HF-13, HF-14, HF-15):** YES. Verification protocols specify subject counts, test apparatus, pass criteria, artifacts. Third-party-runnable on commodity hardware.

**Shell scope (HF-1, HF-2, HF-3, HF-4, HF-5, HF-6, HF-7, HF-11):** PROCUREMENT-READY. Specified to the level a hardware partner can bid against. Facility-specific protocols (which exact chamber, which exact lab) deferred to v1.2 with partner selection. This is acknowledged as a known limitation of v1.1.

**Phase 2 closure verdict:** YES for substrate scope (which is what Phase 5 needs); CONDITIONAL for shell scope (procurement-package-ready; facility-specific completion in v1.2 with partner).

---

## Commit chain

```
chain_position : VBX-ISPS-LEDGER#0002
predecessor    : VBX-ISPS-LEDGER#0001 (v1.0)
artifact       : vbx_isps_bench_v1_1.json
sha256         : <computed at chain submission>
delta_record   : this document (VBX_ISPS_DELTA_v1_0_to_v1_1.md)
delta_sha256   : <computed at chain submission>
timestamp_utc  : <computed at chain submission>
signing_key    : <Ed25519 public key fingerprint — placeholder until production key custody>
ots_anchor     : <OpenTimestamps proof — to be appended on chain anchor>
```

Both the v1.1 spec and this delta record are jointly committed. Any future reference to "VBX-ISPS-BENCH" without version qualifier means v1.1 from this point forward. v1.0 remains historically retrievable but is no longer the operational contract.

---

*End of delta record.*
