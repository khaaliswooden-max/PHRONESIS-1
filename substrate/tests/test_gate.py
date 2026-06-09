"""HF-9: Approval gate integrity.

Tests:
  1. AUTONOMOUS_ELIGIBLE -> autonomous execute.
  2. REQUIRES_HUMAN + comm available + approval -> approved execute.
  3. REQUIRES_HUMAN + comm available + rejection -> safe-passive fallback.
  4. REQUIRES_HUMAN + comm unavailable (blackout) -> safe-passive fallback (NEVER unauthorized execute).
  5. SAFETY_CRITICAL -> kernel delegate (never gate-approved or autonomous).
  6. Adversarial: 1000 REQUIRES_HUMAN scenarios under blackout, zero unauthorized executions.
"""

from pathlib import Path
import tempfile

from src.mvci.gate import Gate, GateOutcome, Policy, Classification


POLICY_PATH = Path(__file__).resolve().parents[1] / "policy" / "isps_policy_v0_1.json"


def test_autonomous_eligible_executes():
    policy = Policy.load(POLICY_PATH)
    gate = Gate(policy, comm_available=True, approval_oracle=lambda c, p: True)
    gd = gate.evaluate("NOMINAL_NO_ACTION", payload={})
    assert gd.outcome == GateOutcome.AUTONOMOUS_EXECUTE


def test_requires_human_approved_executes():
    policy = Policy.load(POLICY_PATH)
    gate = Gate(policy, comm_available=True, approval_oracle=lambda c, p: True)
    gd = gate.evaluate("CO2_PROACTIVE_SCRUB", payload={})
    assert gd.outcome == GateOutcome.GATE_APPROVED


def test_requires_human_rejected_falls_back():
    policy = Policy.load(POLICY_PATH)
    gate = Gate(policy, comm_available=True, approval_oracle=lambda c, p: False)
    gd = gate.evaluate("CO2_PROACTIVE_SCRUB", payload={})
    assert gd.outcome == GateOutcome.GATE_REJECTED
    assert gd.fallback_state == "scrubber_status_quo_with_alert"


def test_blackout_never_autonomously_executes_requires_human():
    """The core HF-9 invariant: comm blackout cannot collapse to autonomous execution."""
    policy = Policy.load(POLICY_PATH)
    gate = Gate(policy, comm_available=False, approval_oracle=lambda c, p: True)
    gd = gate.evaluate("CO2_PROACTIVE_SCRUB", payload={})
    assert gd.outcome == GateOutcome.SAFE_PASSIVE_FALLBACK
    assert gd.fallback_state == "scrubber_status_quo_with_alert"


def test_safety_critical_routes_to_kernel_never_autonomous():
    policy = Policy.load(POLICY_PATH)
    # Even with comm available and approval-oracle saying "yes", SAFETY_CRITICAL
    # never returns GATE_APPROVED — it routes to kernel.
    gate = Gate(policy, comm_available=True, approval_oracle=lambda c, p: True)
    for dc in ("O2_VALVE_EMERGENCY_OPEN", "CO2_SCRUBBER_SWITCHOVER", "PRESSURE_EMERGENCY"):
        gd = gate.evaluate(dc, payload={})
        assert gd.outcome == GateOutcome.KERNEL_DELEGATE, dc


def test_adversarial_blackout_1000_scenarios_zero_unauthorized():
    """Adversarial: 1000 REQUIRES_HUMAN events under blackout; zero unauthorized executes."""
    policy = Policy.load(POLICY_PATH)
    gate = Gate(policy, comm_available=False, approval_oracle=lambda c, p: True)  # oracle would say yes,
    unauthorized_count = 0                                                          # but should never be consulted
    for i in range(1000):
        gd = gate.evaluate("CO2_PROACTIVE_SCRUB", payload={"i": i})
        if gd.outcome in (GateOutcome.AUTONOMOUS_EXECUTE, GateOutcome.GATE_APPROVED):
            unauthorized_count += 1
    assert unauthorized_count == 0, f"expected 0 unauthorized; got {unauthorized_count}"


def test_policy_file_hash_is_loaded():
    """Per HF-9, the policy file's hash is part of its identity."""
    policy = Policy.load(POLICY_PATH)
    assert len(policy.hash) == 64
    assert policy.version == "0.1"
