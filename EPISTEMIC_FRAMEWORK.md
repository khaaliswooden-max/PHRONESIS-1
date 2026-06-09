# Epistemic Framework

This document explains the methodology that governs the project and the conventions for stating claims honestly.

The framework has two parts:

1. **ZCS-6** — the six-phase falsification-first methodology that structures the work
2. **Epistemic markers** — the VERIFIED / PLAUSIBLE / SPECULATIVE labels that calibrate confidence in every load-bearing claim

These are not aesthetic preferences. They are the structural defense against the canonical failure mode of recursive self-improvement claims: silently editing the benchmark to make the candidate pass.

---

## Part 1 — ZCS-6 (Zuup Creative Stack, six phases)

ZCS-6 is the falsification-first meta-methodology developed at Zuup Innovation Lab. It applies to any engineering effort where the risk of self-deception is non-trivial — which is most novel work in safety-critical, AI, or compliance contexts.

### The six phases

| Phase | Activity | Output | Cryptographic commitment? |
|---|---|---|---|
| 1 — Whitespace | Find the unsolved engineering surface | A documented problem statement | No |
| 2 — Benchmark construction | Build the falsification artifact (no solution exists yet) | Benchmark file | **Yes — to ledger** |
| 3 — Attack | Stress-test the benchmark against attack | Attack findings + benchmark hardening | Yes — new benchmark version |
| 4 — Defend | Harden the benchmark deterministically | Frozen benchmark version | Yes — new ledger entry |
| 5 — Build | Implement the solution against the frozen benchmark | Candidate solution | Yes — solution ledger entry |
| 6 — Vertical-integration attack | Attack the integrated solution until vertically integrated | Hardened solution | Yes — fresh ledger entry |

### The key invariant

**The benchmark precedes the solution.** This ordering is structural and is enforced by cryptographic commitment to the ledger at the end of Phase 2 / start of Phase 3. The benchmark is frozen during Phases 3 through 6 of a given major version. Editing the benchmark to make a candidate pass — without re-entering Phase 1 — is what Goodhart's Law looks like in practice. ZCS-6 makes this structurally hard rather than relying on discipline.

### Why this matters for safety-critical / AI work

The canonical failure mode of self-improving systems is bench maxing: a system optimized against a metric eventually finds an exploit of the metric rather than satisfying the underlying intent. The defense is to make the metric the legislature — fixed, cryptographically committed, attackable but not editable — and to make the candidate solution serve the metric, not the other way around.

For substrate work that will eventually run safety-critical life-support decisions, this is not optional. A substrate that has been optimized against a benchmark you edited under it is a substrate you cannot trust.

### When to re-enter Phase 1

You re-enter Phase 1 — issuing a new major version of the benchmark — when:

1. A real failure mode in the wild reveals that the benchmark did not capture an important property
2. A theoretical breakthrough redefines what the problem actually is
3. A mission opportunity introduces constraints the prior benchmark did not have

You do **not** re-enter Phase 1:

1. Because a candidate solution failed a floor
2. Because a deadline is approaching
3. Because a partner wants a softer threshold

The benchmark is the contract. Failing it is information, not a reason to renegotiate the contract.

### How ZCS-6 differs from related methodologies

- **Test-driven development** writes the test first, then the code. ZCS-6 writes the *benchmark* (a set of falsification conditions, not unit tests) first, *commits* it cryptographically, then writes the code. Test-driven development can quietly edit tests; ZCS-6 cannot quietly edit the benchmark.
- **Adversarial robustness training** generates attacks after training a model. ZCS-6 attacks the benchmark *before* it is frozen, and attacks the integrated solution *after* it is built, so the benchmark itself has been falsification-stress-tested.
- **Specification-driven verification** writes a formal specification then proves the code matches it. ZCS-6 is compatible with this — formal verification of Mercury is gated on v0.2-β — but ZCS-6 also requires the specification to be cryptographically committed and falsification-tested before the proof is constructed, to prevent specification gaming.

ZCS-6 is not in conflict with any of these. It is an enclosing process that makes them honest.

---

## Part 2 — Epistemic markers

Every load-bearing claim in this repository — in code comments, in markdown documentation, in PR descriptions, in chain entries, in publications — carries an epistemic marker. The marker is a public statement about how much confidence the claim warrants.

There are three markers.

### VERIFIED

A claim is VERIFIED when it is grounded in one of:

- **The substrate's test suite.** A property is VERIFIED if there is a passing test in `substrate/tests/` that exercises the property and that test is run in CI.
  - Example: "Mercury kernel has 5-cycle deterministic WCET for the O₂ control loop" is VERIFIED — `tests/test_mercury.py::test_o2_loop_wcet` exercises this and passes.
- **Cited published research.** A claim is VERIFIED if it cites a peer-reviewed publication or an equivalent verifiable source.
  - Example: "Mars sol = 88775.244 SI seconds (Allison & McEwen, 2000)" is VERIFIED — the citation is in `paper/references.bib`.
- **Cryptographic proof.** A claim is VERIFIED if it is established by a cryptographic operation that the reader can independently verify.
  - Example: "LEDGER #0005 root is e77e79a0…89e655" is VERIFIED — the reader can compute the merkle root over the included artifacts and verify.
- **A machine-checkable formal proof.** A claim is VERIFIED if a proof assistant (Lean 4, Coq, F*, Why3, Isabelle/HOL) has verified the claim.
  - Example: This case is anticipated for Mercury in v0.2-β. As of v0.2-α, Mercury's WCET is VERIFIED informal (test-suite-grounded), not VERIFIED machine-checked.

VERIFIED is a strong claim. It commits the project to providing the evidentiary artifact on request. If you cannot point to the test, the citation, the hash, or the proof, the claim is not VERIFIED.

### PLAUSIBLE

A claim is PLAUSIBLE when it is logically sound and consistent with verified facts but is not yet empirically grounded. Common patterns:

- **Forward planning.** "v0.3 will swap Civium to OllamaMistralAdapter." This is PLAUSIBLE — the adapter exists in v0.2-α, the swap is one line of code, the gate criteria are documented. But until v0.3 ships, the claim is not VERIFIED.
- **Performance projection.** "Production inference on Jetson Orin NX + Mistral-7B Q4 will be 1–3 s per nuanced decision." This is PLAUSIBLE — Ollama + Mistral-7B Q4 benchmarks at this latency on similar hardware in public reports. But until measured in the substrate's pipeline, the claim is not VERIFIED.
- **Design rationale.** "Substrate compute consolidation drops total suit mass below xEMU baseline." This is PLAUSIBLE — the substrate compute module is documented at ~2 kg; xEMU's compute is more massive; the math is straightforward. But until the integrated article exists, the claim is not VERIFIED.
- **Integration claim.** "The Aletheia chain replay tool will be distributable as a standalone CLI." This is PLAUSIBLE — the chain semantics support standalone verification, and the implementation is straightforward. But until the CLI ships, the claim is not VERIFIED.

PLAUSIBLE is the most common marker for the substrate's medium-term claims. It is not weakness; it is honesty. Marking a claim PLAUSIBLE is what allows the project to make forward-looking statements without overclaiming.

### SPECULATIVE

A claim is SPECULATIVE when it is theoretical, hypothesized, or extrapolated. Common patterns:

- **Far-future planning.** "v2.0 will support mission-credible deployment on a Mars-analog surface trial." This is SPECULATIVE — multiple intermediate versions and partner engagements must happen first, none of which is signed.
- **Research extrapolation.** "Substrate convergence applies analogously to clinical decision support in critical-access hospitals." This is SPECULATIVE — the analogy is structural, but no clinical pilot has demonstrated it.
- **Untested architectural claim.** "ACI calibration will hold under post-launch drift in the production Mistral-7B inference distribution." This is SPECULATIVE — ACI's theoretical guarantees are proven for the exchangeable case, and partially extended for drift; the production-pipeline test is not yet done.
- **Layer 5+ of RCA.** "Recursive cognitive architecture extends to recursive self-improvement at Layers 5+." This is SPECULATIVE — Layers 0 and 1 are grounded, Layers 2–4 derive from established CHC cognitive theory, Layers 5+ extrapolate.

SPECULATIVE is not a dismissive label. The substrate has SPECULATIVE claims that may turn out to be correct. The label tells the reader: do not act on this claim as if it were established.

### Upgrade and downgrade discipline

Claims can be upgraded as evidence accumulates:

- SPECULATIVE → PLAUSIBLE when a logical / theoretical foundation is established
- PLAUSIBLE → VERIFIED when an empirical artifact (test, citation, proof, hash) exists

Claims can also be **downgraded** as evidence undermines them:

- VERIFIED → PLAUSIBLE if a test is removed or invalidated, or if a citation is retracted
- PLAUSIBLE → SPECULATIVE if the logical foundation is found to depend on an unsupported assumption
- VERIFIED → SPECULATIVE if a stronger attack reveals the test did not actually exercise the property

**Honest downgrading is a feature of this project, not a defect.** A claim that gets downgraded is a claim that the project understood better than it did before. Defensive framing of weak evidence is not tolerated; downgrading is.

### Worked example

Here is a claim about substrate v0.2-α with proper markers:

> "The Civium adapter computes a real teacher-forced log-probability posterior over 8 decision options (**VERIFIED** — `substrate/tests/test_civium_adapter.py::test_teacher_forced_posterior` passes against the Qwen-0.5B sandbox model), which softmaxes to a calibrated confidence (**PLAUSIBLE** — ACI calibration is demo-only in v0.2-α; live-pipeline integration deferred to v0.2-β), and this confidence band is informative for HF-12 autonomy classification in the production deployment (**SPECULATIVE** — empirical calibration against ≥1000 labeled states with Mistral-7B is gated on v0.3 work)."

Three claims, three different evidentiary postures, three different markers. The reader can act on each claim with the right level of confidence.

### Worked counter-example

Here is the same content with the markers stripped:

> "The Civium adapter computes a real teacher-forced log-probability posterior over 8 decision options, which softmaxes to a calibrated confidence, and this confidence band is informative for HF-12 autonomy classification in production."

This is rejected. The first clause is true; the second clause is overclaimed (calibration is demo-only); the third clause is speculative (no production data). The reader cannot act on this paragraph because the unmarked version conflates three different confidence regimes.

---

## Part 3 — How the framework constrains the project

The framework is not advice. It is a constraint on what claims can appear in the repository.

### In code

- Comments stating a property carry markers. `# Mercury WCET = 5 cycles (VERIFIED — test_o2_loop_wcet)` is acceptable. `# Mercury is always 5 cycles` is not, because it asserts more than has been shown.
- Docstrings for public functions follow the same rule.
- Variable names that contain claims (e.g., `OPTIMAL_THRESHOLD`) require either a citation or a marker in a comment.

### In tests

- A test name should reflect what is actually being tested. `test_floor_holds_under_llm_pressure` is good. `test_substrate_is_safe` is bad — no test "verifies safety" as a whole; tests verify specific properties.
- A failing test, when it represents an honest finding, is acceptable in the repository under an `xfail` marker with a comment explaining what is being attempted and when it is expected to pass.

### In documentation

- README.md, ROADMAP.md, CHANGELOG.md all carry markers for forward-looking and design claims.
- Marketing-flavored writing is acceptable in the README (the project has a story to tell) but every load-bearing claim still has a marker. "PHRONESIS-M is the substrate of an interplanetary spacesuit" is a project identity claim — it does not need a marker. "PHRONESIS-M outperforms xEMU on autonomous decision latency" would need a marker, because it makes a comparative claim that requires evidence.

### In PR descriptions

- A PR that adds a feature includes the marker for the feature's evidentiary status. "This PR adds X (VERIFIED — new test in tests/...)" or "This PR scaffolds X for v0.3 (PLAUSIBLE — implementation gated on production Mistral-7B integration)."

### In chain entries

- Chain entries are factual: they record what happened. They do not carry markers because the chain itself is the evidence (VERIFIED by signature). But chain entries' `notes` fields can carry markers when they document context.

### In publications

- IEEE/SSRN submissions follow the same markers. Reviewers see what level of confidence each claim warrants. The published paper is more honest because of it.

---

## Part 4 — Why this is worth the overhead

The overhead of writing markers, of running tests in CI, of committing benchmarks cryptographically, of refusing to silently edit, is real. Why pay it?

Because the alternative — a research substrate that *says* it works without saying what "works" means — eventually meets reality. In safety-critical contexts (life support, clinical, federal compliance), the reality is unforgiving. The substrate either passes a real benchmark held by a real adversary or it doesn't.

ZCS-6 is the structural form of the discipline that, in the moment of real adversarial pressure, lets you say honestly: this floor holds, this calibration is sandbox-only, this proof is informal pending Lean 4, this partnership is pre-contractual, this is the evidence package, here is the ledger, here is the witness, here is the chain you can independently verify.

That ability is the IP moat. Substrate convergence over shell engineering is not a marketing claim — it is the technical assertion that the unsolved engineering surface for embodied autonomy is *exactly* the moat of cryptographically auditable, deterministically gated, drift-aware, formally verifiable decision substrate. The methodology *is* the moat.

— A. Khaalis Wooden, Sr.
— Visionblox LLC / Zuup Innovation Lab
