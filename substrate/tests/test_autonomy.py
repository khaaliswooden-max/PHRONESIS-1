"""HF-12: Effective autonomy ratio on AUTONOMOUS_ELIGIBLE decisions.

The system must resolve >= 70% of AUTONOMOUS_ELIGIBLE-classified decisions
autonomously (not safe-passive fallback), with mission task continuity.

v0.1 test: 10,000 stratified scenarios spanning nominal, edge, and adversarial
operational conditions. Per-scenario policy classification is computed by the
v0.1 policy file; autonomous resolution rate is measured on the AUTONOMOUS_ELIGIBLE
subset.

The Goodhart counter: a system passing HF-9 by collapsing all decisions to
safe-passive would fail this floor.
"""

import random
import tempfile
from pathlib import Path

from src.aletheia.chain import AletheiaChain
from src.mvci.gate import Gate, GateOutcome, Policy
from src.isolation.bus import SafetyBus
from src.runner.simulate import process_event


POLICY_PATH = Path(__file__).resolve().parents[1] / "policy" / "isps_policy_v0_1.json"


def generate_stratified_scenarios(n: int = 10000, seed: int = 42) -> list:
    """Stratified scenarios across nominal / edge / adversarial.

    Returns list of state dicts. Each is a candidate input to process_event.
    """
    rng = random.Random(seed)
    scenarios = []
    # 70% nominal, 20% edge, 10% adversarial
    for _ in range(int(0.7 * n)):
        scenarios.append({
            "o2_partial_pressure_kpa": rng.uniform(20.0, 22.5),
            "co2_partial_pressure_kpa": rng.uniform(0.2, 0.6),
            "suit_pressure_psi": rng.uniform(4.8, 5.2),
            "suit_temp_c": rng.uniform(18.0, 26.0),
            "battery_percent": rng.uniform(50.0, 100.0),
            "comm_link_quality": rng.uniform(0.7, 1.0),
        })
    for _ in range(int(0.2 * n)):
        # edge — elevated parameters but within safety bounds
        scenarios.append({
            "o2_partial_pressure_kpa": rng.uniform(17.0, 24.0),
            "co2_partial_pressure_kpa": rng.uniform(0.5, 1.2),
            "suit_pressure_psi": rng.uniform(4.5, 5.5),
            "suit_temp_c": rng.uniform(25.0, 32.0),
            "battery_percent": rng.uniform(15.0, 60.0),
            "comm_link_quality": rng.uniform(0.3, 0.8),
        })
    for _ in range(int(0.1 * n)):
        # adversarial — outside bands, may trigger safety-critical
        scenarios.append({
            "o2_partial_pressure_kpa": rng.uniform(13.0, 28.0),
            "co2_partial_pressure_kpa": rng.uniform(0.0, 2.0),
            "suit_pressure_psi": rng.uniform(3.0, 6.0),
            "suit_temp_c": rng.uniform(-10.0, 40.0),
            "battery_percent": rng.uniform(0.0, 100.0),
            "comm_link_quality": rng.uniform(0.0, 1.0),
        })
    rng.shuffle(scenarios)
    return scenarios


def test_autonomous_resolution_rate_meets_threshold():
    """HF-12 verification harness.

    Run 10k scenarios through the full pipeline. Count per-classification outcomes.
    Compute autonomous-resolution rate on AUTONOMOUS_ELIGIBLE subset.
    Threshold: >= 70%.
    """
    scenarios = generate_stratified_scenarios(n=10000, seed=42)
    policy = Policy.load(POLICY_PATH)

    with tempfile.TemporaryDirectory() as tmp:
        chain = AletheiaChain.open_or_create(Path(tmp) / "chain.db", Path(tmp) / "key.pem")
        gate = Gate(policy, comm_available=True, approval_oracle=lambda c, p: True)
        bus = SafetyBus()

        counts_by_class = {}
        autonomous_resolved = {}
        for state in scenarios:
            record = process_event(state, gate, chain, bus, comm_available=True)
            cls = record["gate_decision"]["classification"]
            outcome_executed = record["executed"]
            counts_by_class[cls] = counts_by_class.get(cls, 0) + 1
            # AUTONOMOUS_ELIGIBLE scenarios: resolved autonomously means executed == 'autonomous'
            if cls == "AUTONOMOUS_ELIGIBLE":
                if outcome_executed == "autonomous":
                    autonomous_resolved[cls] = autonomous_resolved.get(cls, 0) + 1

        eligible_count = counts_by_class.get("AUTONOMOUS_ELIGIBLE", 0)
        resolved_count = autonomous_resolved.get("AUTONOMOUS_ELIGIBLE", 0)
        assert eligible_count > 0, "no AUTONOMOUS_ELIGIBLE scenarios — scenario generator may need broader coverage"
        ratio = resolved_count / eligible_count
        # Write a small report alongside the test (for inclusion in BENCHMARK_RESULTS)
        Path(tmp).joinpath("hf12_report.txt").write_text(
            f"eligible={eligible_count} resolved={resolved_count} ratio={ratio:.4f}\n"
            f"counts_by_class={counts_by_class}\n"
        )
        assert ratio >= 0.70, f"HF-12 fail: autonomous resolution rate = {ratio:.4f}, threshold 0.70"
        chain.close()
