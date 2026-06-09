"""HF-12 re-measurement with LLM-driven inference.

The v0.1.1 measurement of HF-12 was 8770/8770 = 1.000 because the rule-based
stub never produced low-confidence outputs. v0.2-α replaces the nuanced-band
inference with an LLM adapter that produces real, variable log-probabilities.

This script runs a stratified set of nuanced-band PLSS states through the
LLM-driven path and reports the confidence distribution. We then evaluate
HF-12 autonomy rate at several candidate AUTONOMY_CONFIDENCE_FLOOR values to
demonstrate that the architecture produces meaningful confidence-driven gate
routing.

Important caveat: the sandbox model is Qwen2.5-0.5B-Instruct (494M params),
which is two orders of magnitude smaller than the production target Mistral-
7B-Instruct (7B params). The 0.5B model's calibration is weaker than Mistral-7B.
The HF-12 number produced here is an ARCHITECTURAL demonstration that
confidence-driven routing works, NOT a validated benchmark score for the
production substrate. Validated HF-12 requires Mistral-7B + calibration audit
+ scenario-library expansion; this is documented as a v0.2-β residual.
"""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.civium.adapters.transformers_hf import TransformersHFAdapter
from src.civium.inference import recommend_with_llm


# Stratified nuanced-band scenarios. NONE trigger hard safety floors;
# all are AUTONOMOUS_ELIGIBLE candidates that exercise the LLM's confidence.
SCENARIOS = [
    # Nominal (1)
    {"o2_partial_pressure_kpa": 21.3, "co2_partial_pressure_kpa": 0.4, "suit_pressure_psi": 5.0,
     "suit_temp_c": 22.0, "battery_percent": 80.0, "comm_link_quality": 0.9},

    # Elevated thermal (1)
    {"o2_partial_pressure_kpa": 20.5, "co2_partial_pressure_kpa": 0.5, "suit_pressure_psi": 5.0,
     "suit_temp_c": 34.5, "battery_percent": 60.0, "comm_link_quality": 0.85},

    # Mid-band CO2 (1)
    {"o2_partial_pressure_kpa": 20.6, "co2_partial_pressure_kpa": 1.2, "suit_pressure_psi": 5.0,
     "suit_temp_c": 23.0, "battery_percent": 68.0, "comm_link_quality": 0.85},

    # Low battery (1)
    {"o2_partial_pressure_kpa": 21.0, "co2_partial_pressure_kpa": 0.4, "suit_pressure_psi": 5.0,
     "suit_temp_c": 22.0, "battery_percent": 18.0, "comm_link_quality": 0.85},

    # Multi-axis off-nominal but no emergency (2)
    {"o2_partial_pressure_kpa": 19.0, "co2_partial_pressure_kpa": 0.8, "suit_pressure_psi": 4.7,
     "suit_temp_c": 28.0, "battery_percent": 45.0, "comm_link_quality": 0.7},
    {"o2_partial_pressure_kpa": 18.5, "co2_partial_pressure_kpa": 1.0, "suit_pressure_psi": 4.6,
     "suit_temp_c": 30.0, "battery_percent": 35.0, "comm_link_quality": 0.65},
]


def main():
    adapter = TransformersHFAdapter()
    print(f"Loading adapter ({adapter.model_id})...", flush=True)
    adapter._ensure_loaded()
    print(f"Loaded; model_hash={adapter.model_hash[:16]}...", flush=True)

    # Checkpoint to JSONL — each scenario result written as it completes,
    # so an interrupt does not lose work.
    checkpoint = ROOT / "v02_alpha" / "hf12_remeasure_records.jsonl"
    checkpoint.parent.mkdir(exist_ok=True)
    # Resume: skip scenarios already in checkpoint
    done_indices = set()
    if checkpoint.exists():
        for line in checkpoint.read_text().splitlines():
            try:
                done_indices.add(json.loads(line)["scenario"])
            except Exception:
                pass
        print(f"Resuming: {len(done_indices)} scenarios already complete", flush=True)

    records = []
    if checkpoint.exists():
        for line in checkpoint.read_text().splitlines():
            try:
                records.append(json.loads(line))
            except Exception:
                pass

    t_total_start = time.time()
    for i, state in enumerate(SCENARIOS):
        if i in done_indices:
            continue
        t0 = time.time()
        recs = recommend_with_llm(state, adapter)
        dt = time.time() - t0
        rec = recs[0]
        entry = {
            "scenario": i,
            "state": state,
            "decision_class": rec.decision_class,
            "confidence": rec.confidence,
            "selected_logprob": rec.selected_logprob,
            "source": rec.source,
            "latency_s": dt,
        }
        records.append(entry)
        # Append checkpoint immediately
        with open(checkpoint, "a") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"  [{i+1:2d}/{len(SCENARIOS)}] {rec.decision_class:30s} conf={rec.confidence:.3f} ({dt:.1f}s)", flush=True)
    t_total = time.time() - t_total_start

    if not records:
        print("No records produced.", flush=True)
        return

    # Confidence distribution
    confs = [r["confidence"] for r in records]
    latencies = [r["latency_s"] for r in records]

    # HF-12 autonomy rate at candidate confidence floors
    thresholds = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80]
    hf12_table = []
    for thr in thresholds:
        autonomous = sum(1 for r in records if r["confidence"] >= thr)
        rate = autonomous / len(records)
        hf12_table.append({"threshold": thr, "autonomous": autonomous, "total": len(records), "rate": rate})

    summary = {
        "n_scenarios": len(records),
        "session_latency_s": t_total,
        "per_inference_latency_s": {
            "min": min(latencies), "max": max(latencies),
            "mean": sum(latencies) / len(latencies),
            "p50": sorted(latencies)[len(latencies) // 2],
        },
        "confidence_distribution": {
            "min": min(confs), "max": max(confs),
            "mean": sum(confs) / len(confs),
            "p50": sorted(confs)[len(confs) // 2],
            "unique_values_3dp": len({round(c, 3) for c in confs}),
        },
        "decision_class_counts": {},
        "hf12_at_thresholds": hf12_table,
        "model_id": "hf/Qwen/Qwen2.5-0.5B-Instruct",
        "records": records,
    }
    for r in records:
        summary["decision_class_counts"][r["decision_class"]] = summary["decision_class_counts"].get(r["decision_class"], 0) + 1

    out = ROOT / "v02_alpha" / "hf12_remeasure_results.json"
    out.write_text(json.dumps(summary, indent=2))

    print(f"\n=== HF-12 re-measurement complete ===", flush=True)
    print(f"Scenarios: {len(records)}; session latency: {t_total:.1f}s", flush=True)
    print(f"Per-inference latency: mean {summary['per_inference_latency_s']['mean']:.2f}s", flush=True)
    print(f"Confidence range: {min(confs):.3f} - {max(confs):.3f}; unique: {summary['confidence_distribution']['unique_values_3dp']}/{len(confs)}", flush=True)
    print(f"Decision class distribution: {summary['decision_class_counts']}", flush=True)
    print(f"HF-12 autonomy rate at thresholds:", flush=True)
    for row in hf12_table:
        print(f"  thr={row['threshold']:.2f}: {row['autonomous']:2d}/{row['total']} = {row['rate']:.3f}", flush=True)
    print(f"Results: {out}", flush=True)


if __name__ == "__main__":
    main()
