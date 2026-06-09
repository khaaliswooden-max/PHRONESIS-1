"""HF-13: Biomedical alert latency.

End-to-end from sensor event timestamp to crew-perceptible alert <= 5 seconds,
INCLUDING chain signing.

Test: 1000 alert events per class. p99 latency under threshold.
"""

import tempfile
import time
from pathlib import Path

from src.aletheia.chain import AletheiaChain
from src.biomedical.alerts import classify, emit_alert, ALERT_CLASSES


def test_alert_latency_p99_under_5_seconds():
    with tempfile.TemporaryDirectory() as tmp:
        chain = AletheiaChain.open_or_create(Path(tmp) / "chain.db", Path(tmp) / "key.pem")
        latencies_by_class = {}
        for cls in ALERT_CLASSES:
            latencies = []
            for i in range(1000):
                t_detect = time.time_ns()
                event = classify({
                    "sensor_id": f"sensor_{i}",
                    "alert_class": cls,
                    "detected_at_ns": t_detect,
                    "payload": {"i": i},
                })
                # crew interface is a no-op fn for v0.1
                timing = emit_alert(event, chain, crew_interface_fn=lambda a: None)
                latencies.append(timing["total_latency_s"])
            latencies_by_class[cls] = latencies
            # p99
            sorted_lat = sorted(latencies)
            p99 = sorted_lat[int(0.99 * len(sorted_lat))]
            assert p99 < 5.0, f"HF-13 fail for {cls}: p99 = {p99:.4f} s, threshold 5.0"
        chain.close()


def test_alert_chain_entry_within_budget():
    """Every alert MUST produce a signed chain entry in the same emit call."""
    with tempfile.TemporaryDirectory() as tmp:
        chain = AletheiaChain.open_or_create(Path(tmp) / "chain.db", Path(tmp) / "key.pem")
        before = sum(1 for _ in chain.replay())
        ev = classify({"sensor_id": "s0", "alert_class": "hypoxia", "detected_at_ns": time.time_ns()})
        emit_alert(ev, chain)
        after = sum(1 for _ in chain.replay())
        assert after - before == 1, "exactly one chain entry per alert"
        # verify the entry is signed correctly
        result = chain.verify_integrity()
        assert result["integrity_ok"]
        chain.close()
