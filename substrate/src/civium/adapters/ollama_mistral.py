"""Ollama + Mistral-7B-Instruct adapter (CANONICAL PRODUCTION PATH).

Honors the MVCI zero-budget constraint: local inference via Ollama, no paid APIs.
This is the adapter the v0.2 production substrate uses on Jetson-class or
laptop-class hardware.

Honest sandbox status: this adapter does NOT run in the v0.2-α development
sandbox (3.9 GB RAM; Mistral-7B-Instruct at Q4 needs ~5 GB). The adapter is
code-complete and dependency-free (uses only `requests` for the Ollama HTTP
API); functional verification is via the integration test that mocks the
Ollama HTTP responses with realistic log-prob distributions. The
TransformersHFAdapter handles sandbox execution with a smaller open model and
the same interface.

Production deployment:
  1. Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
  2. Pull the model: `ollama pull mistral:7b-instruct-q4_K_M`
  3. Start the service: `ollama serve` (or systemd unit)
  4. Substrate connects to http://localhost:11434/api/generate by default
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from typing import Dict, Optional

try:
    import requests  # optional in dev environments
except ImportError:
    requests = None

from .base import (
    DECISION_OPTIONS,
    CiviumLLMAdapter,
    InferenceResult,
    compose_prompt,
    hash_prompt,
    select_top_option,
    softmax_to_confidence,
)


OLLAMA_DEFAULT_URL = "http://localhost:11434"


class OllamaMistralAdapter(CiviumLLMAdapter):
    """Canonical production adapter for Mistral-7B-Instruct via Ollama.

    Parameters
    ----------
    base_url : str
        Ollama HTTP endpoint (default localhost:11434).
    model_name : str
        Ollama model tag (default mistral:7b-instruct-q4_K_M).
    timeout_s : float
        Request timeout. Production should set this conservatively given
        the safety-criticality of the path.
    """

    def __init__(
        self,
        base_url: str = OLLAMA_DEFAULT_URL,
        model_name: str = "mistral:7b-instruct-q4_K_M",
        timeout_s: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout_s = timeout_s
        self._model_hash: Optional[str] = None

    # ---- AIBOM identity ----

    @property
    def model_version(self) -> str:
        return f"ollama/{self.model_name}"

    @property
    def model_hash(self) -> str:
        """In production, Ollama reports the model digest at /api/show. v0.1
        of this adapter caches the digest on first call; subsequent calls
        return cached. If Ollama is unreachable, returns 'unavailable'.
        """
        if self._model_hash is not None:
            return self._model_hash
        if requests is None:
            self._model_hash = "unavailable-requests-not-installed"
            return self._model_hash
        try:
            r = requests.post(
                f"{self.base_url}/api/show",
                json={"model": self.model_name},
                timeout=self.timeout_s,
            )
            if r.status_code == 200:
                # Ollama returns a 'digest' field for the model layers
                data = r.json()
                digest = data.get("digest") or data.get("manifest", {}).get("digest") or ""
                self._model_hash = digest or "unavailable-no-digest"
            else:
                self._model_hash = f"unavailable-status-{r.status_code}"
        except Exception:
            self._model_hash = "unavailable-connection-failed"
        return self._model_hash

    # ---- Core inference ----

    def infer(self, state: Dict) -> InferenceResult:
        if requests is None:
            raise RuntimeError(
                "OllamaMistralAdapter requires the `requests` library. "
                "Install: pip install requests"
            )
        prompt = compose_prompt(state)
        prompt_h = hash_prompt(prompt)

        # Strategy: use Ollama's `generate` endpoint with `options.logprobs` to
        # request token-level log-probs. We then evaluate each DECISION_OPTIONS
        # candidate by computing its sequence log-prob under the prompt.
        # Ollama exposes per-token log-probs when 'options.num_logits' or
        # 'logprobs' is set. The contract below uses the modern Ollama API
        # (>=0.4.x) which supports `logprobs` for sampled tokens.
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,  # deterministic for safety
                "num_predict": 80,
                "logprobs": True,
            },
        }
        r = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.timeout_s,
        )
        r.raise_for_status()
        data = r.json()

        completion = data.get("response", "").strip()
        token_logprobs = data.get("logprobs", [])

        # Parse first non-empty line as the decision label
        first_line = completion.splitlines()[0].strip() if completion else ""
        # Tolerant label extraction
        selected = self._extract_label(first_line, completion)

        # Construct per-option log-probs from the token stream. If Ollama
        # provided the relevant token log-probs, use them; otherwise synthesize
        # a delta posterior (selected = 0.0, others = -inf) so the chain entry
        # still has a structured logprob_summary field.
        logprobs = self._extract_option_logprobs(token_logprobs, completion)
        if selected not in logprobs:
            logprobs[selected] = 0.0  # selected with no extracted log-prob
        # Ensure every DECISION_OPTION has an entry
        for opt in DECISION_OPTIONS:
            logprobs.setdefault(opt, -50.0)

        confidence = softmax_to_confidence(logprobs, selected)
        rationale = self._extract_rationale(completion)

        return InferenceResult(
            decision_class=selected,
            confidence=confidence,
            rationale=rationale,
            logprob_summary=logprobs,
            selected_logprob=logprobs[selected],
            prompt_hash=prompt_h,
            model_version=self.model_version,
            model_hash=self.model_hash,
            raw_completion=completion,
        )

    # ---- Parsing helpers ----

    @staticmethod
    def _extract_label(first_line: str, completion: str) -> str:
        """Look for any DECISION_OPTION in the first line; fall back to NOMINAL."""
        normalized = first_line.upper().strip().rstrip(":.,")
        if normalized in DECISION_OPTIONS:
            return normalized
        # Search the full completion for the first option mentioned
        for opt in DECISION_OPTIONS:
            if re.search(rf"\b{opt}\b", completion):
                return opt
        # Last-resort default — process_event S-1 fallback will catch any
        # adversarial deviation
        return "NOMINAL_NO_ACTION"

    @staticmethod
    def _extract_rationale(completion: str) -> str:
        lines = [l.strip() for l in completion.splitlines() if l.strip()]
        return lines[1] if len(lines) >= 2 else lines[0] if lines else ""

    @staticmethod
    def _extract_option_logprobs(token_logprobs, completion: str) -> Dict[str, float]:
        """Reconstruct per-option log-probs from Ollama's token log-prob stream.

        Ollama returns a list of (token, logprob, top_alternatives) tuples for
        the generated sequence. To get a per-option posterior, we re-prompt
        each option as a teacher-forced completion. In v0.2-α we use a simpler
        heuristic: if the top token at the decision position has alternatives
        matching DECISION_OPTIONS labels, we use those log-probs directly.

        v0.2-β refinement: implement proper teacher-forcing per option for
        well-calibrated posteriors. This requires a second-pass evaluator
        endpoint and is deferred to v0.2-β.
        """
        result: Dict[str, float] = {}
        if not token_logprobs:
            return result
        # Walk tokens looking for any whose surface form matches an option
        for tok in token_logprobs:
            surface = tok.get("token", "") if isinstance(tok, dict) else ""
            lp = tok.get("logprob", -50.0) if isinstance(tok, dict) else -50.0
            for opt in DECISION_OPTIONS:
                if opt.startswith(surface.strip().upper()) and len(surface.strip()) >= 4:
                    if opt not in result or lp > result[opt]:
                        result[opt] = lp
            # Also check top alternatives at this position
            alternatives = tok.get("top_logprobs", []) if isinstance(tok, dict) else []
            for alt in alternatives:
                alt_tok = alt.get("token", "").strip().upper() if isinstance(alt, dict) else ""
                alt_lp = alt.get("logprob", -50.0) if isinstance(alt, dict) else -50.0
                for opt in DECISION_OPTIONS:
                    if opt.startswith(alt_tok) and len(alt_tok) >= 4:
                        if opt not in result or alt_lp > result[opt]:
                            result[opt] = alt_lp
        return result
