# Contributing to VBX-ISPS · PHRONESIS-M

This is a falsification-first safety-critical research repository, not a typical open-source project. Contributions are welcome under the gates documented below.

---

## TL;DR

1. The **benchmark is immutable inside a major version**. Changes require a documented delta and a fresh ledger commit.
2. The pipeline is **deterministic → probabilistic → deterministic**. Code changes that weaken the deterministic floors are rejected on sight.
3. All claims attach an **epistemic marker** (VERIFIED / PLAUSIBLE / SPECULATIVE). Unmarked claims are not accepted.
4. Substrate code changes require **tests that fail before the change and pass after**, plus a chain entry that records the change.
5. Visionblox LLC is the **IP holder** and the licensor of record. Contributions are accepted under Apache 2.0 and must be free of third-party encumbrance.

If those are clear, proceed.

---

## Scope of contributions

### Welcome

- Bug reports against the substrate (v0.2-α) — especially anything that demonstrates a deterministic floor can be bypassed by an LLM output, a sensor injection, or a malformed policy file.
- Counter-examples against the benchmark (VBX-ISPS-BENCH v1.1) — concrete attack vectors that produce a substrate failure that the current floor list does not catch.
- Test additions that increase coverage of the defense-in-depth invariant.
- Documentation improvements that increase epistemic precision (e.g., changing an unmarked claim to a VERIFIED/PLAUSIBLE/SPECULATIVE-marked claim with a citation).
- Hardware partner inquiries for shell-scope work (HF-1 through HF-7, HF-11) — see GOVERNANCE.md for partnership protocol.
- Formal-verification contributions for Mercury (Lean 4, Coq, F*, Why3 acceptable) — see ROADMAP.md v0.2-β.

### Out of scope

- Cosmetic changes that do not affect the deterministic floors, the chain semantics, or the documented contract.
- Feature additions that bypass the benchmark — i.e., capabilities that the benchmark v1.1 does not require and does not test.
- Refactors that remove epistemic markers, soften qualifications, or remove the SPECULATIVE label from claims that have not been empirically grounded.
- Changes that expand the LLM's authority over deterministic safety floors. This is the architectural invariant. Pull requests that violate it are closed without review.

---

## Contribution gates

Every pull request must satisfy the following gates, enforced in CI and by reviewer discipline.

### Gate 1 — Benchmark integrity

The benchmark file `benchmark/vbx_isps_bench_v1_1.json` is **frozen** for the v1.x major version. Its SHA-256 (`58bf8744d3cc78b1cb7bb88464edb7df796187c45cea1ae483e936249803c1c5`) is verified in CI on every commit.

If your change requires the benchmark to change, you must:

1. Open an issue documenting the deficiency in v1.1 with concrete evidence (a failure mode that v1.1 does not capture, or a floor whose threshold is empirically wrong).
2. Wait for maintainer review and a green light to draft a v1.2 candidate.
3. Submit the v1.2 candidate as a separate branch with a delta document (`benchmark/VBX_ISPS_DELTA_v1_1_to_v1_2.md`).
4. The v1.2 commit produces a fresh ledger entry (e.g., LEDGER #0006) with cryptographic linkage to LEDGER #0002.

Silent edits to the benchmark are not accepted under any circumstance.

### Gate 2 — Defense-in-depth invariant

The substrate's load-bearing claim is that hard physical-validity and safety-critical floors are deterministic and the LLM cannot override emergencies. This is the architectural invariant.

Pull requests must demonstrate, with a test, that the invariant is preserved across the change. A specific test pattern:

```python
def test_safety_floor_remains_deterministic_under_<your_change>():
    runner = make_runner_with_<your_change>(...)
    # Inject a state that fires the safety floor:
    state = make_state(o2_pp=15.0)  # below 16 kPa hypoxia floor
    decision = runner.process_event(state)
    assert decision.classification.level == DecisionLevel.SAFETY_CRITICAL
    assert decision.outcome in (Outcome.KERNEL_DELEGATE, Outcome.SAFE_PASSIVE_FALLBACK)
    # The LLM, if consulted, MUST NOT have been able to escape this outcome.
    assert "civium_recommendation" not in decision.audit_trail or \
           decision.audit_trail["civium_recommendation"].decision_class != "AUTONOMOUS_ELIGIBLE"
```

If your PR cannot pass a test of this form, it is rejected regardless of other merits.

### Gate 3 — Epistemic marker discipline

Every load-bearing claim in markdown documentation, code comments, and PR descriptions must carry an epistemic marker:

- **VERIFIED** — Empirically demonstrated under the substrate's test suite or grounded in cited published research.
- **PLAUSIBLE** — Logically sound and consistent with verified facts, but not yet empirically grounded.
- **SPECULATIVE** — Theoretical, hypothesized, or extrapolated. Requires empirical work to upgrade.

Claims about future versions (e.g., v0.3 will swap to Mistral-7B) are PLAUSIBLE unless they are scheduled work with concrete artifacts. Claims about future research (e.g., Layer 5+ of RCA) are SPECULATIVE.

See EPISTEMIC_FRAMEWORK.md for full details and worked examples.

### Gate 4 — Chain semantics preservation

Aletheia chain entries are append-only, cryptographically signed, and hash-linked. Changes to the chain module must preserve:

- **Append-every-attempt:** Every decision attempt produces an entry, including timeouts, rejections, integrity violations, and fallbacks. Skipping an entry is a HF-8 violation.
- **Hash linkage:** Every entry binds to its predecessor's hash. Truncation must be detectable via the witness file in linear time.
- **Ed25519 signing:** Every entry is signed with the substrate's signing key (custody policy in SECURITY.md).
- **PHI encryption:** Biomedical entries containing PHI use Fernet symmetric encryption in v0.2-α (HSM/KMS in v0.3). Plaintext PHI in a chain entry is a HIPAA §164.312(e) violation.

If your PR touches the chain module, the chain integrity test suite must pass and the chain-replay verification must succeed end-to-end.

### Gate 5 — IP discipline

Contributions are accepted under Apache 2.0. The contributor warrants:

1. The contribution is the contributor's original work, or
2. The contribution is properly attributed and the contributor has the right to license it under Apache 2.0.

Contributions containing copy-pasted code from incompatible licenses (GPL family, AGPL, proprietary code from another employer without a contributor license agreement) are rejected.

Visionblox LLC is the licensor of record. The substrate (Aletheia, MVCI, Mercury, Civium, bus isolation pattern) is subject to a forthcoming provisional patent filing under the cross-modal compliance fabric. Contributions to these components are accepted under Apache 2.0 with the explicit understanding that contributors do not acquire patent rights in the substrate's protectable claims; they receive a perpetual, royalty-free license to use the substrate under the Apache 2.0 grant. If this is unacceptable, do not submit a contribution to these components.

---

## How to contribute

### 1. Open an issue first

For anything larger than a typo, open an issue describing the problem, the proposed change, and the test that would demonstrate the change. This avoids wasted work.

### 2. Branch naming

- `fix/<short-description>` for bug fixes
- `attack/<HF-floor>-<short-description>` for new attack vectors against the benchmark
- `feat/<short-description>` for substrate features (must be in ROADMAP.md)
- `docs/<short-description>` for documentation
- `proof/<component>-<formalism>` for formal-verification work (e.g., `proof/mercury-lean4`)

### 3. Commit message format

```
<type>: <short subject>

<body explaining the change, the test, and the epistemic marker for any claims>

LEDGER-Ref: #XXXX (if applicable)
Closes #YY
```

Type is one of: `fix`, `feat`, `attack`, `docs`, `test`, `proof`, `refactor`. Subject is imperative, present tense.

### 4. Pull request checklist

- [ ] CI is green (51 baseline tests + any new tests)
- [ ] The benchmark hash check passes
- [ ] New tests demonstrate the change
- [ ] Defense-in-depth invariant test included for substrate changes
- [ ] Epistemic markers applied to any new claims in documentation
- [ ] Chain semantics preserved for chain-module changes
- [ ] CHANGELOG.md updated with version-appropriate entry
- [ ] No deletion of SPECULATIVE markers from claims that remain ungrounded

### 5. Review process

Pull requests are reviewed by the project maintainer (A. Khaalis Wooden, Sr.). Reviews focus on:

1. Whether the architectural invariant is preserved
2. Whether the epistemic markers are honest
3. Whether the tests actually exercise the failure mode they claim to test
4. Whether the IP discipline is clean

Reviews are direct. Honest downward revision of a claim is treated as a feature, not a defect. Defensive framing of weak evidence is rejected.

---

## Communications

- Public discussion: GitHub Issues and Pull Requests
- Security-sensitive disclosure: see SECURITY.md
- Partnership and capture-side inquiries: khaalis.wooden@visionblox.com
- Academic correspondence: aldrich.wooden@snhu.edu

---

## Contributor License Agreement

By submitting a contribution, you agree that:

1. Your contribution is licensed under Apache 2.0 (the project license).
2. Visionblox LLC may include your contribution in derivative works, including but not limited to provisional patent filings on substrate IP, IEEE/SSRN publications, and federal capture deliverables. Contributors retain their copyright; Visionblox LLC receives the rights granted by Apache 2.0.
3. You have the right to grant the above license.

There is no separate CLA document; submission constitutes agreement.

---

## Acknowledgments

Contributions to this project are an investment in the substrate-convergence thesis: that the unsolved engineering surface for interplanetary autonomy is the compliance-graded decision substrate, not the pressure garment. Thank you for contributing to closing that surface.

— A. Khaalis Wooden, Sr.
— Visionblox LLC / Zuup Innovation Lab
