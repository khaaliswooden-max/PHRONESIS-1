"""Non-stationarity clause: static CI collapses, ACI holds under 3x drift.

This reproduces the Aletheia DAC headline result on synthetic data: a static
conformal predictor fitted on calibration data fails when the test-time
distribution shifts; ACI adapts and maintains target coverage.

Pass: ACI coverage >= 0.85 at 3x shift on at least one named distribution.
v0.1 evaluates the metabolic-rate-analog distribution (a scalar regression
proxy); v0.2+ extend to the other four named distributions.
"""

import numpy as np

from src.civium.aci import StaticConformal, ACI


def synthetic_stream(n: int, drift_factor: float, seed: int = 0):
    """Generate (prediction, actual) pairs where the actual's noise scale grows by drift_factor.

    Predictor knows the nominal mean but not the drift. Actuals = mean + noise * scale.
    """
    rng = np.random.default_rng(seed)
    mean = 100.0
    nominal_sigma = 5.0
    preds = []
    actuals = []
    for i in range(n):
        # Drift ramps linearly across the stream
        progress = i / max(1, n - 1)
        sigma = nominal_sigma * (1.0 + (drift_factor - 1.0) * progress)
        preds.append(mean)
        actuals.append(mean + rng.normal(0, sigma))
    return preds, actuals


def test_static_ci_collapses_under_3x_drift():
    """Static CI fitted on calibration data fails when test distribution drifts 3x."""
    # Calibration: nominal data
    cal_preds, cal_actuals = synthetic_stream(n=500, drift_factor=1.0, seed=42)
    static = StaticConformal(target_coverage=0.9)
    static.fit(cal_preds, cal_actuals)
    # Test: 3x drift
    test_preds, test_actuals = synthetic_stream(n=2000, drift_factor=3.0, seed=99)
    result = static.evaluate(test_preds, test_actuals)
    # Under 3x drift, static coverage should collapse well below the 0.9 target
    # Allow some slack — must be clearly below 0.75 to demonstrate the failure
    assert result.observed_coverage < 0.75, (
        f"static CI should collapse; got coverage {result.observed_coverage:.3f}"
    )


def test_aci_holds_above_0_85_under_3x_drift():
    """ACI's online adaptation maintains coverage >= 0.85 at 3x drift."""
    aci = ACI(target_coverage=0.9, gamma=0.05)
    # Warm-start ACI with the same calibration data (informs base_quantile)
    cal_preds, cal_actuals = synthetic_stream(n=500, drift_factor=1.0, seed=42)
    base_q = float(np.quantile(np.abs(np.array(cal_preds) - np.array(cal_actuals)), 0.9))
    # Test: 3x drift stream
    test_preds, test_actuals = synthetic_stream(n=2000, drift_factor=3.0, seed=99)
    result = aci.evaluate_stream(test_preds, test_actuals, base_quantile=base_q)
    assert result.observed_coverage >= 0.85, (
        f"ACI should hold >= 0.85 under 3x drift; got {result.observed_coverage:.3f}"
    )


def test_aci_recovers_under_1x_2x_3x_progression():
    """Progressive drift: ACI should maintain near-target coverage across all levels."""
    base_q = 8.0  # initial conservative quantile
    for drift in (1.0, 2.0, 3.0):
        aci = ACI(target_coverage=0.9, gamma=0.05)
        preds, actuals = synthetic_stream(n=2000, drift_factor=drift, seed=int(drift * 100))
        result = aci.evaluate_stream(preds, actuals, base_quantile=base_q)
        assert result.observed_coverage >= 0.80, (
            f"ACI failed at drift={drift}; coverage={result.observed_coverage:.3f}"
        )
