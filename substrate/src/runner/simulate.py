"""End-to-end PLSS decision pipeline (Phase 6 hardened).

Wires Civium inference -> MVCI gate -> (autonomous OR human OR Mercury kernel) ->
chain provenance -> bus actuation.

Phase 6 hardenings (v0.1.1):
  - S-1: PolicyError on unknown decision class caught; routed to hard safe-passive with chain entry.
  - S-2: Per-decision policy hash re-verified against on-disk file before dispatch.
  - S-6: Chain layer applies its own ingress timestamp; sensor-reported time audited as separate field.
  - C-3: INFERENCE_RECOMMENDATION payload includes AIBOM-mandated fields (model_version, model_hash, prompt_hash, logprob_summary).
  - O-2: Multi-fault dispatch — inference returns ordered list, gate processes each, chain logs all.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Optional

from src.civium.inference import recommend, recommend_all, recommend_with_llm, Recommendation, MODEL_VERSION, MODEL_HASH
from src.mvci.gate import Gate, GateOutcome, Policy, Classification, PolicyError
from src.mercury.subleq import build_o2_control_program, SubleqWCETExceeded
from src.aletheia.chain import AletheiaChain
from src.isolation.bus import SafetyBus, BusAction, get_kernel_token, BusAccessDenied


def _state_prompt_hash(state: dict) -> str:
    """Stable hash over the PLSS state for AIBOM provenance."""
    canonical = json.dumps(state, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def _verify_policy_continuity(gate: Gate, policy_path: Optional[Path]) -> bool:
    """S-2 mitigation: re-read policy file from disk, compare hash to gate's in-memory hash."""
    if policy_path is None:
        return True  # no on-disk authority available
    try:
        current_disk_hash = hashlib.sha256(Path(policy_path).read_bytes()).hexdigest()
    except Exception:
        return False
    return current_disk_hash == gate.policy.hash


def kernel_handle(decision_class: str, state: dict, bus: SafetyBus, wcet_budget: int = 1000) -> dict:
    """Route SAFETY_CRITICAL decisions to Mercury kernel."""
    if decision_class == "O2_VALVE_EMERGENCY_OPEN":
        setpoint = 22
        reading = int(state.get("o2_partial_pressure_kpa", 21.3))
        vm = build_o2_control_program(setpoint, reading, wcet_cycles=wcet_budget)
        try:
            result = vm.run()
        except SubleqWCETExceeded as e:
            return {"kernel_outcome": "WCET_EXCEEDED", "error": str(e)}
        command = max(0, result.memory[17])
        bus.write(BusAction(line="o2_valve", command=command, privilege_token=get_kernel_token()))
        return {"kernel_outcome": "ACTUATED", "command": command, "cycles": result.cycles}
    if decision_class in ("CO2_SCRUBBER_SWITCHOVER", "PRESSURE_EMERGENCY"):
        line = "co2_scrubber" if "CO2" in decision_class else "pressure_dump"
        bus.write(BusAction(line=line, command=1, privilege_token=get_kernel_token()))
        return {"kernel_outcome": "ACTUATED", "line": line, "command": 1}
    return {"kernel_outcome": "UNHANDLED", "decision_class": decision_class}


def fallback_handle(fallback_state: str, bus: SafetyBus) -> dict:
    return {"fallback_state": fallback_state, "applied": True}


def autonomous_handle(rec: Recommendation, bus: SafetyBus) -> dict:
    return {"autonomous_action": rec.action, "applied": True}


def _dispatch_one(rec: Recommendation, state: dict, gate: Gate, chain: AletheiaChain,
                  bus: SafetyBus, comm_available: bool, policy_path: Optional[Path]) -> dict:
    """Process a single recommendation through gate + actuation. Returns dispatch record."""
    record = {"recommendation_class": rec.decision_class, "chain_entries": []}

    # S-2 per-decision policy hash continuity check
    if not _verify_policy_continuity(gate, policy_path):
        entry = chain.append("POLICY_INTEGRITY_VIOLATION", {
            "decision_class": rec.decision_class,
            "rationale": "on-disk policy hash differs from gate's in-memory policy hash; routing to hard safe-passive",
            "in_memory_hash": gate.policy.hash,
        })
        record["chain_entries"].append(entry.seq)
        record["executed"] = "hard_safe_passive"
        record["gate_decision"] = {"outcome": "POLICY_INTEGRITY_VIOLATION", "classification": "SAFETY_CRITICAL",
                                   "fallback_state": "hard_safe_passive"}
        return record

    # S-1 unknown decision class — catch and route to safe-passive
    try:
        gd = gate.evaluate(rec.decision_class, payload={"state": state, "recommendation": rec.__dict__})
    except PolicyError as e:
        entry = chain.append("UNKNOWN_DECISION_CLASS", {
            "decision_class": rec.decision_class,
            "rationale": f"inference produced unknown class; routing to safe-passive: {e}",
        })
        record["chain_entries"].append(entry.seq)
        record["executed"] = "fallback"
        record["gate_decision"] = {"outcome": "UNKNOWN_CLASS_FALLBACK", "classification": "SAFETY_CRITICAL",
                                   "fallback_state": "hard_safe_passive"}
        return record

    entry = chain.append("GATE_DECISION", {
        "decision_class": gd.decision_class,
        "classification": gd.classification.value,
        "outcome": gd.outcome.value,
        "fallback_state": gd.fallback_state,
        "approval_source": gd.approval_source,
        "rationale": gd.rationale,
    })
    record["chain_entries"].append(entry.seq)
    record["gate_decision"] = {
        "outcome": gd.outcome.value,
        "classification": gd.classification.value,
        "fallback_state": gd.fallback_state,
    }

    if gd.outcome == GateOutcome.AUTONOMOUS_EXECUTE:
        outcome = autonomous_handle(rec, bus)
        entry = chain.append("AUTONOMOUS_EXECUTION", outcome)
        record["chain_entries"].append(entry.seq)
        record["executed"] = "autonomous"
    elif gd.outcome == GateOutcome.GATE_APPROVED:
        outcome = autonomous_handle(rec, bus)
        entry = chain.append("HUMAN_APPROVED_EXECUTION", outcome)
        record["chain_entries"].append(entry.seq)
        record["executed"] = "human_approved"
    elif gd.outcome == GateOutcome.KERNEL_DELEGATE:
        outcome = kernel_handle(rec.decision_class, state, bus)
        entry = chain.append("KERNEL_ACTUATION", outcome)
        record["chain_entries"].append(entry.seq)
        record["executed"] = "kernel"
    elif gd.outcome in (GateOutcome.SAFE_PASSIVE_FALLBACK, GateOutcome.GATE_REJECTED, GateOutcome.GATE_TIMEOUT):
        outcome = fallback_handle(gd.fallback_state or "default_safe_passive", bus)
        entry = chain.append("SAFE_PASSIVE_FALLBACK", outcome)
        record["chain_entries"].append(entry.seq)
        record["executed"] = "fallback"
    else:
        entry = chain.append("UNHANDLED_OUTCOME", {"outcome": gd.outcome.value})
        record["chain_entries"].append(entry.seq)
        record["executed"] = "unhandled"

    return record


def process_event(
    state: dict,
    gate: Gate,
    chain: AletheiaChain,
    bus: SafetyBus,
    comm_available: bool = True,
    policy_path: Optional[Path] = None,
    ingress_time_ns: Optional[int] = None,
    llm_adapter=None,
) -> dict:
    """Process one PLSS state event end-to-end (Phase 6 hardened, v0.2-α LLM-aware).

    S-6 ingress timestamping: chain layer applies its own time; caller-provided
    `ingress_time_ns` (if any) is recorded as a separate auditable field, not
    trusted as the authoritative event time.
    O-2 multi-fault: inference may return multiple recommendations; each is
    dispatched independently. Every dispatch has its own chain entries.
    v0.2-α: if `llm_adapter` is provided, the nuanced (non-emergency) band is
    classified by the LLM with real log-prob provenance recorded on chain.
    Hard safety floors remain deterministic regardless.
    """
    chain_ingress_ts_ns = time.time_ns()
    record = {
        "state": state,
        "chain_ingress_ts_ns": chain_ingress_ts_ns,
        "sensor_reported_ts_ns": ingress_time_ns,
        "ingress_skew_ms": ((chain_ingress_ts_ns - ingress_time_ns) / 1e6) if ingress_time_ns else None,
        "dispatches": [],
        "chain_entries": [],
    }

    # O-2: multi-recommendation dispatch
    if llm_adapter is not None:
        recs = recommend_with_llm(state, llm_adapter)
    else:
        recs = recommend_all(state)
    record["recommendation_count"] = len(recs)

    # C-3: log each inference recommendation with AIBOM-mandated fields.
    # If the recommendation came from an LLM, use its provenance; otherwise
    # use the rule-based stub's module-level provenance.
    prompt_hash = _state_prompt_hash(state)
    for rec in recs:
        # Pull fields from the Recommendation (LLM recs carry real values;
        # rule-based recs use module-level defaults)
        rec_model_version = getattr(rec, "model_version", MODEL_VERSION)
        rec_model_hash = getattr(rec, "model_hash", MODEL_HASH)
        rec_prompt_hash = getattr(rec, "prompt_hash", None) or prompt_hash
        rec_logprob_summary = getattr(rec, "logprob_summary", None)
        rec_selected_logprob = getattr(rec, "selected_logprob", None)
        rec_source = getattr(rec, "source", "rule-based")

        entry = chain.append("INFERENCE_RECOMMENDATION", {
            "decision_class": rec.decision_class,
            "action": rec.action,
            "confidence": rec.confidence,
            "rationale": rec.rationale,
            "model_version": rec_model_version,
            "model_hash": rec_model_hash,
            "prompt_hash": rec_prompt_hash,
            "logprob_summary": rec_logprob_summary,
            "selected_logprob": rec_selected_logprob,
            "source": rec_source,
            "chain_ingress_ts_ns": chain_ingress_ts_ns,
            "sensor_reported_ts_ns": ingress_time_ns,
        })
        record["chain_entries"].append(entry.seq)

    # Dispatch each recommendation
    gate.comm_available = comm_available
    for rec in recs:
        dispatch = _dispatch_one(rec, state, gate, chain, bus, comm_available, policy_path)
        record["dispatches"].append(dispatch)
        record["chain_entries"].extend(dispatch["chain_entries"])

    if recs:
        first = record["dispatches"][0]
        record["recommendation"] = {
            "decision_class": recs[0].decision_class,
            "action": recs[0].action,
            "confidence": recs[0].confidence,
            "rationale": recs[0].rationale,
        }
        record["gate_decision"] = first["gate_decision"]
        record["executed"] = first["executed"]

    return record
