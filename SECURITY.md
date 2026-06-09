# Security Policy

## Reporting a vulnerability

VBX-ISPS · PHRONESIS-M is a safety-critical research substrate. Vulnerabilities in this codebase have a narrower attack surface than typical software (it is not deployed to flight, it is not in a production system, it is not on a public network), but they nonetheless matter — because the substrate is intended to be the trust root for downstream deployments, and because the falsification-first methodology depends on the substrate's deterministic floors being unfalsifiable in ways the benchmark doesn't catch.

### How to report

**Do not open a public GitHub issue for a vulnerability.** Send email to:

**khaalis.wooden@visionblox.com**

with the subject line `[VBX-ISPS SECURITY]`. Include:

1. A description of the vulnerability with enough detail that a reasonably skilled engineer could reproduce it.
2. The component affected (Aletheia chain, MVCI gate, Mercury kernel, Civium adapter, bus isolation, policy file handling, PHI encryption, witness file).
3. The substrate version (v0.1, v0.1.1, v0.2-α, etc. — see CHANGELOG.md).
4. Whether the vulnerability is exploitable in the current threat model (research/development substrate) or whether it would become exploitable in a future deployment context (flight, hardware silicon, HSM-backed PHI).
5. Your assessment of impact severity (informational / minor / moderate / severe / critical) with a one-paragraph justification.
6. Any proof-of-concept code or test case, with a clear "this is for disclosure only" header.

### What you can expect

- Acknowledgment of receipt within **5 business days**.
- Initial triage and severity confirmation within **14 business days**.
- A coordinated disclosure timeline negotiated with the reporter — typical embargo is 90 days from confirmation, longer if a fix requires a benchmark v1.x → v1.y delta or a hardware partner.
- Public credit in the CHANGELOG.md and SECURITY.md after the embargo expires, unless the reporter requests anonymity.
- A retrospective entry in `reports/` documenting the failure mode, the fix, and the lesson for the methodology.

### What we ask in return

- Please do not disclose the vulnerability publicly until the embargo expires.
- Please do not exploit the vulnerability against any system other than your own development copy.
- Please coordinate with us on any IEEE/SSRN publication of the finding — we are happy to credit and to co-author where appropriate.

---

## Threat model (current scope, v0.2-α)

The substrate's threat model in v0.2-α is **research/development**, not flight. The system is:

- A Python codebase under a single maintainer's control
- Tested with `pytest` on a single machine
- Backed by SQLite chains and on-disk policy files
- Using software-surrogate bus isolation (boot-time secret token, not hardware-enforced)
- Using Fernet symmetric PHI encryption (not HSM-backed)
- Running LLM inference with a sandbox model (Qwen-0.5B) for HF-12 demonstration; production Mistral-7B swap is v0.3

Adversaries in scope:

- A contributor or maintainer who attempts to bypass the architectural invariant by submitting code that weakens the deterministic floors.
- An attacker with file system access to the policy file who attempts to mutate it between the integrity check and the gate evaluation (S-2 Phase 6 mitigation).
- An attacker who attempts to truncate the chain database after-the-fact (O-3 Phase 6 mitigation — witness file detection).
- An attacker who attempts to inject malformed sensor telemetry causing a NaN/Inf to propagate (S-7 Phase 6 mitigation).
- An attacker who attempts to gain bus-write authority without the privilege token (S-4 Phase 6 mitigation — boot secret token).
- An attacker who attempts to cause the gate to mis-classify by mutating policy after load (S-2).

Adversaries out of scope (deferred to later versions):

- A sophisticated adversary with hardware-level access to the compute module — v1.0 hardware partner work, including TPM-backed boot, side-channel-resistant signing, anti-tamper enclosure.
- A nation-state adversary attempting cryptographic key extraction — v0.3 HSM/KMS work.
- An adversary attempting to compromise the ground replication channel — v0.2-β OpenTimestamps anchor work.

---

## Threat model (future deployment scope, v1.0+)

When the substrate is deployed to a real flight system, the threat model expands:

- An adversary with physical access to the suit between EVAs (insider threat, supply chain).
- An adversary attempting to manipulate the LLM model file on the compute module (Q4-quantized weights binary).
- An adversary attempting to spoof biomedical sensor readings to trigger unnecessary fallbacks (denial of life-support availability).
- An adversary attempting to exhaust the chain storage by injecting attempted decisions at high rate.
- An adversary attempting to manipulate the witness file before ground replication.

Mitigations for the flight threat model are gated on v1.0+ work. They are documented in ROADMAP.md.

---

## Signing-key custody

The Aletheia chain uses Ed25519 signing keys. Custody in v0.2-α is:

- The signing key (`key.pem`) is generated locally by the chain's `open_or_create` method on first instantiation.
- The key is stored on the local filesystem with no special protection.
- The key is **not committed to the repository**. The `.gitignore` excludes `*.pem` and the `chain.db` file.
- The key is **not** in a secure element, HSM, or KMS in v0.2-α.

This is appropriate for a research/development substrate but is **not appropriate for flight**. Flight custody requires:

- Key generation in a NIST-validated HSM (FIPS 140-3 Level 3 minimum)
- Key replication to a paired ground HSM for chain verification
- Key rotation policy with documented re-key procedure
- Key destruction at end-of-life with documented attestation

These are gated on v0.3 production-deployment work.

If the development signing key in a contributor's local environment is compromised, the contributor's local chain is compromised. This has no effect on the substrate's claims because no production deployment exists. Regenerate the key by deleting `key.pem` and re-running the substrate; a new chain begins from genesis.

---

## PHI handling

Biomedical alert chain entries (HF-13) carry crew physiological data subject to HIPAA §164.312 (technical safeguards). The substrate's v0.2-α posture:

- PHI is encrypted with Fernet (cryptography library, AES-128-CBC + HMAC-SHA-256) using a key separate from the chain signing key.
- The encryption key is stored on the local filesystem (same custody posture as the signing key, see above).
- PHI is **never** stored in plaintext in the chain.
- PHI cipher text is included in the chain entry's payload field; the entry's hash and signature are computed over the cipher text, not the plaintext.
- A chain reader without the encryption key sees only cipher text, but can still verify the chain's integrity (hash + signature) without decrypting.

This satisfies HIPAA §164.312(e)(1) (transmission security) for the v0.2-α research scope but does **not** satisfy §164.312(a)(2)(iv) (encryption and decryption) for production — that requires the encryption key to be in an HSM/KMS with documented access logging. Gated on v0.3.

If a PHI-handling vulnerability is found in v0.2-α, please report it via the security channel even though no real PHI is in scope. The vulnerability is informational for v0.2-α but blocking for v0.3.

---

## What is NOT a vulnerability

Some properties of the substrate are intentional and are documented as such. They are not vulnerabilities; reports about them will be closed with a pointer to this section:

- **The LLM can produce a probabilistically wrong answer in the nuanced band.** This is the LLM's purpose. The defense is the deterministic floors, the MVCI gate, the chain provenance, and the conformal calibration band — not removing the LLM. A report that says "the LLM was wrong" without showing that a floor was bypassed is not a vulnerability.
- **The chain grows without bound.** This is the append-only contract. Garbage collection of chain entries would defeat HF-8 (provenance survives forever). Storage rotation is a deployment concern, not a substrate vulnerability.
- **The substrate refuses to actuate when comm is unavailable for a REQUIRES_HUMAN decision.** This is HF-9 / HF-12 behavior by design — SAFE_PASSIVE_FALLBACK. A report that says "I lost comm and the suit didn't do what I wanted" is not a vulnerability; the substrate is doing the safety-critical thing.
- **Sandbox LLM (Qwen-0.5B) shows narrow confidence band.** This is a documented sandbox artifact, not a substrate defect. Production (Mistral-7B) is gated on v0.3.

---

## Known security limitations of v0.2-α

For transparency, the following are known limitations explicitly documented in the substrate v0.2-α and deferred to later versions. They are not vulnerabilities to disclose; they are the published v0.2-α posture:

- C-2: filesystem ACLs on `chain.db` and `key.pem` are operator responsibility, not enforced by the code (Phase 6 finding, deferred)
- C-3: AIBOM metadata in chain entries is populated by Civium but not yet validated against a CycloneDX 1.6 / SPDX 2.3 schema (closure path: v0.3)
- FTO-1: provisional patent FTO snapshot is pending practitioner engagement (per Khaalis's 90-day plan)
- HF-10 full: bus isolation is software-surrogate; hardware silicon is v1.0 partner work
- HSM/KMS: signing and PHI keys are local filesystem; HSM/KMS is v0.3

---

## Vulnerability handling philosophy

This project treats vulnerability reports the same way it treats Phase 6 attacks: as evidence that the substrate is not yet what its specification claims. The response is:

1. Acknowledge the report and the contribution.
2. Construct a regression test that exhibits the vulnerability before the fix.
3. Implement the fix.
4. Verify the regression test now passes.
5. Append a chain entry recording the finding, the fix, and the test.
6. Document the lesson in `reports/` and update the threat model if the finding changes its scope.

Falsification is welcome. The substrate gets stronger by being attacked, not by being assumed-correct.

— A. Khaalis Wooden, Sr.
— Visionblox LLC / Zuup Innovation Lab
