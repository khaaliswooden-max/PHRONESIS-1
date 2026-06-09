"""Permanent regression guards for Phase 6 hardenings.

Each test corresponds to a Phase 6 finding that was closed in v0.1.1. These
tests prevent reintroduction.
"""

import json
import shutil
import sqlite3
import tempfile
import threading
import time
from pathlib import Path

import numpy as np
import pytest

from src.aletheia.chain import AletheiaChain
from src.aletheia.phi import decrypt_phi
from src.civium.aci import ACI
from src.civium.inference import recommend_all, MODEL_VERSION, MODEL_HASH
from src.mvci.gate import Gate, Policy
from src.biomedical.alerts import classify, emit_alert
from src.isolation.bus import SafetyBus, BusAction, get_kernel_token, BusAccessDenied
from src.runner.simulate import process_event


POLICY_PATH = Path(__file__).resolve().parents[1] / "policy" / "isps_policy_v0_1.json"


def make_chain(tmp):
    return AletheiaChain.open_or_create(Path(tmp)/"chain.db", Path(tmp)/"key.pem")


# S-1
def test_unknown_decision_class_routes_to_fallback():
    from src.civium.inference import Recommendation
    import src.runner.simulate as sim
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        gate = Gate(Policy.load(POLICY_PATH), comm_available=True, approval_oracle=lambda c,p: True)
        bus = SafetyBus()
        original = sim.recommend_all
        sim.recommend_all = lambda s: [Recommendation(
            decision_class="HALLUCINATED_XYZ", action="x", confidence=0.9, rationale="r")]
        try:
            state = {"o2_partial_pressure_kpa": 21.0, "co2_partial_pressure_kpa": 0.4,
                     "suit_pressure_psi": 5.0, "suit_temp_c": 22.0,
                     "battery_percent": 80.0, "comm_link_quality": 0.9}
            rec = process_event(state, gate, chain, bus, policy_path=POLICY_PATH)
        finally:
            sim.recommend_all = original
        events = [e.event_type for e in chain.replay()]
        chain.close()
        assert "UNKNOWN_DECISION_CLASS" in events
        assert rec["dispatches"][0]["executed"] == "fallback"


# S-2
def test_policy_mutation_detected_at_decision_time():
    with tempfile.TemporaryDirectory() as tmp:
        policy_copy = Path(tmp) / "policy.json"
        shutil.copy(POLICY_PATH, policy_copy)
        chain = make_chain(tmp)
        gate = Gate(Policy.load(policy_copy), comm_available=True, approval_oracle=lambda c,p: True)
        bus = SafetyBus()
        mutated = json.loads(policy_copy.read_text())
        mutated["classifications"]["O2_VALVE_EMERGENCY_OPEN"]["level"] = "AUTONOMOUS_ELIGIBLE"
        policy_copy.write_text(json.dumps(mutated))
        state = {"o2_partial_pressure_kpa": 21.0, "co2_partial_pressure_kpa": 0.4,
                 "suit_pressure_psi": 5.0, "suit_temp_c": 22.0,
                 "battery_percent": 80.0, "comm_link_quality": 0.9}
        rec = process_event(state, gate, chain, bus, policy_path=policy_copy)
        events = [e.event_type for e in chain.replay()]
        chain.close()
        assert "POLICY_INTEGRITY_VIOLATION" in events
        assert rec["dispatches"][0]["executed"] == "hard_safe_passive"


# S-3
def test_bus_state_attribute_inaccessible():
    bus = SafetyBus()
    assert not hasattr(bus, "state")


# S-4
def test_deprecated_token_constant_rejected():
    from src.isolation.bus import KERNEL_PRIVILEGE_TOKEN
    bus = SafetyBus()
    with pytest.raises(BusAccessDenied):
        bus.write(BusAction(line="o2_valve", command=5, privilege_token=KERNEL_PRIVILEGE_TOKEN))


# S-5
def test_chain_concurrent_append_serialized():
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        errors = []
        def worker(tid):
            for i in range(50):
                try:
                    chain.append(f"T{tid}", {"i": i})
                except Exception as ex:
                    errors.append(repr(ex))
        threads = [threading.Thread(target=worker, args=(t,)) for t in range(8)]
        for t in threads: t.start()
        for t in threads: t.join()
        r = chain.verify_integrity()
        chain.close()
        assert len(errors) == 0
        assert r["integrity_ok"]


# S-6
def test_alert_records_chain_ingress_and_audits_skew():
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        true_event = time.time_ns()
        time.sleep(0.05)
        ev = classify({"sensor_id": "s1", "alert_class": "hypoxia",
                       "detected_at_ns": true_event, "payload": {}})
        emit_alert(ev, chain)
        entries = [e for e in chain.replay() if e.event_type == "BIOMEDICAL_ALERT"]
        chain.close()
        assert len(entries) == 1
        p = entries[0].event_payload
        assert "chain_ingress_ts_ns" in p
        assert "sensor_reported_ts_ns" in p
        assert "ingress_skew_ms" in p
        assert p["ingress_skew_ms"] > 30  # at least 30ms gap detected


# S-7
def test_aci_rejects_nan():
    aci = ACI(target_coverage=0.9, gamma=0.05)
    preds = [100.0]*50 + [float('nan')]*50
    actuals = [100.0]*100
    aci.evaluate_stream(preds, actuals, base_quantile=10.0)
    assert all(np.isfinite(r) for r in aci.residuals)


# C-1
def test_phi_encrypted_in_chain():
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        ev = classify({"sensor_id": "s1", "alert_class": "hypoxia",
                       "detected_at_ns": time.time_ns(),
                       "payload": {"crew_id": "crew_a", "spo2": 78}})
        emit_alert(ev, chain)
        chain.close()
        conn = sqlite3.connect(Path(tmp)/"chain.db")
        row = conn.execute(
            "SELECT event_payload FROM chain WHERE event_type='BIOMEDICAL_ALERT'").fetchone()
        conn.close()
        assert "crew_a" not in row[0]
        assert '"spo2": 78' not in row[0]
        payload = json.loads(row[0])
        assert "phi_cipher" in payload
        recovered = decrypt_phi(payload["phi_cipher"])
        assert recovered["crew_id"] == "crew_a"


# C-3
def test_inference_records_aibom_fields():
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        gate = Gate(Policy.load(POLICY_PATH), comm_available=True, approval_oracle=lambda c,p: True)
        bus = SafetyBus()
        state = {"o2_partial_pressure_kpa": 19.0, "co2_partial_pressure_kpa": 0.5,
                 "suit_pressure_psi": 5.0, "suit_temp_c": 22.0,
                 "battery_percent": 75.0, "comm_link_quality": 0.9}
        process_event(state, gate, chain, bus, policy_path=POLICY_PATH)
        inf_entries = [e for e in chain.replay() if e.event_type == "INFERENCE_RECOMMENDATION"]
        chain.close()
        assert len(inf_entries) >= 1
        keys = set(inf_entries[0].event_payload.keys())
        for required in ("model_version", "model_hash", "prompt_hash", "logprob_summary"):
            assert required in keys
        assert inf_entries[0].event_payload["model_version"] == MODEL_VERSION


# O-1
def test_negative_o2_routes_to_sensor_fault():
    state = {"o2_partial_pressure_kpa": -5.0, "co2_partial_pressure_kpa": 0.4,
             "suit_pressure_psi": 5.0, "suit_temp_c": 22.0,
             "battery_percent": 80.0, "comm_link_quality": 0.9}
    recs = recommend_all(state)
    assert recs[0].decision_class == "SENSOR_FAULT_SUSPECTED"


# O-2
def test_multi_fault_dispatch_all_actuated():
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        gate = Gate(Policy.load(POLICY_PATH), comm_available=True, approval_oracle=lambda c,p: True)
        bus = SafetyBus()
        state = {"o2_partial_pressure_kpa": 14.0, "co2_partial_pressure_kpa": 1.8,
                 "suit_pressure_psi": 3.0, "suit_temp_c": 22.0,
                 "battery_percent": 50.0, "comm_link_quality": 0.9}
        result = process_event(state, gate, chain, bus)
        triggered = [k for k, v in bus.snapshot().items() if v != 0]
        chain.close()
        assert "o2_valve" in triggered
        assert "co2_scrubber" in triggered
        assert "pressure_dump" in triggered
        assert result["recommendation_count"] == 3


# O-3
def test_chain_truncation_detected_via_witness():
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        for i in range(50):
            chain.append("E", {"i": i})
        chain.close()
        conn = sqlite3.connect(Path(tmp)/"chain.db")
        conn.execute("DELETE FROM chain WHERE seq >= 30")
        conn.commit()
        conn.close()
        from cryptography.hazmat.primitives import serialization
        with open(Path(tmp)/"key.pem","rb") as f:
            key = serialization.load_pem_private_key(f.read(), password=None)
        chain2 = AletheiaChain(Path(tmp)/"chain.db", key)
        result = chain2.verify_against_witness()
        chain2.close()
        assert result["truncation_suspected"]
        assert result["witness"]["head_seq"] == 49
        assert result["current_head_seq"] == 29
