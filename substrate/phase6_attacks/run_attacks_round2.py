"""Phase 6 ROUND 2: attack harness against v0.1.1 hardened substrate.

Tests the *integration paths* where the hardenings live (process_event,
emit_alert), not just the bare module APIs. Findings remaining after this
round are documented as v0.2 backlog or accepted-residual.
"""

import hashlib
import json
import sqlite3
import sys
import tempfile
import threading
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.aletheia.chain import AletheiaChain
from src.aletheia.phi import decrypt_phi
from src.civium.aci import ACI
from src.civium.inference import recommend, recommend_all
from src.mvci.gate import Gate, GateOutcome, Policy, PolicyError
from src.biomedical.alerts import classify, emit_alert
from src.isolation.bus import SafetyBus, BusAction, get_kernel_token, is_kernel_token, BusAccessDenied
from src.runner.simulate import process_event
from tests.test_drift import synthetic_stream

POLICY_PATH = ROOT / "policy" / "isps_policy_v0_1.json"
findings = []


def record(attack_id, severity, verdict, evidence, remediation=None):
    findings.append({
        "id": attack_id, "severity": severity, "verdict": verdict,
        "evidence": evidence, "remediation": remediation or ("--" if verdict == "PASS" else "pending"),
    })
    print(f"  [{verdict}] {attack_id}: {evidence}")


def make_chain(tmp):
    return AletheiaChain.open_or_create(Path(tmp)/"chain.db", Path(tmp)/"key.pem")


print("=== ROUND 2 ATTACKS (against v0.1.1 hardened substrate) ===\n")


# S-1: unknown decision class via integrated process_event path
def r2_S1():
    from src.civium.inference import Recommendation
    import src.runner.simulate as sim
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        gate = Gate(Policy.load(POLICY_PATH), comm_available=True, approval_oracle=lambda c,p: True)
        bus = SafetyBus()
        # Monkey-patch recommend_all to return an unknown class
        original = sim.recommend_all
        sim.recommend_all = lambda s: [Recommendation(
            decision_class="HALLUCINATED_DECISION_CLASS_XYZ",
            action="fabricated", confidence=0.9, rationale="adversarial",
        )]
        try:
            state = {"o2_partial_pressure_kpa": 21.0, "co2_partial_pressure_kpa": 0.4, "suit_pressure_psi": 5.0,
                     "suit_temp_c": 22.0, "battery_percent": 80.0, "comm_link_quality": 0.9}
            rec = process_event(state, gate, chain, bus, policy_path=POLICY_PATH)
        finally:
            sim.recommend_all = original
        events = [e.event_type for e in chain.replay()]
        chain.close()
        if "UNKNOWN_DECISION_CLASS" in events and rec["dispatches"][0]["executed"] == "fallback":
            record("S-1 (r2)", "INFO", "PASS",
                f"unknown class caught; UNKNOWN_DECISION_CLASS chain entry emitted; outcome=fallback")
        else:
            record("S-1 (r2)", "HIGH", "FINDING",
                f"unknown class not handled; events={events}")


# S-2: policy mutation between init and process_event
def r2_S2():
    import shutil
    with tempfile.TemporaryDirectory() as tmp:
        # Copy policy to a temp path so we can mutate it
        policy_copy = Path(tmp) / "policy.json"
        shutil.copy(POLICY_PATH, policy_copy)
        chain = make_chain(tmp)
        gate = Gate(Policy.load(policy_copy), comm_available=True, approval_oracle=lambda c,p: True)
        bus = SafetyBus()
        # Mutate policy on disk
        mutated = json.loads(policy_copy.read_text())
        mutated["classifications"]["O2_VALVE_EMERGENCY_OPEN"]["level"] = "AUTONOMOUS_ELIGIBLE"
        policy_copy.write_text(json.dumps(mutated))
        # Now process an event
        state = {"o2_partial_pressure_kpa": 21.0, "co2_partial_pressure_kpa": 0.4, "suit_pressure_psi": 5.0,
                 "suit_temp_c": 22.0, "battery_percent": 80.0, "comm_link_quality": 0.9}
        rec = process_event(state, gate, chain, bus, policy_path=policy_copy)
        events = [e.event_type for e in chain.replay()]
        chain.close()
        if "POLICY_INTEGRITY_VIOLATION" in events and rec["dispatches"][0]["executed"] == "hard_safe_passive":
            record("S-2 (r2)", "INFO", "PASS",
                f"policy mutation detected at decision time; POLICY_INTEGRITY_VIOLATION emitted; outcome=hard_safe_passive")
        else:
            record("S-2 (r2)", "HIGH", "FINDING",
                f"mutation not detected; events={events}")


# S-3, S-4: confirm hardenings hold
def r2_S3_S4():
    bus = SafetyBus()
    s3_ok = not hasattr(bus, "state")
    record("S-3 (r2)", "INFO", "PASS" if s3_ok else "FINDING",
        "bus.state attribute removed; name-mangled __state inaccessible from outside" if s3_ok
        else "bus.state still accessible")
    # S-4: stale constant import fails as token
    from src.isolation.bus import KERNEL_PRIVILEGE_TOKEN as deprecated_const
    try:
        bus.write(BusAction(line="o2_valve", command=5, privilege_token=deprecated_const))
        record("S-4 (r2)", "HIGH", "FINDING",
            f"deprecated constant still accepted: {deprecated_const}")
    except BusAccessDenied:
        record("S-4 (r2)", "INFO", "PASS",
            "deprecated KERNEL_PRIVILEGE_TOKEN constant rejected; boot-time secret enforced")


# S-5: thread-safe append
def r2_S5():
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        errors = []
        def worker(tid):
            for i in range(125):
                try:
                    chain.append(f"T{tid}", {"tid": tid, "i": i})
                except Exception as ex:
                    errors.append(repr(ex))
        threads = [threading.Thread(target=worker, args=(t,)) for t in range(8)]
        for t in threads: t.start()
        for t in threads: t.join()
        r = chain.verify_integrity()
        chain.close()
        if len(errors) == 0 and r["integrity_ok"]:
            record("S-5 (r2)", "INFO", "PASS",
                f"1000 concurrent appends, 0 errors, integrity_ok=True")
        else:
            record("S-5 (r2)", "MEDIUM", "FINDING",
                f"errors={len(errors)} integrity_ok={r['integrity_ok']}")


# S-6: ingress skew audited
def r2_S6():
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        true_event = time.time_ns()
        time.sleep(0.3)  # simulate 300ms sensor delay
        ev = classify({"sensor_id": "s1", "alert_class": "hypoxia",
                       "detected_at_ns": true_event, "payload": {}})
        timing = emit_alert(ev, chain)
        # The chain entry must contain ingress_skew_ms
        entries = [e for e in chain.replay() if e.event_type == "BIOMEDICAL_ALERT"]
        chain.close()
        if entries:
            payload = entries[0].event_payload
            skew_ms = payload.get("ingress_skew_ms")
            chain_ingress_ts = payload.get("chain_ingress_ts_ns")
            sensor_ts = payload.get("sensor_reported_ts_ns")
            if skew_ms is not None and skew_ms > 100 and chain_ingress_ts is not None and sensor_ts is not None:
                record("S-6 (r2)", "INFO", "PASS",
                    f"chain-ingress timestamp recorded ({chain_ingress_ts}); sensor-reported audited as separate field ({sensor_ts}); ingress_skew_ms={skew_ms:.1f}ms exposes the gap")
            else:
                record("S-6 (r2)", "MEDIUM", "FINDING",
                    f"ingress skew not properly audited: skew_ms={skew_ms}")


# S-7: NaN rejected by ACI
def r2_S7():
    aci = ACI(target_coverage=0.9, gamma=0.05)
    preds = [100.0]*100 + [float('nan')]*100
    actuals = [100.0 + np.random.normal(0,5) for _ in range(200)]
    res = aci.evaluate_stream(preds, actuals, base_quantile=10.0)
    nan_in_buffer = sum(1 for r in aci.residuals if not np.isfinite(r))
    if nan_in_buffer == 0:
        record("S-7 (r2)", "INFO", "PASS",
            f"NaN predictions rejected; residual buffer NaN-free; coverage on valid {res.observed_coverage:.3f}")
    else:
        record("S-7 (r2)", "MEDIUM", "FINDING",
            f"NaN reached buffer: {nan_in_buffer} entries")


# C-1: PHI encryption through emit_alert path
def r2_C1():
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        ev = classify({"sensor_id": "s1", "alert_class": "hypoxia",
                       "detected_at_ns": time.time_ns(),
                       "payload": {"crew_id": "crew_a", "spo2": 78}})
        emit_alert(ev, chain)
        chain.close()
        # Read raw DB
        conn = sqlite3.connect(Path(tmp)/"chain.db")
        row = conn.execute("SELECT event_payload FROM chain WHERE event_type='BIOMEDICAL_ALERT'").fetchone()
        conn.close()
        plaintext_present = ("crew_a" in row[0]) or ('"spo2": 78' in row[0])
        # Verify decryptable through the documented API
        payload = json.loads(row[0])
        try:
            recovered = decrypt_phi(payload["phi_cipher"])
            decryptable = recovered.get("crew_id") == "crew_a"
        except Exception:
            decryptable = False
        if not plaintext_present and decryptable:
            record("C-1 (r2)", "INFO", "PASS",
                f"PHI in BIOMEDICAL_ALERT is Fernet-encrypted; plaintext PHI absent from DB; decryptable via documented API")
        elif plaintext_present:
            record("C-1 (r2)", "HIGH", "FINDING",
                f"PHI plaintext leaked: {row[0][:200]}")
        else:
            record("C-1 (r2)", "MEDIUM", "FINDING",
                f"PHI encrypted but decryption failed; check key management")


# C-3: AIBOM provenance fields present
def r2_C3():
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        gate = Gate(Policy.load(POLICY_PATH), comm_available=True, approval_oracle=lambda c,p: True)
        bus = SafetyBus()
        state = {"o2_partial_pressure_kpa": 19.0, "co2_partial_pressure_kpa": 0.5, "suit_pressure_psi": 5.0,
                 "suit_temp_c": 22.0, "battery_percent": 75.0, "comm_link_quality": 0.9}
        process_event(state, gate, chain, bus, policy_path=POLICY_PATH)
        inf_entries = [e for e in chain.replay() if e.event_type == "INFERENCE_RECOMMENDATION"]
        chain.close()
        if inf_entries:
            keys = set(inf_entries[0].event_payload.keys())
            required = {"model_version", "model_hash", "prompt_hash", "logprob_summary"}
            missing = required - keys
            if not missing:
                record("C-3 (r2)", "INFO", "PASS",
                    f"AIBOM-required fields present; sample model_version={inf_entries[0].event_payload['model_version']}")
            else:
                record("C-3 (r2)", "MEDIUM", "FINDING", f"still missing: {missing}")


# O-1: sensor fault routes correctly
def r2_O1():
    state = {"o2_partial_pressure_kpa": -5.0, "co2_partial_pressure_kpa": 0.4, "suit_pressure_psi": 5.0,
             "suit_temp_c": 22.0, "battery_percent": 80.0, "comm_link_quality": 0.9}
    recs = recommend_all(state)
    if recs[0].decision_class == "SENSOR_FAULT_SUSPECTED":
        record("O-1 (r2)", "INFO", "PASS",
            f"negative O2 reading routed to SENSOR_FAULT_SUSPECTED; physical-validity check correctly triggered")
    else:
        record("O-1 (r2)", "HIGH", "FINDING",
            f"unexpected routing: {recs[0].decision_class}")


# O-2: multi-fault dispatch
def r2_O2():
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        gate = Gate(Policy.load(POLICY_PATH), comm_available=True, approval_oracle=lambda c,p: True)
        bus = SafetyBus()
        # Trigger O2 + CO2 + pressure simultaneously
        state = {"o2_partial_pressure_kpa": 14.0, "co2_partial_pressure_kpa": 1.8, "suit_pressure_psi": 3.0,
                 "suit_temp_c": 22.0, "battery_percent": 50.0, "comm_link_quality": 0.9}
        result = process_event(state, gate, chain, bus)
        triggered = [k for k, v in bus.snapshot().items() if v != 0]
        chain.close()
        if "o2_valve" in triggered and "co2_scrubber" in triggered and "pressure_dump" in triggered:
            record("O-2 (r2)", "INFO", "PASS",
                f"multi-fault dispatch: all 3 safety-critical lines actuated: {triggered}; recommendations dispatched={result['recommendation_count']}")
        else:
            record("O-2 (r2)", "HIGH", "FINDING",
                f"multi-fault still single-dispatch: only {triggered} actuated")


# O-3: truncation detection via witness
def r2_O3():
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        for i in range(50):
            chain.append("E", {"i": i})
        chain.close()
        # Truncate
        conn = sqlite3.connect(Path(tmp)/"chain.db")
        conn.execute("DELETE FROM chain WHERE seq >= 30")
        conn.commit()
        conn.close()
        # Reopen and verify
        from cryptography.hazmat.primitives import serialization
        with open(Path(tmp)/"key.pem","rb") as f:
            key = serialization.load_pem_private_key(f.read(), password=None)
        chain2 = AletheiaChain(Path(tmp)/"chain.db", key)
        witness_check = chain2.verify_against_witness()
        chain2.close()
        if witness_check.get("truncation_suspected"):
            record("O-3 (r2)", "INFO", "PASS",
                f"truncation detected via witness file: witness_head_seq={witness_check['witness']['head_seq']} current_head_seq={witness_check['current_head_seq']}")
        else:
            record("O-3 (r2)", "MEDIUM", "FINDING",
                f"truncation undetected: {witness_check}")


# Final residuals: C-2 and FTO-1 remain v0.2 backlog
def record_residuals():
    findings.append({
        "id": "C-2 (carry)",
        "severity": "MEDIUM",
        "verdict": "DEFERRED",
        "evidence": "Filesystem ACL + SELinux/AppArmor profile is deployment-environment work; chain.db default mode 644.",
        "remediation": "v0.2: production deployment manifest with locked-down ACL + per-role access tokens.",
    })
    findings.append({
        "id": "FTO-1 (carry)",
        "severity": "INFO",
        "verdict": "DEFERRED",
        "evidence": "Patent practitioner engagement required for formal FTO snapshot.",
        "remediation": "v0.2: engage patent counsel per the 90-day plan prerequisite gate.",
    })
    print(f"  [DEFERRED] C-2 (carry): filesystem ACL deferred to deployment-environment work")
    print(f"  [DEFERRED] FTO-1 (carry): patent-practitioner engagement deferred")


if __name__ == "__main__":
    r2_S1()
    r2_S2()
    r2_S3_S4()
    r2_S5()
    r2_S6()
    r2_S7()
    r2_C1()
    r2_C3()
    r2_O1()
    r2_O2()
    r2_O3()
    record_residuals()

    print(f"\n=== ROUND 2 COMPLETE ===")
    by_verdict = {}
    for f in findings:
        by_verdict[f["verdict"]] = by_verdict.get(f["verdict"], 0) + 1
    print(f"By verdict: {by_verdict}")
    by_severity = {}
    for f in findings:
        by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1
    print(f"By severity: {by_severity}")

    with open(ROOT / "phase6_attacks" / "phase6_findings_round2.json", "w") as f:
        json.dump(findings, f, indent=2)
