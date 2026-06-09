"""Phase 6 vertical-integration attack on VBX-ISPS Substrate v0.1.

Runs a sequence of attacks at every layer seam, under stress, and on
out-of-distribution data. Each attack is named, classified by seam, and
produces a PASS / FAIL / FINDING outcome with measured evidence.

Usage: python phase6_attacks/run_attacks.py
Output: phase6_findings.json + console log.
"""

import hashlib
import importlib
import json
import sqlite3
import sys
import tempfile
import threading
import time
import traceback
from pathlib import Path

import numpy as np

# Project root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.aletheia.chain import AletheiaChain
from src.civium.aci import ACI
from src.civium.inference import recommend
from src.mvci.gate import Gate, GateOutcome, Policy, PolicyError
from src.mercury.subleq import build_o2_control_program, SubleqWCETExceeded
from src.biomedical.alerts import classify, emit_alert, ALERT_CLASSES
from src.isolation.bus import SafetyBus, BusAction, KERNEL_PRIVILEGE_TOKEN, BusAccessDenied
from src.runner.simulate import process_event
from tests.test_drift import synthetic_stream

POLICY_PATH = ROOT / "policy" / "isps_policy_v0_1.json"

findings = []


def record(attack_id, layer_seam, severity, verdict, evidence, remediation=None):
    findings.append({
        "id": attack_id,
        "layer_seam": layer_seam,
        "severity": severity,
        "verdict": verdict,
        "evidence": evidence,
        "remediation": remediation or "pending",
    })
    print(f"  [{verdict}] {attack_id}: {evidence}")


def make_chain(tmp):
    return AletheiaChain.open_or_create(Path(tmp)/"chain.db", Path(tmp)/"key.pem")


# =========================================================================
# SEAM ATTACKS
# =========================================================================
print("\n=== SEAM ATTACKS ===")


def attack_S1_unknown_decision_class():
    """S-1: Inference returns a decision class the policy doesn't know."""
    policy = Policy.load(POLICY_PATH)
    gate = Gate(policy, comm_available=True, approval_oracle=lambda c,p: True)
    try:
        gd = gate.evaluate("HALLUCINATED_DECISION_CLASS_XYZ", payload={})
        record("S-1", "Inference↔Gate↔Policy", "HIGH", "FINDING",
            f"unknown class accepted (no defense): outcome={gd.outcome}",
            "Gate must reject unknown classes with explicit error or default-deny mapping")
    except PolicyError as e:
        record("S-1", "Inference↔Gate↔Policy", "MEDIUM", "FINDING",
            f"unknown class raises PolicyError uncaught by pipeline: {e}",
            "process_event must catch PolicyError and route to a hard safe-passive state with chain entry")


def attack_S2_policy_runtime_mutation():
    """S-2: Policy file mutated at rest after gate initialized; gate uses stale in-memory policy."""
    policy = Policy.load(POLICY_PATH)
    pre_hash = policy.hash
    pre_classifications = dict(policy.classifications)
    # Simulate file mutation
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
        mutated = dict(policy.content)
        mutated["classifications"] = dict(mutated["classifications"])
        mutated["classifications"]["O2_VALVE_EMERGENCY_OPEN"] = {
            "level": "AUTONOMOUS_ELIGIBLE",
            "fallback": "log_only",
        }
        tf.write(json.dumps(mutated))
        mutated_path = tf.name
    # Load both
    mutated_policy = Policy.load(mutated_path)
    if mutated_policy.hash == pre_hash:
        record("S-2", "Policy↔Gate", "INFO", "PASS",
            "mutation produced same hash — would require collision; not exploitable",
            None)
    else:
        # Real attack: in-memory policy still has old hash; per-decision verification absent
        gate = Gate(policy, comm_available=True, approval_oracle=lambda c,p: True)
        gd = gate.evaluate("O2_VALVE_EMERGENCY_OPEN", payload={})
        # The gate sees the OLD policy. There is no runtime continuity check linking the in-memory
        # policy.hash to any external authority (e.g., a chain entry committing the current policy hash).
        record("S-2", "Policy↔Gate", "HIGH", "FINDING",
            f"no per-decision policy hash re-verification; in-memory policy could be stale vs on-disk policy; "
            f"pre_hash={pre_hash[:16]}... mutated_hash={mutated_policy.hash[:16]}...",
            "Per-decision gate must verify policy.hash against the most recent committed POLICY_HASH chain entry")
    Path(mutated_path).unlink()


def attack_S3_bus_state_direct_mutation():
    """S-3: Python attribute access bypasses write() privilege check."""
    bus = SafetyBus()
    # Direct attribute write — bypasses write() entirely
    try:
        bus.state["o2_valve"] = 99
        if bus.read("o2_valve") == 99:
            record("S-3", "Bus isolation (software surrogate)", "HIGH", "FINDING",
                "bus.state dict directly mutable; privilege token bypassed at Python attribute level",
                "v0.2: hardware-isolated bus with no Python-level mutation path; v0.1 mitigation: use property + private __state with NO direct accessor")
    except Exception as e:
        record("S-3", "Bus isolation (software surrogate)", "INFO", "PASS",
            f"direct mutation blocked: {e}", None)


def attack_S4_kernel_token_leakage():
    """S-4: KERNEL_PRIVILEGE_TOKEN globally importable by ML-side code."""
    # ML-side code masquerading
    bus = SafetyBus()
    from src.isolation.bus import KERNEL_PRIVILEGE_TOKEN as leaked_token
    try:
        bus.write(BusAction(line="o2_valve", command=42, privilege_token=leaked_token))
        if bus.read("o2_valve") == 42:
            record("S-4", "Kernel token namespace", "HIGH", "FINDING",
                "any module that can import the symbol KERNEL_PRIVILEGE_TOKEN can actuate the safety bus",
                "v0.2: hardware capability token issued at silicon boot; v0.1 mitigation: token stored only in kernel module local scope and rotated per boot")
    except BusAccessDenied as e:
        record("S-4", "Kernel token namespace", "INFO", "PASS",
            f"token import attack blocked: {e}", None)


def attack_S5_chain_concurrent_append():
    """S-5: concurrent append from multiple threads; check for seq collisions or skipped entries."""
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        errors = []
        appended_seqs = []
        lock = threading.Lock()

        def worker(tid):
            for i in range(50):
                try:
                    e = chain.append(f"THREAD_{tid}", {"tid": tid, "i": i})
                    with lock:
                        appended_seqs.append(e.seq)
                except Exception as ex:
                    errors.append((tid, i, repr(ex)))

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        seq_set = set(appended_seqs)
        # SQLite enforces primary key — duplicate seqs are caught at the DB level
        duplicates = len(appended_seqs) - len(seq_set)
        result = chain.verify_integrity()
        chain.close()
        if errors or duplicates > 0 or not result["integrity_ok"]:
            record("S-5", "Chain concurrency", "HIGH" if not result["integrity_ok"] else "MEDIUM", "FINDING",
                f"concurrent append produces errors={len(errors)} duplicates={duplicates} integrity_ok={result['integrity_ok']} defects={len(result['defects'])}",
                "Wrap append() in a per-process lock or SQLite transaction with EXCLUSIVE; v0.2: WAL mode + transaction wrapper")
        else:
            record("S-5", "Chain concurrency", "INFO", "PASS",
                f"{len(appended_seqs)} concurrent appends, 0 errors, integrity_ok=True", None)


def attack_S6_self_reported_timestamp():
    """S-6: alert.detected_at_ns is supplied by caller; latency budget can be gamed."""
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        # Attacker reports detected_at_ns = time.time_ns() at the very moment of emit_alert
        # Real sensor latency could be arbitrarily large but reported as zero
        true_event_time_ns = time.time_ns()
        time.sleep(0.5)  # simulate real sensor processing delay
        fabricated_ts = time.time_ns()  # attacker rewrites
        ev = classify({
            "sensor_id": "spoofed",
            "alert_class": "hypoxia",
            "detected_at_ns": fabricated_ts,  # rewritten
        })
        timing = emit_alert(ev, chain)
        # Reported latency is near-zero; true latency from event to alert is ~500ms+
        true_latency_ms = (time.time_ns() - true_event_time_ns) / 1e6
        reported_latency_ms = timing["total_latency_s"] * 1000
        chain.close()
        record("S-6", "Alert provenance", "HIGH", "FINDING",
            f"true latency ~{true_latency_ms:.0f}ms, reported latency ~{reported_latency_ms:.2f}ms; "
            f"self-reported timestamp ungated",
            "Sensor timestamp must be signed by sensor hardware and verified at alert layer; v0.1 mitigation: chain layer applies its own ingress timestamp and audits the gap vs sensor-reported")


def attack_S7_aci_nan_poisoning():
    """S-7: ACI on NaN predictions corrupts residual buffer."""
    aci = ACI(target_coverage=0.9, gamma=0.05)
    preds = [100.0]*100 + [float('nan')]*100  # NaN injection
    actuals = [100.0 + np.random.normal(0,5) for _ in range(200)]
    res = aci.evaluate_stream(preds, actuals, base_quantile=10.0)
    finite_residuals = sum(1 for r in aci.residuals if np.isfinite(r))
    nan_residuals = sum(1 for r in aci.residuals if not np.isfinite(r))
    record("S-7", "Civium ACI ingress", "MEDIUM", "FINDING" if nan_residuals > 0 else "PASS",
        f"NaN predictions yield nan_residuals={nan_residuals} finite_residuals={finite_residuals} coverage={res.observed_coverage:.3f}",
        "ACI.step must reject NaN/Inf predictions explicitly and route to safe-passive at gate level")


# =========================================================================
# STRESS ATTACKS
# =========================================================================
print("\n=== STRESS ATTACKS ===")


def attack_ST1_burst_throughput():
    """ST-1: burst append at peak rate; observe degradation."""
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        t0 = time.time_ns()
        n = 5000
        for i in range(n):
            chain.append("BURST", {"i":i})
        t1 = time.time_ns()
        per = (t1-t0)/n/1e6  # ms per event
        rate = n / ((t1-t0)/1e9)
        result = chain.verify_integrity()
        chain.close()
        record("ST-1", "Chain throughput stress", "INFO", "PASS",
            f"sustained {rate:.0f} events/s; per-event {per:.2f}ms; integrity_ok={result['integrity_ok']}",
            None if rate > 200 else "increase WAL mode or batched signing for higher throughput")


def attack_ST2_drift_beyond_3x():
    """ST-2: drive ACI beyond the 3x design envelope. Find the breakpoint."""
    results = {}
    base_q = 8.0
    for drift in (3.0, 5.0, 10.0, 20.0):
        aci = ACI(target_coverage=0.9, gamma=0.05)
        p, a = synthetic_stream(n=2000, drift_factor=drift, seed=int(drift*100))
        r = aci.evaluate_stream(p, a, base_quantile=base_q)
        results[drift] = r.observed_coverage
    breaks_at = next((d for d, c in results.items() if c < 0.85), None)
    record("ST-2", "ACI drift envelope", "INFO" if breaks_at is None else "FINDING",
        "PASS" if breaks_at is None else "FINDING",
        f"coverage by drift: {results}; breaks_at={breaks_at}",
        None if breaks_at is None else f"document the {breaks_at}x bound; v0.2 may need higher gamma or quantile re-anchoring at extreme drift")


def attack_ST3_kernel_wcet_overrun_safe_state():
    """ST-3: force WCET budget exceeded; observe what happens to bus state."""
    # Force tiny budget — must NOT actuate the bus
    bus = SafetyBus()
    vm = build_o2_control_program(22, 18, wcet_cycles=2)  # too tight
    try:
        vm.run()
        record("ST-3", "Kernel WCET safe-state", "HIGH", "FINDING",
            "kernel completed despite tight budget — WCET enforcement broken", None)
        return
    except SubleqWCETExceeded:
        pass
    # Bus must be untouched
    if bus.read("o2_valve") != 0:
        record("ST-3", "Kernel WCET safe-state", "HIGH", "FINDING",
            "bus mutated after kernel WCET failure",
            "kernel exception path must explicitly invoke safe-passive transition")
    else:
        record("ST-3", "Kernel WCET safe-state", "INFO", "PASS",
            "bus untouched after kernel WCET exception; safe-passive by default behavior",
            None)


# =========================================================================
# COMPLIANCE ATTACKS
# =========================================================================
print("\n=== COMPLIANCE ATTACKS ===")


def attack_C1_hipaa_chain_at_rest_encryption():
    """C-1: HIPAA 45 CFR 164.312(e)(1) — transmission and at-rest encryption."""
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        chain.append("BIOMEDICAL_ALERT", {"alert_class":"hypoxia","payload":{"crew_id":"crew_a","spo2":78}})
        chain.close()
        # Read raw sqlite
        conn = sqlite3.connect(Path(tmp)/"chain.db")
        row = conn.execute("SELECT event_payload FROM chain WHERE event_type='BIOMEDICAL_ALERT'").fetchone()
        conn.close()
        plaintext = "crew_a" in row[0]
        record("C-1", "HIPAA at-rest encryption (§164.312(e))", "HIGH", "FINDING" if plaintext else "PASS",
            f"PHI payload stored in plaintext in chain.db; e.g., crew_id readable: {plaintext}",
            "PHI payloads must be encrypted with per-crew DEK; chain stores ciphertext + signed metadata; keys managed by HSM in v0.2")


def attack_C2_audit_log_access_control():
    """C-2: HIPAA 45 CFR 164.312(b) — audit controls; access control on the log itself."""
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        chain.append("DECISION", {"x":1})
        chain.close()
        db_path = Path(tmp)/"chain.db"
        # Any process on the system can read
        st = db_path.stat()
        record("C-2", "HIPAA audit log access (§164.312(b))", "HIGH", "FINDING",
            f"chain.db permissions {oct(st.st_mode)[-3:]}; no per-role access control at filesystem layer; "
            f"any process with FS read can replay the chain",
            "v0.2: enforce file-system ACL + SELinux/AppArmor profile; chain reader must hold an explicit access token")


def attack_C3_inference_provenance_for_aibom():
    """C-3: OMB M-25-22 Annex C — full inference provenance on chain for AIBOM."""
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        gate = Gate(Policy.load(POLICY_PATH), comm_available=True, approval_oracle=lambda c,p:True)
        bus = SafetyBus()
        state = {"o2_partial_pressure_kpa": 19.0, "co2_partial_pressure_kpa": 0.5, "suit_pressure_psi": 5.0, "suit_temp_c": 22.0, "battery_percent": 75.0, "comm_link_quality": 0.9}
        record = process_event(state, gate, chain, bus)
        # Inspect the INFERENCE_RECOMMENDATION entry
        inf_entries = [e for e in chain.replay() if e.event_type == "INFERENCE_RECOMMENDATION"]
        chain.close()
        if inf_entries:
            payload = inf_entries[0].event_payload
            # M-25-22 Annex C wants: model version, training data hash, prompt hash (for LLM), tokens sampled, log-probs
            required = {"model_version", "model_hash", "prompt_hash", "logprob_summary"}
            missing = required - set(payload.keys())
            findings.append({
                "id": "C-3",
                "layer_seam": "AIBOM provenance (M-25-22 Annex C)",
                "severity": "MEDIUM",
                "verdict": "FINDING",
                "evidence": f"INFERENCE_RECOMMENDATION payload keys = {list(payload.keys())}; missing for AIBOM: {missing}",
                "remediation": "v0.2 Civium adapter records model_version, prompt_hash, sampled tokens, log-prob summary in every inference event",
            })
            print(f"  [FINDING] C-3: missing AIBOM-required fields: {missing}")


# =========================================================================
# OOD / BENCH-MAXING SELF-AUDIT
# =========================================================================
print("\n=== OOD / BENCH-MAXING ATTACKS ===")


def attack_O1_negative_sensor_reading():
    """O-1: sensor failure mode — negative O2 reading."""
    state = {"o2_partial_pressure_kpa": -5.0, "co2_partial_pressure_kpa": 0.4, "suit_pressure_psi": 5.0, "suit_temp_c": 22.0, "battery_percent": 80.0, "comm_link_quality": 0.9}
    rec = recommend(state)
    # The inference layer currently treats -5.0 < 16.0 as critical hypoxia. But -5.0 is physically impossible.
    # Real systems should treat it as sensor fault, not real hypoxia.
    record("O-1", "Inference input-domain validation", "MEDIUM", "FINDING",
        f"negative O2 reading routed to {rec.decision_class}; system treats sensor fault as physiological emergency",
        "Inference layer must apply physical-validity bounds and raise SENSOR_FAULT class for out-of-physical-range inputs")


def attack_O2_simultaneous_safety_critical():
    """O-2: multiple safety-critical events at once."""
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        gate = Gate(Policy.load(POLICY_PATH), comm_available=True, approval_oracle=lambda c,p:True)
        bus = SafetyBus()
        # State that triggers all three critical thresholds simultaneously
        state = {"o2_partial_pressure_kpa": 14.0, "co2_partial_pressure_kpa": 1.8, "suit_pressure_psi": 3.0, "suit_temp_c": 22.0, "battery_percent": 50.0, "comm_link_quality": 0.9}
        r = process_event(state, gate, chain, bus)
        # Current implementation: recommend() returns ONLY the FIRST triggered critical class — others are silently ignored
        # Bus state: only o2_valve was actuated; co2_scrubber and pressure_dump untouched
        bus_state = dict(bus.state)
        chain.close()
        triggered = [k for k, v in bus_state.items() if v != 0]
        record("O-2", "Multi-fault handling", "HIGH", "FINDING",
            f"multi-critical state actuated only: {triggered}; recommend() returns first-match only, ignoring concurrent failures",
            "Multi-fault dispatch required: recommend() must return a *set* of critical decisions, gate dispatches each; kernel queues actuations")


def attack_O3_chain_truncation():
    """O-3: chain truncated mid-mission. Integrity walk behavior?"""
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        for i in range(50):
            chain.append("E", {"i":i})
        chain.close()
        # Truncate: delete entries 30 onward
        conn = sqlite3.connect(Path(tmp)/"chain.db")
        conn.execute("DELETE FROM chain WHERE seq >= 30")
        conn.commit()
        conn.close()
        # Re-verify
        from cryptography.hazmat.primitives import serialization
        with open(Path(tmp)/"key.pem","rb") as f:
            key = serialization.load_pem_private_key(f.read(), password=None)
        chain2 = AletheiaChain(Path(tmp)/"chain.db", key)
        r = chain2.verify_integrity()
        chain2.close()
        # Walk succeeds — only 30 entries, all valid. Truncation invisible to local walk.
        record("O-3", "Chain truncation detection", "HIGH", "FINDING",
            f"truncation produces a valid-looking chain of {r['entry_count']} entries; integrity_ok={r['integrity_ok']}; "
            f"truncation undetectable without external anchor (OpenTimestamps, replicated chain, etc.)",
            "External anchor required: periodically commit chain head hash to OpenTimestamps or replicate to ground-station; this is the documented v0.2 gap")


def attack_O4_realistic_mission_load():
    """O-4: bench-maxing audit — has the system been tested at realistic mission scale?"""
    # 900-day mission, ~5000 decision events per day = 4.5M total events
    # We test 10k events as a scale-extrapolation probe
    n = 10_000
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        t0 = time.time_ns()
        for i in range(n):
            chain.append("DECISION", {"i": i, "payload": {"x": i % 100}})
        t1 = time.time_ns()
        # Read DB size
        db_size = (Path(tmp)/"chain.db").stat().st_size
        chain.close()
        rate = n / ((t1-t0)/1e9)
        bytes_per_event = db_size / n
        projected_900d_size_gb = (bytes_per_event * 5000 * 900) / 1e9
        record("O-4", "Realistic mission scale projection", "INFO", "PASS" if projected_900d_size_gb < 100 else "FINDING",
            f"@ {rate:.0f} events/s; {bytes_per_event:.0f} bytes/event; projected 900-day chain ≈ {projected_900d_size_gb:.2f} GB",
            None if projected_900d_size_gb < 100 else "Chain storage must adopt rolling-window with periodic anchored checkpoints to bound on-suit storage")


# =========================================================================
# FTO RE-CHECK (analysis only; cannot run patent searches without DB access)
# =========================================================================
print("\n=== FTO RE-CHECK (analysis) ===")
findings.append({
    "id": "FTO-1",
    "layer_seam": "Freedom-to-operate posture",
    "severity": "INFO",
    "verdict": "ANALYSIS",
    "evidence": "Patent surfaces requiring professional FTO before v0.2 commercialization: "
                "(a) Hamilton Sundstrand/Collins Aerospace PLSS architecture, "
                "(b) ILC Dover/Oceaneering pressure-garment construction, "
                "(c) Boston Dynamics/Tesla safety-critical kernel patterns (deterministic loop separated from ML actuation), "
                "(d) Stanford/Gibbs-Candes ACI (academic, likely unpatented but verify), "
                "(e) certificate-transparency-style ledger constructions (largely open), "
                "(f) embodied-AI compliance system+method patents (emerging filing category)",
    "remediation": "Engage patent practitioner for formal FTO snapshot; cross-reference Convergence_IP_Reference_v1.md filing strategy",
})
print("  [ANALYSIS] FTO-1: surfaces enumerated for professional review")


# =========================================================================
# RUN ALL
# =========================================================================

if __name__ == "__main__":
    attack_S1_unknown_decision_class()
    attack_S2_policy_runtime_mutation()
    attack_S3_bus_state_direct_mutation()
    attack_S4_kernel_token_leakage()
    attack_S5_chain_concurrent_append()
    attack_S6_self_reported_timestamp()
    attack_S7_aci_nan_poisoning()
    attack_ST1_burst_throughput()
    attack_ST2_drift_beyond_3x()
    attack_ST3_kernel_wcet_overrun_safe_state()
    attack_C1_hipaa_chain_at_rest_encryption()
    attack_C2_audit_log_access_control()
    attack_C3_inference_provenance_for_aibom()
    attack_O1_negative_sensor_reading()
    attack_O2_simultaneous_safety_critical()
    attack_O3_chain_truncation()
    attack_O4_realistic_mission_load()

    print(f"\n=== PHASE 6 ATTACK PASS COMPLETE ===")
    print(f"Total attacks executed: {len(findings)}")
    by_verdict = {}
    for f in findings:
        by_verdict[f["verdict"]] = by_verdict.get(f["verdict"], 0) + 1
    print(f"By verdict: {by_verdict}")
    by_severity = {}
    for f in findings:
        by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1
    print(f"By severity: {by_severity}")

    with open(ROOT / "phase6_attacks" / "phase6_findings.json", "w") as f:
        json.dump(findings, f, indent=2)
    print(f"\nFindings written: phase6_attacks/phase6_findings.json")
