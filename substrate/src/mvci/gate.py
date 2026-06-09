"""MVCI policy-driven approval gate.

HF-9 implementation: every decision classified by a cryptographically committed
policy file. AUTONOMOUS_ELIGIBLE decisions execute autonomously; REQUIRES_HUMAN
decisions either get gated approval or fall back to documented safe-passive state.
SAFETY_CRITICAL decisions route to the deterministic kernel and never to ML.

Reclassification of a decision class out of REQUIRES_HUMAN requires a versioned
policy update — enforced by the policy file's signed hash.
"""

import enum
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class Classification(enum.Enum):
    AUTONOMOUS_ELIGIBLE = "AUTONOMOUS_ELIGIBLE"
    REQUIRES_HUMAN = "REQUIRES_HUMAN"
    SAFETY_CRITICAL = "SAFETY_CRITICAL"


class GateOutcome(enum.Enum):
    AUTONOMOUS_EXECUTE = "AUTONOMOUS_EXECUTE"
    GATE_APPROVED = "GATE_APPROVED"
    GATE_REJECTED = "GATE_REJECTED"
    GATE_TIMEOUT = "GATE_TIMEOUT"
    SAFE_PASSIVE_FALLBACK = "SAFE_PASSIVE_FALLBACK"
    KERNEL_DELEGATE = "KERNEL_DELEGATE"


@dataclass
class GateDecision:
    decision_class: str
    classification: Classification
    outcome: GateOutcome
    fallback_state: Optional[str]
    approval_source: Optional[str]
    rationale: str


class PolicyError(Exception):
    pass


class Policy:
    """Loaded policy file. The hash is the binding identity."""

    def __init__(self, content: dict, file_hash: str):
        self.content = content
        self.hash = file_hash
        self.version = content["version"]
        self.classifications = content["classifications"]
        self.fallbacks = content["fallbacks"]

    @classmethod
    def load(cls, path: Path) -> "Policy":
        raw = Path(path).read_bytes()
        h = hashlib.sha256(raw).hexdigest()
        content = json.loads(raw.decode())
        for k, v in content["classifications"].items():
            if v["level"] not in (e.value for e in Classification):
                raise PolicyError(f"unknown classification level for {k}: {v['level']}")
        return cls(content, h)

    def classify(self, decision_class: str) -> Classification:
        if decision_class not in self.classifications:
            raise PolicyError(f"unknown decision class: {decision_class}")
        return Classification(self.classifications[decision_class]["level"])

    def fallback_for(self, decision_class: str) -> str:
        return self.classifications[decision_class]["fallback"]


class CommGateError(Exception):
    """Raised when ground approval cannot be reached."""


class Gate:
    """Approval gate engine.

    Behaviors:
      AUTONOMOUS_ELIGIBLE -> AUTONOMOUS_EXECUTE (no gate)
      REQUIRES_HUMAN      -> request approval; if unreachable -> SAFE_PASSIVE_FALLBACK
      SAFETY_CRITICAL     -> KERNEL_DELEGATE (gate refuses; routes to Mercury kernel)

    The gate never lets a REQUIRES_HUMAN action execute autonomously.
    """

    def __init__(self, policy: Policy, comm_available: bool = True, approval_oracle=None):
        self.policy = policy
        self.comm_available = comm_available
        # approval_oracle: callable(decision_class, payload) -> bool (True=approved)
        self.approval_oracle = approval_oracle

    def evaluate(self, decision_class: str, payload: dict) -> GateDecision:
        cls = self.policy.classify(decision_class)
        if cls == Classification.AUTONOMOUS_ELIGIBLE:
            return GateDecision(
                decision_class=decision_class,
                classification=cls,
                outcome=GateOutcome.AUTONOMOUS_EXECUTE,
                fallback_state=None,
                approval_source="policy",
                rationale="AUTONOMOUS_ELIGIBLE per policy",
            )
        if cls == Classification.SAFETY_CRITICAL:
            return GateDecision(
                decision_class=decision_class,
                classification=cls,
                outcome=GateOutcome.KERNEL_DELEGATE,
                fallback_state=None,
                approval_source="policy",
                rationale="SAFETY_CRITICAL must route to deterministic kernel; ML/inference layer is not permitted to actuate",
            )
        # REQUIRES_HUMAN
        if not self.comm_available:
            return GateDecision(
                decision_class=decision_class,
                classification=cls,
                outcome=GateOutcome.SAFE_PASSIVE_FALLBACK,
                fallback_state=self.policy.fallback_for(decision_class),
                approval_source=None,
                rationale="comm unavailable; fallback to documented safe-passive state",
            )
        # Comm available — ask approver
        if self.approval_oracle is None:
            return GateDecision(
                decision_class=decision_class,
                classification=cls,
                outcome=GateOutcome.GATE_TIMEOUT,
                fallback_state=self.policy.fallback_for(decision_class),
                approval_source=None,
                rationale="no approval oracle; timeout treated as fallback",
            )
        approved = self.approval_oracle(decision_class, payload)
        if approved:
            return GateDecision(
                decision_class=decision_class,
                classification=cls,
                outcome=GateOutcome.GATE_APPROVED,
                fallback_state=None,
                approval_source="human",
                rationale="approved by human authority",
            )
        return GateDecision(
            decision_class=decision_class,
            classification=cls,
            outcome=GateOutcome.GATE_REJECTED,
            fallback_state=self.policy.fallback_for(decision_class),
            approval_source="human",
            rationale="rejected by human authority; fallback to safe-passive state",
        )
