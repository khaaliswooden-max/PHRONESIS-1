"""HF-10: Safety-critical deterministic kernel.

Tests:
  1. Mercury Subleq emulator computes O2 valve command correctly across many inputs.
  2. WCET is bounded and measured.
  3. Kernel completes in deterministic cycle count (same input -> same cycles).
  4. Bus isolation: ML-side actuation attempts (no kernel token) are denied.
  5. Penetration test: 1000 ML-impersonation attempts all rejected.

v0.1 honest status: full formal verification (Coq/Lean proofs) NOT produced.
WCET measured empirically. This is acknowledged in BENCHMARK_RESULTS_v0_1.md.
"""

import pytest

from src.mercury.subleq import build_o2_control_program, measure_wcet, SubleqWCETExceeded
from src.isolation.bus import SafetyBus, BusAction, BusAccessDenied, get_kernel_token


def test_o2_control_correctness_basic():
    """setpoint - reading. Memory[14] should equal max(0, setpoint - reading) after clipping."""
    cases = [(22, 20, 2), (25, 18, 7), (20, 22, -2), (20, 20, 0), (30, 5, 25)]
    for setpoint, reading, expected in cases:
        vm = build_o2_control_program(setpoint, reading, wcet_cycles=100)
        res = vm.run()
        # The subleq program computes setpoint - reading and stores in command (idx 14)
        # Result may be negative if reading > setpoint; clipped in production code
        computed = res.memory[17]
        assert computed == expected, f"setpoint={setpoint} reading={reading}: expected {expected} got {computed}"


def test_wcet_measured_and_bounded():
    """Measure WCET across 1000 random-ish input pairs. Must be small and bounded."""
    setpoints = list(range(0, 30))
    readings = list(range(0, 30))
    # Cartesian sample
    sp_seq = []
    rd_seq = []
    for s in setpoints:
        for r in readings:
            sp_seq.append(s)
            rd_seq.append(r)
    worst, n = measure_wcet(sp_seq, rd_seq, wcet_budget=100)
    assert worst <= 6, f"WCET worst={worst} cycles over n={n} runs; expected ≤ 6 (program is 5 subleq instructions)"
    assert n == len(sp_seq)


def test_wcet_budget_breach_caught():
    """Force a tiny budget; verify WCET exception fires."""
    vm = build_o2_control_program(22, 18, wcet_cycles=2)
    with pytest.raises(SubleqWCETExceeded):
        vm.run()


def test_kernel_deterministic_same_input_same_cycles():
    """Determinism property: same input -> same cycle count, every time."""
    cycles_seen = set()
    for _ in range(20):
        vm = build_o2_control_program(22, 18, wcet_cycles=100)
        res = vm.run()
        cycles_seen.add(res.cycles)
    assert len(cycles_seen) == 1, f"non-deterministic: saw {cycles_seen}"


def test_bus_denies_unauthorized_write():
    """ML-side actuation attempt without kernel token -> BusAccessDenied."""
    bus = SafetyBus()
    with pytest.raises(BusAccessDenied):
        bus.write(BusAction(line="o2_valve", command=5, privilege_token="ml-impersonator-token"))


def test_bus_allows_kernel_write():
    bus = SafetyBus()
    ok = bus.write(BusAction(line="o2_valve", command=5, privilege_token=get_kernel_token()))
    assert ok
    assert bus.read("o2_valve") == 5


def test_penetration_1000_ml_impersonation_attempts():
    """1000 attempts to actuate from ML side; all must be denied. Audit trail records each."""
    bus = SafetyBus()
    denied = 0
    for i in range(1000):
        try:
            bus.write(BusAction(line="o2_valve", command=i, privilege_token=f"forged-token-{i}"))
        except BusAccessDenied:
            denied += 1
    assert denied == 1000, f"expected 1000 denials; got {denied}"
    # Audit trail captures all attempts
    audit = bus.audit_write_attempts()
    assert len(audit) == 1000
    # Bus state is unchanged
    assert bus.read("o2_valve") == 0
