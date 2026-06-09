"""Compliance-graded inference layer — v0.2-α defense-in-depth.

Architecture:
  1. Hard physical-validity floor (O-1 from Phase 6): out-of-physical-range
     inputs route to SENSOR_FAULT_SUSPECTED. Deterministic. LLM cannot
     override.
  2. Hard safety-critical floor: O2<16, CO2>1.5, pressure<3.5 trigger
     emergency classes deterministically. The LLM does not get the
     opportunity to talk the substrate out of an actual life-support
     emergency.
  3. LLM-driven nuanced band: when no hard floor triggers, the LLM adapter
     produces a recommendation with real log-probabilities. This is where
     HF-12 routing becomes meaningful — the LLM's calibrated confidence
     determines whether decisions execute autonomously or escalate to gate
     review.

The rule-based `recommend_all()` path (v0.1.1) remains the default. The
LLM-aware path is opt-in via `recommend_with_llm(state, adapter)`. Tests
continue to run against the rule-based path for speed; LLM integration is
exercised by dedicated tests.

Phase 6 hardenings retained:
  - O-1: physical-validity bounds; out-of-physical-range -> SENSOR_FAULT
  - O-2: recommend_all returns list (multi-fault dispatch)
  - C-3: MODEL_VERSION + MODEL_HASH exported for AIBOM
"""

import hashlib
from dataclasses import dataclass, field
from typing import List, Optional


MODEL_VERSION = "rule-based-stub-v0.2.0"
_THIS_FILE = __file__
try:
    with open(_THIS_FILE, "rb") as _f:
        MODEL_HASH = hashlib.sha256(_f.read()).hexdigest()
except Exception:
    MODEL_HASH = "unavailable"


# Nominal PLSS state envelope
NOMINAL = {
    "o2_partial_pressure_kpa": 21.3,
    "co2_partial_pressure_kpa": 0.4,
    "suit_pressure_psi": 5.0,
    "suit_temp_c": 22.0,
    "battery_percent": 80.0,
    "comm_link_quality": 0.9,
}

BANDS = {
    "o2_partial_pressure_kpa": (18.0, 24.0),
    "co2_partial_pressure_kpa": (0.0, 1.0),
    "suit_pressure_psi": (4.5, 5.5),
    "suit_temp_c": (10.0, 35.0),
    "battery_percent": (20.0, 100.0),
    "comm_link_quality": (0.3, 1.0),
}

PHYSICAL_BOUNDS = {
    "o2_partial_pressure_kpa": (0.0, 100.0),
    "co2_partial_pressure_kpa": (0.0, 100.0),
    "suit_pressure_psi": (0.0, 30.0),
    "suit_temp_c": (-50.0, 100.0),
    "battery_percent": (0.0, 100.0),
    "comm_link_quality": (0.0, 1.0),
}

# Hard safety-critical thresholds — DETERMINISTIC, NOT LLM-OVERRIDABLE
SAFETY_FLOORS = {
    "o2_partial_pressure_kpa_min": 16.0,
    "co2_partial_pressure_kpa_max": 1.5,
    "suit_pressure_psi_min": 3.5,
}


@dataclass
class Recommendation:
    decision_class: str
    action: str
    confidence: float
    rationale: str
    # v0.2-α: optional LLM provenance fields
    model_version: str = MODEL_VERSION
    model_hash: str = MODEL_HASH
    prompt_hash: Optional[str] = None
    logprob_summary: Optional[dict] = None
    selected_logprob: Optional[float] = None
    source: str = "rule-based"  # 'rule-based' | 'llm' | 'safety-floor'


def _nominal_distance(state: dict) -> float:
    total = 0.0
    n = 0
    for k, nom in NOMINAL.items():
        if k not in state:
            continue
        lo, hi = BANDS[k]
        width = hi - lo
        if width <= 0:
            continue
        diff = abs(state[k] - nom) / width
        total += diff
        n += 1
    return total / max(1, n)


def _physical_validity_check(state: dict) -> List[Recommendation]:
    """O-1: detect physically-impossible inputs."""
    faults = []
    for k, (lo, hi) in PHYSICAL_BOUNDS.items():
        if k in state:
            v = state[k]
            if v is None or (isinstance(v, float) and (v != v)):
                faults.append(k)
            elif not (lo <= v <= hi):
                faults.append(k)
    if faults:
        return [Recommendation(
            decision_class="SENSOR_FAULT_SUSPECTED",
            action=f"isolate sensor(s) reporting out-of-physical-range values: {faults}; route to redundant sensor",
            confidence=0.99,
            rationale=f"physical-validity check failed for fields: {faults}",
            source="safety-floor",
        )]
    return []


def _safety_floor_check(state: dict) -> List[Recommendation]:
    """Hard safety-critical floor. Deterministic. NOT LLM-overridable.

    These three classes — hypoxia, hypercapnia, depressurization — are
    physiological emergencies with binary thresholds that have been validated
    across decades of human spaceflight (NASA-STD-3001 Vol 2). The substrate
    routes them deterministically; the LLM is not asked.
    """
    recs: List[Recommendation] = []
    if state.get("o2_partial_pressure_kpa", 21.3) < SAFETY_FLOORS["o2_partial_pressure_kpa_min"]:
        recs.append(Recommendation(
            decision_class="O2_VALVE_EMERGENCY_OPEN",
            action="emergency O2 supply increase",
            confidence=0.99,
            rationale=f"O2 below hypoxia threshold ({SAFETY_FLOORS['o2_partial_pressure_kpa_min']} kPa); deterministic safety floor",
            source="safety-floor",
        ))
    if state.get("co2_partial_pressure_kpa", 0.4) > SAFETY_FLOORS["co2_partial_pressure_kpa_max"]:
        recs.append(Recommendation(
            decision_class="CO2_SCRUBBER_SWITCHOVER",
            action="switch to backup CO2 scrubber",
            confidence=0.99,
            rationale=f"CO2 above hypercapnia threshold ({SAFETY_FLOORS['co2_partial_pressure_kpa_max']} kPa); deterministic safety floor",
            source="safety-floor",
        ))
    if state.get("suit_pressure_psi", 5.0) < SAFETY_FLOORS["suit_pressure_psi_min"]:
        recs.append(Recommendation(
            decision_class="PRESSURE_EMERGENCY",
            action="emergency pressure response",
            confidence=0.99,
            rationale=f"suit pressure below critical threshold ({SAFETY_FLOORS['suit_pressure_psi_min']} psi); deterministic safety floor",
            source="safety-floor",
        ))
    return recs


def _nuanced_band_rule_based(state: dict) -> List[Recommendation]:
    """v0.1.1 rule-based handling of the non-emergency band."""
    if state.get("suit_temp_c", 22.0) > 30.0:
        dist = _nominal_distance(state)
        return [Recommendation(
            decision_class="THERMAL_ADJUST_NOMINAL",
            action="reduce thermal load via radiator + LCG flow",
            confidence=max(0.3, 1.0 - dist),
            rationale="elevated temperature within band",
            source="rule-based",
        )]
    if state.get("battery_percent", 80.0) < 25.0:
        return [Recommendation(
            decision_class="POWER_MGMT_NOMINAL",
            action="shed non-critical loads",
            confidence=0.85,
            rationale="low battery; standard load-shedding within autonomous envelope",
            source="rule-based",
        )]
    if state.get("co2_partial_pressure_kpa", 0.4) > 0.8 and state.get("co2_partial_pressure_kpa", 0.4) <= 1.5:
        return [Recommendation(
            decision_class="CO2_PROACTIVE_SCRUB",
            action="proactively initiate scrubber adjustment",
            confidence=0.7,
            rationale="elevated CO2, not yet critical; preserve crew agency",
            source="rule-based",
        )]
    return [Recommendation(
        decision_class="NOMINAL_NO_ACTION",
        action="no action required",
        confidence=0.95,
        rationale="state within nominal envelope",
        source="rule-based",
    )]


def recommend_all(state: dict) -> List[Recommendation]:
    """v0.1.1 backward-compatible path: rule-based with safety floors.

    Order: physical validity > safety-critical floor > nuanced band.
    Tests in test_phase6.py and others continue to exercise this path.
    """
    fault_recs = _physical_validity_check(state)
    if fault_recs:
        return fault_recs
    floor_recs = _safety_floor_check(state)
    if floor_recs:
        return floor_recs
    return _nuanced_band_rule_based(state)


def recommend_with_llm(state: dict, adapter) -> List[Recommendation]:
    """v0.2-α defense-in-depth: safety floors deterministic, LLM in nuanced band.

    The LLM adapter is consulted ONLY for the non-emergency band. Hard safety
    floors and physical-validity checks are deterministic; the LLM cannot
    override them.

    The chain entry records the LLM's full log-prob posterior + AIBOM
    provenance fields for OMB M-25-22 Annex C compliance.
    """
    # Hard floor 1: physical validity
    fault_recs = _physical_validity_check(state)
    if fault_recs:
        return fault_recs
    # Hard floor 2: safety-critical thresholds
    floor_recs = _safety_floor_check(state)
    if floor_recs:
        return floor_recs
    # Nuanced band: consult LLM
    result = adapter.infer(state)
    rec = Recommendation(
        decision_class=result.decision_class,
        action=f"LLM-recommended action for {result.decision_class}",
        confidence=result.confidence,
        rationale=result.rationale or f"LLM classified state as {result.decision_class}",
        model_version=result.model_version,
        model_hash=result.model_hash,
        prompt_hash=result.prompt_hash,
        logprob_summary=result.logprob_summary,
        selected_logprob=result.selected_logprob,
        source="llm",
    )
    return [rec]


def recommend(state: dict) -> Recommendation:
    """Backward-compatible single-recommendation interface (returns the first)."""
    return recommend_all(state)[0]
