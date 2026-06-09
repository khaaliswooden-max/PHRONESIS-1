"""LLM inference adapter abstraction for Civium.

v0.2 substrate replaces the v0.1.1 rule-based inference stub with real LLM
inference. Two adapter implementations are shipped:

  - OllamaMistralAdapter: canonical production adapter; targets Ollama running
    Mistral-7B-Instruct locally. Honors the MVCI zero-budget constraint (no
    paid APIs). Documented in the v0.2 deployment manifest.
  - TransformersHFAdapter: sandbox demonstration adapter using a small
    instruction-tuned model via the HuggingFace transformers library. Same
    interface as the Ollama adapter; used for development and CI when a full
    7B model exceeds the available RAM/compute budget.

Both adapters return an InferenceResult containing:
  - decision_class: one of the policy-known classes
  - confidence: posterior probability (exp of selected class log-prob)
  - rationale: short natural-language explanation from the model
  - logprob_summary: dict with per-option log-probs and the selected option
    (this is the AIBOM-mandated provenance field for OMB M-25-22 Annex C)
  - prompt_hash: SHA-256 of the prompt text actually sent to the model
  - model_version, model_hash: AIBOM identifiers

The contract is deliberately narrow so the adapter is replaceable. The Civium
layer never depends on the backend.
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# Decision-class option vocabulary. The LLM is constrained to these labels;
# anything else triggers the S-1 unknown-class fallback in process_event.
DECISION_OPTIONS: List[str] = [
    "NOMINAL_NO_ACTION",
    "THERMAL_ADJUST_NOMINAL",
    "POWER_MGMT_NOMINAL",
    "CO2_PROACTIVE_SCRUB",
    "O2_VALVE_EMERGENCY_OPEN",
    "CO2_SCRUBBER_SWITCHOVER",
    "PRESSURE_EMERGENCY",
    "SENSOR_FAULT_SUSPECTED",
]


@dataclass
class InferenceResult:
    decision_class: str
    confidence: float
    rationale: str
    logprob_summary: Dict[str, float]
    selected_logprob: float
    prompt_hash: str
    model_version: str
    model_hash: str
    raw_completion: Optional[str] = None

    def to_chain_payload(self) -> Dict:
        """Subset of fields recorded on the INFERENCE_RECOMMENDATION chain entry."""
        return {
            "decision_class": self.decision_class,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "logprob_summary": self.logprob_summary,
            "selected_logprob": self.selected_logprob,
            "prompt_hash": self.prompt_hash,
            "model_version": self.model_version,
            "model_hash": self.model_hash,
        }


PLSS_PROMPT_TEMPLATE = """You are the inference layer of a spacesuit life-support decision substrate.

Given the current PLSS (Portable Life-Support System) telemetry, classify the appropriate response into ONE of these decision classes:

- NOMINAL_NO_ACTION: state within nominal envelope; no intervention required
- THERMAL_ADJUST_NOMINAL: elevated temperature within autonomous-adjust band
- POWER_MGMT_NOMINAL: low battery; standard load-shedding within autonomous envelope
- CO2_PROACTIVE_SCRUB: elevated CO2, not yet critical; preserve crew agency
- O2_VALVE_EMERGENCY_OPEN: O2 below hypoxia threshold; safety-critical
- CO2_SCRUBBER_SWITCHOVER: CO2 above hypercapnia threshold; safety-critical
- PRESSURE_EMERGENCY: suit pressure critical; safety-critical
- SENSOR_FAULT_SUSPECTED: telemetry reads physically impossible; suspect sensor failure

Telemetry:
{state_json}

Respond with the single decision-class label only (one of the eight above), then on a new line a one-sentence rationale.

Decision:"""


def compose_prompt(state: Dict) -> str:
    return PLSS_PROMPT_TEMPLATE.format(state_json=json.dumps(state, indent=2, sort_keys=True))


def hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode()).hexdigest()


class CiviumLLMAdapter(ABC):
    """Abstract base for all LLM inference backends."""

    @property
    @abstractmethod
    def model_version(self) -> str: ...

    @property
    @abstractmethod
    def model_hash(self) -> str: ...

    @abstractmethod
    def infer(self, state: Dict) -> InferenceResult: ...


# =========================================================================
# Helpers shared by all adapters
# =========================================================================

def softmax_to_confidence(logprobs: Dict[str, float], selected: str) -> float:
    """Normalize per-option log-probs into a posterior over the option set."""
    import math
    if selected not in logprobs:
        return 0.0
    max_lp = max(logprobs.values())
    exps = {k: math.exp(v - max_lp) for k, v in logprobs.items()}
    total = sum(exps.values())
    if total <= 0:
        return 0.0
    return exps[selected] / total


def select_top_option(logprobs: Dict[str, float]) -> str:
    """Return the option with the highest log-probability."""
    if not logprobs:
        raise ValueError("empty logprobs dict")
    return max(logprobs.items(), key=lambda kv: kv[1])[0]
