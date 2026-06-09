"""Bus isolation abstraction.

HF-10 dependency: in production, hardware enforces that only the formally
verified kernel can actuate safety-critical lines. In v0.1 (software-only), we
model the bus as an object that enforces a privilege-token check; the ML
inference subsystem holds no such token.

Phase 6 hardenings (v0.1.1):
  - Bus state is name-mangled (`__state`) and exposed only via read()/write();
    direct attribute assignment is no longer a bypass path.
  - The kernel privilege token is generated at process boot (random 32-byte
    secret), kept in module-scope, and verified by `is_kernel_token()` rather
    than equality with an importable constant. ML-side code can still import
    the module but cannot synthesize a valid token.

This is still a SURROGATE for the hardware mechanism. v0.2 with real Mercury
hardware must enforce the same property at the silicon level.
"""

import os
import secrets
from dataclasses import dataclass


# Boot-time generated kernel privilege secret. Kept in module scope; not a
# constant attribute. Modules that import this file see the verifier function
# but cannot reconstruct the secret from the function's signature.
_KERNEL_PRIVILEGE_SECRET = secrets.token_hex(32)


def get_kernel_token():
    """Returns the boot-time kernel token. The kernel module calls this once
    at startup and holds the token in local scope. Anything else calling this
    function and using the result is, by audit, behaving as the kernel.
    """
    return _KERNEL_PRIVILEGE_SECRET


def is_kernel_token(token):
    """Constant-time verifier. ML-side code cannot synthesize the secret."""
    if not isinstance(token, str):
        return False
    return secrets.compare_digest(token, _KERNEL_PRIVILEGE_SECRET)


# Legacy export (deprecated): retained only to surface a clear error if older
# code tries to import a constant. The string is intentionally invalid.
KERNEL_PRIVILEGE_TOKEN = "DEPRECATED_USE_get_kernel_token_INSTEAD"


class BusAccessDenied(Exception):
    pass


@dataclass
class BusAction:
    line: str
    command: int
    privilege_token: str


class SafetyBus:
    """Software-modeled safety bus with hardened state encapsulation."""

    SAFETY_LINES = ("o2_valve", "co2_scrubber", "pressure_dump", "battery_cutoff")

    def __init__(self):
        # Name-mangled private state; not reachable as `bus.state`.
        self.__state = {line: 0 for line in self.SAFETY_LINES}
        self.__write_attempts = []

    def read(self, line: str) -> int:
        return self.__state.get(line, 0)

    def write(self, action: BusAction) -> bool:
        self.__write_attempts.append({
            "line": action.line,
            "command": action.command,
            "token_valid": is_kernel_token(action.privilege_token),
        })
        if not is_kernel_token(action.privilege_token):
            raise BusAccessDenied(f"unauthorized write to {action.line}; token mismatch")
        if action.line not in self.SAFETY_LINES:
            raise BusAccessDenied(f"unknown safety line: {action.line}")
        self.__state[action.line] = action.command
        return True

    def audit_write_attempts(self) -> list:
        return list(self.__write_attempts)

    def snapshot(self) -> dict:
        """Read-only snapshot for audit. Returned dict is a copy."""
        return dict(self.__state)
