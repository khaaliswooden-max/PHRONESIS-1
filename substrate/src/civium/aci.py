"""Adaptive Conformal Inference for confidence band management.

Drift clause implementation: static conformal coverage collapses under
distribution shift; ACI adapts its quantile online to maintain target coverage.

Reference: Gibbs & Candes (2021), Adaptive Conformal Inference Under Distribution Shift.

v0.1: scalar online ACI with miscoverage-rate-driven quantile adaptation.
"""

import numpy as np
from dataclasses import dataclass
from typing import List


@dataclass
class ConformalResult:
    target_coverage: float
    observed_coverage: float
    n_predictions: int
    final_quantile: float


class StaticConformal:
    """Static (non-adaptive) conformal predictor — for comparison baseline.

    Computes residual quantile once on a calibration window, holds fixed.
    This is the system that collapses under drift; we use it as the failure baseline.
    """

    def __init__(self, target_coverage: float = 0.9, calibration_size: int = 200):
        self.target_coverage = target_coverage
        self.calibration_size = calibration_size
        self.quantile = None
        self.predictions = []
        self.actuals = []

    def fit(self, predictions: List[float], actuals: List[float]):
        residuals = np.abs(np.array(predictions) - np.array(actuals))
        self.quantile = float(np.quantile(residuals, self.target_coverage))

    def interval(self, prediction: float) -> tuple:
        assert self.quantile is not None, "must fit first"
        return (prediction - self.quantile, prediction + self.quantile)

    def evaluate(self, predictions: List[float], actuals: List[float]) -> ConformalResult:
        covered = 0
        for p, a in zip(predictions, actuals):
            lo, hi = self.interval(p)
            if lo <= a <= hi:
                covered += 1
        return ConformalResult(
            target_coverage=self.target_coverage,
            observed_coverage=covered / len(predictions),
            n_predictions=len(predictions),
            final_quantile=self.quantile,
        )


class ACI:
    """Adaptive Conformal Inference (Gibbs & Candes 2021).

    Maintains an effective miscoverage level alpha_t that is adapted based on
    realized coverage. When recent intervals fail to cover, alpha_t shrinks
    (interval widens). When they over-cover, alpha_t grows (interval narrows).
    """

    def __init__(self, target_coverage: float = 0.9, gamma: float = 0.01):
        self.target_alpha = 1.0 - target_coverage  # nominal miscoverage
        self.alpha_t = self.target_alpha
        self.gamma = gamma  # learning rate
        self.residuals = []  # rolling residual store
        self.window_size = 500

    def step(self, prediction: float, actual: float, base_quantile: float) -> dict:
        """Process one (prediction, actual) pair.

        Phase 6 S-7 hardening: NaN/Inf prediction or actual produces a NAN_REJECT
        outcome; ACI does not corrupt its residual buffer and returns a sentinel
        result so the gate layer can route the decision to SAFE_PASSIVE.
        """
        if not (np.isfinite(prediction) and np.isfinite(actual)):
            return {
                "interval": (float("nan"), float("nan")),
                "covered": False,
                "quantile": float("nan"),
                "alpha_t": self.alpha_t,
                "nan_reject": True,
            }
        # Compute interval at current alpha_t
        q_level = 1.0 - self.alpha_t
        if len(self.residuals) >= 20:
            q = float(np.quantile(self.residuals, np.clip(q_level, 0.01, 0.99)))
        else:
            q = base_quantile
        lo, hi = prediction - q, prediction + q
        covered = 1 if lo <= actual <= hi else 0
        miscov = 1 - covered
        err = self.target_alpha - miscov
        self.alpha_t = float(np.clip(self.alpha_t + self.gamma * err, 1e-3, 1 - 1e-3))
        self.residuals.append(abs(prediction - actual))
        if len(self.residuals) > self.window_size:
            self.residuals.pop(0)
        return {
            "interval": (lo, hi),
            "covered": bool(covered),
            "quantile": q,
            "alpha_t": self.alpha_t,
            "nan_reject": False,
        }

    def evaluate_stream(self, predictions: List[float], actuals: List[float], base_quantile: float) -> ConformalResult:
        covered = 0
        last_q = base_quantile
        valid_count = 0
        for p, a in zip(predictions, actuals):
            r = self.step(p, a, base_quantile)
            if r.get("nan_reject"):
                continue  # NaN rejected; do not count toward coverage stats
            valid_count += 1
            last_q = r["quantile"]
            if r["covered"]:
                covered += 1
        denom = max(1, valid_count)
        return ConformalResult(
            target_coverage=1 - self.target_alpha,
            observed_coverage=covered / denom,
            n_predictions=valid_count,
            final_quantile=last_q,
        )
