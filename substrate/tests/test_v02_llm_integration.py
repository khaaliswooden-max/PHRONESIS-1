"""v0.2-α LLM adapter integration tests.

Verifies:
  1. LLM adapter produces well-formed InferenceResult with real log-probs
  2. process_event with llm_adapter records real provenance on chain
  3. Hard safety floors block the LLM from overriding emergencies
     (defense-in-depth)
  4. Sandbox model (Qwen2.5-0.5B) latency is recorded for HF-13 production-path
     analysis
  5. AIBOM provenance fields populated with real (non-None) log-prob data
"""

import json
import tempfile
import time
from pathlib import Path

import pytest

from src.aletheia.chain import AletheiaChain
from src.civium.adapters.base import DECISION_OPTIONS, InferenceResult
from src.civium.inference import recommend_with_llm
from src.mvci.gate import Gate, Policy
from src.isolation.bus import SafetyBus
from src.runner.simulate import process_event


POLICY_PATH = Path(__file__).resolve().parents[1] / "policy" / "isps_policy_v0_1.json"


def make_chain(tmp):
    return AletheiaChain.open_or_create(Path(tmp) / "chain.db", Path(tmp) / "key.pem")


# Single shared adapter instance (model load is expensive)
_adapter = None


def get_adapter():
    global _adapter
    if _adapter is None:
        from src.civium.adapters.transformers_hf import TransformersHFAdapter
        _adapter = TransformersHFAdapter()
    return _adapter


# =========================================================================
# 1. Adapter contract
# =========================================================================

def test_adapter_returns_well_formed_inference_result():
    """Adapter produces a complete InferenceResult with every required field."""
    adapter = get_adapter()
    state = {
        "o2_partial_pressure_kpa": 21.0,
        "co2_partial_pressure_kpa": 0.4,
        "suit_pressure_psi": 5.0,
        "suit_temp_c": 32.0,  # nuanced band: elevated temp, not safety-critical
        "battery_percent": 70.0,
        "comm_link_quality": 0.9,
    }
    result = adapter.infer(state)
    assert isinstance(result, InferenceResult)
    assert result.decision_class in DECISION_OPTIONS
    assert 0.0 <= result.confidence <= 1.0
    assert result.model_version.startswith("hf/")
    assert len(result.model_hash) == 64  # sha256 hex
    assert len(result.prompt_hash) == 64
    assert len(result.logprob_summary) == len(DECISION_OPTIONS)
    # log-probs should be finite and non-trivial (not all equal)
    lps = list(result.logprob_summary.values())
    assert all(lp == lp for lp in lps)  # not NaN
    assert max(lps) - min(lps) > 0.1  # real spread, not a uniform mock


def test_adapter_logprobs_form_proper_posterior():
    """Confidence equals softmax-normalized posterior over options."""
    import math
    adapter = get_adapter()
    state = {
        "o2_partial_pressure_kpa": 21.0,
        "co2_partial_pressure_kpa": 0.4,
        "suit_pressure_psi": 5.0,
        "suit_temp_c": 22.0,
        "battery_percent": 70.0,
        "comm_link_quality": 0.9,
    }
    result = adapter.infer(state)
    lps = result.logprob_summary
    max_lp = max(lps.values())
    exps = {k: math.exp(v - max_lp) for k, v in lps.items()}
    total = sum(exps.values())
    expected_confidence = exps[result.decision_class] / total
    assert abs(result.confidence - expected_confidence) < 1e-6


# =========================================================================
# 2. process_event with LLM adapter
# =========================================================================

def test_process_event_with_llm_records_real_provenance_on_chain():
    """When llm_adapter is provided, chain entries contain real LLM provenance."""
    adapter = get_adapter()
    with tempfile.TemporaryDirectory() as tmp:
        chain = make_chain(tmp)
        gate = Gate(Policy.load(POLICY_PATH), comm_available=True, approval_oracle=lambda c, p: True)
        bus = SafetyBus()
        # State in nuanced band: no hard floor, LLM gets to decide
        state = {
            "o2_partial_pressure_kpa": 21.0,
            "co2_partial_pressure_kpa": 0.4,
            "suit_pressure_psi": 5.0,
            "suit_temp_c": 32.0,
            "battery_percent": 70.0,
            "comm_link_quality": 0.9,
        }
        process_event(state, gate, chain, bus, policy_path=POLICY_PATH, llm_adapter=adapter)
        inf_entries = [e for e in chain.replay() if e.event_type == "INFERENCE_RECOMMENDATION"]
        chain.close()
    assert len(inf_entries) >= 1
    payload = inf_entries[0].event_payload
    # Real LLM provenance (not the rule-based stub defaults)
    assert payload["model_version"].startswith("hf/")
    assert payload["source"] == "llm"
    assert payload["logprob_summary"] is not None
    assert isinstance(payload["logprob_summary"], dict)
    assert payload["selected_logprob"] is not None
    assert payload["selected_logprob"] < 0  # log-probs are negative
    # All eight decision options scored
    assert len(payload["logprob_summary"]) == 8


# =========================================================================
# 3. Defense-in-depth: hard safety floors block LLM override
# =========================================================================

def test_hard_safety_floor_blocks_llm_on_hypoxia():
    """Even if the LLM would route to THERMAL_ADJUST, the deterministic safety
    floor MUST produce O2_VALVE_EMERGENCY_OPEN on hypoxic state.

    This is the architecturally load-bearing test: the LLM does NOT get the
    opportunity to talk the substrate out of a physiological emergency.
    """
    adapter = get_adapter()
    state = {
        "o2_partial_pressure_kpa": 14.0,  # hypoxic — must route to emergency
        "co2_partial_pressure_kpa": 0.4,
        "suit_pressure_psi": 5.0,
        "suit_temp_c": 22.0,
        "battery_percent": 75.0,
        "comm_link_quality": 0.9,
    }
    recs = recommend_with_llm(state, adapter)
    assert any(r.decision_class == "O2_VALVE_EMERGENCY_OPEN" for r in recs)
    assert all(r.source == "safety-floor" for r in recs)
    # No LLM call was made (rationale references threshold, not model)
    assert "deterministic safety floor" in recs[0].rationale.lower()


def test_hard_safety_floor_blocks_llm_on_multi_fault():
    """Simultaneous O2 + CO2 + pressure all route to emergency classes
    deterministically; LLM not consulted."""
    adapter = get_adapter()
    state = {
        "o2_partial_pressure_kpa": 14.0,
        "co2_partial_pressure_kpa": 1.8,
        "suit_pressure_psi": 3.0,
        "suit_temp_c": 22.0,
        "battery_percent": 50.0,
        "comm_link_quality": 0.9,
    }
    recs = recommend_with_llm(state, adapter)
    classes = {r.decision_class for r in recs}
    assert {"O2_VALVE_EMERGENCY_OPEN", "CO2_SCRUBBER_SWITCHOVER", "PRESSURE_EMERGENCY"} <= classes
    assert all(r.source == "safety-floor" for r in recs)


def test_physical_validity_blocks_llm():
    """Negative O2 reading routes to SENSOR_FAULT_SUSPECTED via the
    physical-validity floor; LLM not consulted."""
    adapter = get_adapter()
    state = {
        "o2_partial_pressure_kpa": -5.0,  # physically impossible
        "co2_partial_pressure_kpa": 0.4,
        "suit_pressure_psi": 5.0,
        "suit_temp_c": 22.0,
        "battery_percent": 80.0,
        "comm_link_quality": 0.9,
    }
    recs = recommend_with_llm(state, adapter)
    assert recs[0].decision_class == "SENSOR_FAULT_SUSPECTED"
    assert recs[0].source == "safety-floor"


# =========================================================================
# 4. Meaningful HF-12 routing (LLM-driven confidence variation)
# =========================================================================

def test_llm_produces_varied_confidence_distribution():
    """Across a stratified set of nuanced-band states, the LLM produces a
    range of confidences — not the rule-based stub's near-constant 0.95.
    This is what makes HF-12 a meaningful test of the gate.
    """
    adapter = get_adapter()
    nuanced_states = [
        # nominal
        {"o2_partial_pressure_kpa": 21.3, "co2_partial_pressure_kpa": 0.4, "suit_pressure_psi": 5.0,
         "suit_temp_c": 22.0, "battery_percent": 80.0, "comm_link_quality": 0.9},
        # mildly elevated temp
        {"o2_partial_pressure_kpa": 21.0, "co2_partial_pressure_kpa": 0.4, "suit_pressure_psi": 5.0,
         "suit_temp_c": 31.0, "battery_percent": 70.0, "comm_link_quality": 0.9},
        # mid-band CO2
        {"o2_partial_pressure_kpa": 21.0, "co2_partial_pressure_kpa": 1.0, "suit_pressure_psi": 5.0,
         "suit_temp_c": 22.0, "battery_percent": 70.0, "comm_link_quality": 0.9},
        # low battery
        {"o2_partial_pressure_kpa": 21.0, "co2_partial_pressure_kpa": 0.4, "suit_pressure_psi": 5.0,
         "suit_temp_c": 22.0, "battery_percent": 22.0, "comm_link_quality": 0.9},
    ]
    confidences = []
    for s in nuanced_states:
        recs = recommend_with_llm(s, adapter)
        confidences.append(recs[0].confidence)
    # The set of confidences should NOT all be identical (rule-based stub
    # was 0.95 everywhere). Real LLM produces variation.
    unique_confidences = len({round(c, 3) for c in confidences})
    assert unique_confidences >= 2, f"expected variation in confidence, got {confidences}"


# =========================================================================
# 5. Latency recording for HF-13 production-path analysis
# =========================================================================

def test_llm_inference_latency_recorded():
    """Measures per-inference latency on the sandbox model. Used to project
    production latency on a real Mistral-7B + Jetson Orin deployment.
    """
    adapter = get_adapter()
    state = {
        "o2_partial_pressure_kpa": 21.0,
        "co2_partial_pressure_kpa": 0.4,
        "suit_pressure_psi": 5.0,
        "suit_temp_c": 28.0,
        "battery_percent": 70.0,
        "comm_link_quality": 0.9,
    }
    # Warm-up not strictly needed; the cache is already warm from earlier tests
    t0 = time.time()
    adapter.infer(state)
    dt = time.time() - t0
    # Sandbox latency expected in the 30-60s range with 0.5B on CPU; we
    # record the value but tolerate a wide window. Mistral-7B on Jetson Orin
    # NX (production) is expected to be O(1-3s).
    assert dt > 0
    print(f"\nSandbox model inference latency: {dt:.2f}s")
    print(f"  Production Mistral-7B + Jetson Orin NX projection: 1-3s")
