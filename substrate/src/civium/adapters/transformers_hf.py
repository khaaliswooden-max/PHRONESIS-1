"""HuggingFace transformers adapter (sandbox demonstration).

This adapter runs in the v0.2-α development sandbox where the full Mistral-7B
production model exceeds available RAM. The adapter has the same interface as
OllamaMistralAdapter; swapping is a one-line change in the Civium layer
(`adapter = TransformersHFAdapter(...)` instead of `OllamaMistralAdapter(...)`).

Sandbox model: Qwen2.5-0.5B-Instruct (494M params, fits in <1 GB RAM).
This is NOT the production model. The architecture demonstration here is:

  1. Real instruction-tuned LLM produces a classification decision over the
     PLSS state.
  2. Real log-probabilities are computed *per decision-class option* via
     teacher-forcing — each candidate option is scored under the prompt and
     the resulting log-probs form a proper posterior.
  3. Confidence is the softmax-normalized posterior probability of the
     top-scoring option.
  4. Every inference produces the full AIBOM provenance record (model_version,
     model_hash, prompt_hash, logprob_summary).

The 0.5B model is weaker than Mistral-7B at classification, but the
*architectural deliverable* — real log-prob extraction wired through ACI
gating to the substrate — is the v0.2-α exit criterion. Production deployment
swaps the adapter; the substrate code path is unchanged.
"""

from __future__ import annotations

import hashlib
import math
import os
import threading
from typing import Dict, List, Optional

from .base import (
    DECISION_OPTIONS,
    CiviumLLMAdapter,
    InferenceResult,
    compose_prompt,
    hash_prompt,
    select_top_option,
    softmax_to_confidence,
)


class TransformersHFAdapter(CiviumLLMAdapter):
    """HF transformers adapter using a small instruction-tuned model.

    Parameters
    ----------
    model_id : str
        HuggingFace model repository ID (default Qwen/Qwen2.5-0.5B-Instruct).
    device : str
        torch device (default 'cpu').
    use_chat_template : bool
        If True, format the prompt using the tokenizer's chat template.
    """

    _model_cache: Dict[str, tuple] = {}  # (tokenizer, model)
    _cache_lock = threading.Lock()

    def __init__(
        self,
        model_id: str = "Qwen/Qwen2.5-0.5B-Instruct",
        device: str = "cpu",
        use_chat_template: bool = True,
    ):
        self.model_id = model_id
        self.device = device
        self.use_chat_template = use_chat_template
        self._tokenizer = None
        self._model = None
        self._model_hash_cached: Optional[str] = None

    # ---- Lazy model load (shared across adapter instances) ----

    def _ensure_loaded(self):
        if self._model is not None:
            return
        with self._cache_lock:
            if self.model_id in self._model_cache:
                self._tokenizer, self._model = self._model_cache[self.model_id]
                return
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            tok = AutoTokenizer.from_pretrained(self.model_id)
            model = AutoModelForCausalLM.from_pretrained(self.model_id, dtype=torch.float32)
            model.eval()
            self._model_cache[self.model_id] = (tok, model)
            self._tokenizer, self._model = tok, model

    # ---- AIBOM identity ----

    @property
    def model_version(self) -> str:
        return f"hf/{self.model_id}"

    @property
    def model_hash(self) -> str:
        """Returns SHA-256 over the tokenizer vocab and model parameter shapes
        as a stable identifier. Real model weights digest in production would
        be computed by Ollama or hf-xet; this is a v0.2-α surrogate.
        """
        if self._model_hash_cached is not None:
            return self._model_hash_cached
        self._ensure_loaded()
        h = hashlib.sha256()
        h.update(self.model_id.encode())
        h.update(str(self._tokenizer.vocab_size).encode())
        # Include shape signature of named parameters
        for name, p in self._model.named_parameters():
            h.update(name.encode())
            h.update(str(tuple(p.shape)).encode())
        self._model_hash_cached = h.hexdigest()
        return self._model_hash_cached

    # ---- Core inference (teacher-forced per-option log-probs) ----

    def infer(self, state: Dict) -> InferenceResult:
        import torch
        self._ensure_loaded()
        prompt = compose_prompt(state)
        prompt_h = hash_prompt(prompt)

        # 1) Compute teacher-forced log-prob for each DECISION_OPTION.
        # For each option O, we tokenize (prompt + "\n" + O) and compute the
        # sum of log-probs of the option tokens conditional on the prompt.
        # This yields a proper per-option posterior.
        logprobs: Dict[str, float] = {}
        for option in DECISION_OPTIONS:
            lp = self._teacher_force_logprob(prompt, option)
            logprobs[option] = lp

        # 2) Select top option
        selected = select_top_option(logprobs)
        confidence = softmax_to_confidence(logprobs, selected)

        # 3) Free-form rationale via sampled generation (low temp)
        rationale, raw_completion = self._sample_rationale(prompt, selected)

        return InferenceResult(
            decision_class=selected,
            confidence=confidence,
            rationale=rationale,
            logprob_summary=logprobs,
            selected_logprob=logprobs[selected],
            prompt_hash=prompt_h,
            model_version=self.model_version,
            model_hash=self.model_hash,
            raw_completion=raw_completion,
        )

    def _teacher_force_logprob(self, prompt: str, option: str) -> float:
        """Compute log P(option | prompt) by summing per-token log-probs.

        Uses the tokenizer's chat template if available so the model sees the
        instruction-formatted prompt it was trained on.
        """
        import torch
        if self.use_chat_template:
            try:
                full = self._tokenizer.apply_chat_template(
                    [{"role": "user", "content": prompt}],
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except Exception:
                full = prompt
        else:
            full = prompt
        prompt_ids = self._tokenizer(full, return_tensors="pt").input_ids.to(self.device)
        option_ids = self._tokenizer(option, return_tensors="pt", add_special_tokens=False).input_ids.to(self.device)
        combined = torch.cat([prompt_ids, option_ids], dim=1)
        with torch.no_grad():
            outputs = self._model(combined)
        logits = outputs.logits  # (1, T, V)
        # Token at position t is predicted from position t-1's logits
        # So for the i-th option token (at position prompt_len + i), the
        # relevant logits are at position prompt_len + i - 1.
        prompt_len = prompt_ids.shape[1]
        option_len = option_ids.shape[1]
        total_logprob = 0.0
        for i in range(option_len):
            pos = prompt_len + i - 1
            target = combined[0, prompt_len + i].item()
            lp = torch.log_softmax(logits[0, pos], dim=-1)[target].item()
            total_logprob += lp
        return total_logprob

    def _sample_rationale(self, prompt: str, selected: str) -> tuple:
        """Generate a one-sentence rationale by sampling.

        We seed the generation with `prompt + "\n" + selected + "\nRationale:"`
        and read a single line. The free-form rationale is recorded for audit
        and operator readability but is not authoritative — the chain entry's
        machine-readable record is the decision_class + logprob_summary.
        """
        import torch
        if self.use_chat_template:
            try:
                full = self._tokenizer.apply_chat_template(
                    [{"role": "user", "content": prompt}],
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except Exception:
                full = prompt
        else:
            full = prompt
        seed = full + selected + "\nRationale:"
        inputs = self._tokenizer(seed, return_tensors="pt").input_ids.to(self.device)
        with torch.no_grad():
            out = self._model.generate(
                inputs,
                max_new_tokens=40,
                do_sample=False,
                temperature=0.0,
                pad_token_id=self._tokenizer.eos_token_id,
            )
        generated = self._tokenizer.decode(out[0, inputs.shape[1]:], skip_special_tokens=True)
        line1 = generated.splitlines()[0].strip() if generated else ""
        return line1, generated[:300]
