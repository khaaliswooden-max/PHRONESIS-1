# Governance

## Overview

VBX-ISPS · PHRONESIS-M is governed by a **falsification-first** model in which the **benchmark is the legislature**, the **substrate code is the executive**, and the **chain ledger is the judiciary**. Each has clearly bounded authority. The arrangement is designed to make it structurally hard to lie to yourself about progress — which is the canonical failure mode for recursive self-improvement claims and the lesson that motivated ZCS-6.

This document explains who makes decisions, how decisions are recorded, what the boundaries are between different kinds of changes, and how the project resolves disagreement.

---

## Project ownership

| Role | Holder |
|---|---|
| Project owner / IP holder | Visionblox LLC |
| Principal investigator / lead maintainer | A. Khaalis Wooden, Sr. (MBA; MSIT Candidate, SNHU) |
| Affiliation | Visionblox LLC; Zuup Innovation Lab |
| Legal entity for licensing | Visionblox LLC |

Visionblox LLC owns the project IP, holds the licensor seat for the Apache 2.0 grant, and is the entity of record for any future provisional patent filings on substrate components. The principal investigator is the technical decision-maker and the maintainer of the benchmark and ledger.

---

## ZCS-6 phase discipline as governance

The ZCS-6 methodology partitions any major engineering effort into six phases, each with a different governance posture:

| Phase | Activity | Decision authority |
|---|---|---|
| 1 — Whitespace | Identify the unsolved engineering surface | Principal investigator; documented in `reports/` |
| 2 — Benchmark construction | Build the falsification artifact (no solution exists yet) | Principal investigator + cryptographic commitment to ledger |
| 3 — Attack | Stress-test the benchmark before solving it | Open to contribution; merged with reviewer discipline |
| 4 — Defend | Harden the benchmark against attack | Principal investigator + ledger commitment for new version |
| 5 — Build | Implement the solution against the frozen benchmark | Open to contribution under CONTRIBUTING.md gates |
| 6 — Vertical-integration attack | Attack the integrated solution | Open to contribution; findings logged to ledger |

**The benchmark is frozen during Phases 3, 4, 5, and 6 of a given major version.** Inside a major version (e.g., v1.x of the benchmark), the benchmark file is cryptographically committed at the start of Phase 3 and is immutable until a deliberate Phase 1/2 reset begins a new major version.

This is the most important governance rule. It is the structural defense against Goodhart's Law and "bench maxing." Editing a benchmark to make a candidate pass — without re-entering Phase 1 with a documented deficiency in the prior version — is project-fraud. See CODE_OF_CONDUCT.md.

---

## What the benchmark is

The benchmark `benchmark/vbx_isps_bench_v1_1.json` is a JSON document containing:

- 15 hard-fail floors (HF-1 through HF-15) with quantitative thresholds
- Scope partition (substrate vs shell) for each floor
- Reference-system scoring metadata (xEMU / AxEMU / xMHU baselines where public)
- Cryptographic hash binding to the originating problem statement

Its SHA-256 is `58bf8744d3cc78b1cb7bb88464edb7df796187c45cea1ae483e936249803c1c5` and is verified in CI on every commit.

Changes to the benchmark require:

1. A documented deficiency in the current version (concrete failure mode the benchmark does not capture, or threshold empirically wrong)
2. A draft delta document (`benchmark/VBX_ISPS_DELTA_v1_X_to_v1_Y.md`) explaining the change with epistemic markers
3. A new ledger commit (e.g., LEDGER #0006) cryptographically linking to the prior benchmark commit
4. Principal investigator sign-off

Minor versions (v1.1 → v1.2) reflect refinements within the same problem framing. Major versions (v1.x → v2.x) reflect a re-entry into Phase 1 with a substantively different problem.

---

## What the ledger is

The ledger (`ledger/VBX_ISPS_LEDGER_NNNN.json`) is a chain of commit manifests. Each manifest:

- Identifies the artifact being committed (benchmark, substrate, paper, blueprint)
- Lists the constituent files with their SHA-256 hashes
- Includes the merkle root over the manifest contents
- Links to the prior ledger entry's root (hash chain)
- Is timestamped in UTC
- Is signed by the principal investigator

The ledger is the project's commit history of the canonical artifacts. It is separate from `git log` because it operates at a coarser granularity (per-version, not per-commit) and because it is cryptographically structured for external verifiability (in v0.2-β it will anchor to OpenTimestamps and replicate to a ground witness).

The current head is LEDGER #0005 with root `e77e79a02d836345cc35d9105862f0fb8c42b1c64fdd2af32c4646b53389e655` (v0.2-α substrate commit, 2026-06-09).

---

## What the substrate code is

The substrate code (`substrate/`) is the executive implementation. Its authority is bounded by the benchmark; it must pass the benchmark's tests, and it must do so without weakening the deterministic safety floors.

Decisions about the substrate's internal architecture (which components, which interfaces, which language, which dependencies) are made by the principal investigator, subject to:

- The benchmark's hard-fail floors (cannot be weakened)
- The defense-in-depth invariant (cannot be removed)
- The chain semantics (append-only, signed, hash-linked, witness-protected)
- The IP-aware contribution policy (Apache 2.0; no incompatible-license code)

Contributions to the substrate are accepted under the CONTRIBUTING.md gates.

---

## Decision-making process

### Routine technical decisions

For routine technical decisions inside a phase (e.g., which serialization format for chain entries, which signing library, how to structure a test), the principal investigator decides. The decision is recorded in:

- Code comments (for component-level decisions)
- Commit messages (for change-level decisions)
- Architecture Decision Records in `reports/adrs/` (for cross-cutting decisions)

### Phase transitions

Transitions between ZCS-6 phases (Phase 3 closure → Phase 4 open, Phase 5 closure → Phase 6 open, Phase 6 closure → next major version) require:

1. A phase-closure report in `reports/` documenting what was attempted, what was found, and what was resolved
2. A ledger commit
3. Public announcement in CHANGELOG.md

### Benchmark changes

Benchmark changes require the formal process in "What the benchmark is" above. They cannot be made silently or unilaterally.

### Disagreements

When a contributor and the principal investigator disagree about a technical decision:

1. The disagreement is recorded in a GitHub issue with both positions stated.
2. Both positions are stress-tested against the benchmark (does either position fail a hard floor?) and against the architectural invariants (does either position weaken defense-in-depth?).
3. If one position is empirically dominant, that position wins regardless of who proposed it.
4. If neither position is empirically dominant, the principal investigator decides, with the disagreement recorded as an ADR.
5. The contributor retains the right to fork under Apache 2.0.

This is not democracy; it is benchmark-arbitration with a tiebreaker. The benchmark is the legislature, and the principal investigator interprets it only where it is silent.

---

## Roles

### Principal investigator / lead maintainer

- A. Khaalis Wooden, Sr.
- Owns benchmark integrity
- Owns ledger commits
- Final tiebreaker on benchmark-silent decisions
- Sign-off authority for new major versions
- Speaks for the project in academic submissions, federal capture, and partnership conversations

### Reviewers (named in CHANGELOG.md when they review)

- Reviewers are contributors who have demonstrated facility with the substrate and the methodology and who agree to enforce the CONTRIBUTING.md gates. Reviewer status is offered by the principal investigator; reviewers may also resign at any time.

### Contributors

- Anyone who submits code, documentation, attack findings, or formal verification work under CONTRIBUTING.md. Contributors retain copyright in their contributions; they license under Apache 2.0 at submission time.

### IP holder

- Visionblox LLC, the licensor of record. Visionblox holds the cumulative project copyright (assembled work) and the patent rights for substrate components subject to forthcoming provisional filings.

### Affiliated partners

- Zuup Innovation Lab (the principal investigator's R&D vehicle; IP development workflow). For shell-scope partnership work (HF-1 through HF-7, HF-11), see ROADMAP.md v1.2.

---

## Conflicts of interest

The principal investigator discloses the following continuing affiliations that may create conflicts of interest:

- Director of Enterprise Capture & Compliance at Visionblox LLC (the IP holder of record). Federal contracting work may involve products derived from the substrate.
- Founder of Zuup Innovation Lab. ZIL is the IP development entity.
- MSIT candidate at Southern New Hampshire University. Some material may also be used in academic deliverables.
- The substrate is intended for IEEE / SSRN publication; the IP-and-publication strategy may impose timing constraints on what is disclosed publicly versus held under embargo.

These affiliations are pre-existing and integral to the project's purpose. They do not constitute a conflict for routine technical decisions inside the substrate. They do constrain choices like (a) where the substrate is hosted, (b) which license is used, (c) the timing of public disclosure for novel claims pending patent filing. Decisions in those areas are made by the principal investigator with disclosure to contributors via this section.

---

## Patent strategy and contribution implications

A provisional patent filing covering the substrate (the cross-modal compliance fabric: Aletheia + MVCI + Mercury + Civium + bus isolation as a unified system-and-method claim) is on the 90-day plan. Contributors should know:

- The Apache 2.0 license grant **does** convey the patent license for the contributed code (Section 3 of Apache 2.0).
- The Apache 2.0 license grant **does not** convey to the contributor any patent rights *of the licensor* — i.e., Visionblox LLC's filed claims do not pass to a contributor by virtue of contribution.
- Contributors retain the right to publish their own work independently and to seek their own patent protection for claims that are not subsumed by Visionblox LLC's filing.
- If a contributor's submission contains a novel claim that is patentable, the contributor should disclose this in the PR description so that the principal investigator can decide whether to include it in the Visionblox filing (with credit and a documented agreement) or whether to recommend a separate filing path.

This is a research/development project moving toward IP disclosure. Honesty about novelty and prior art is part of the methodology.

---

## Amendments

Amendments to this governance document require:

1. A pull request modifying GOVERNANCE.md
2. Sign-off from the principal investigator
3. A ledger commit recording the new governance state
4. Communication to active contributors via the project mailing channel

Trivial editorial corrections (typos, link fixes) can be made without ceremony.

---

## In summary

The benchmark legislates. The substrate code executes. The ledger judges. The principal investigator interprets the benchmark in cases where it is silent and is bound by it where it is not. The methodology is falsification-first; honest downward revision of claims is a feature, not a defect. Visionblox LLC is the IP holder. Contributions are welcome under Apache 2.0 with the CONTRIBUTING.md gates.

— A. Khaalis Wooden, Sr.
— Visionblox LLC / Zuup Innovation Lab
