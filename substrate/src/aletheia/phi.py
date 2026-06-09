"""HIPAA at-rest encryption helper for PHI-bearing chain payloads.

Phase 6 C-1 partial mitigation. v0.1 ships Fernet (AES-128-CBC + HMAC) wrapper
for PHI fields written to the chain. Key derivation in v0.1 is from an
environment-supplied secret; v0.2 with HSM/KMS replaces this with hardware-key
custody and per-crew DEKs.

Honest status: this is a tactical hardening, not a HIPAA Security Rule
conformance certification. Conformance requires (a) BAA with the deploying
organization, (b) full key lifecycle management, (c) audit access controls
beyond what v0.1 demonstrates. v0.2 production substrate must close those.

Usage:
    from src.aletheia.phi import encrypt_phi, decrypt_phi
    cipher = encrypt_phi({"crew_id": "crew_a", "spo2": 78}, key=KEY)
    chain.append("BIOMEDICAL_ALERT", {"phi_cipher": cipher, "phi_scheme": "fernet-v0.1"})
"""

import base64
import hashlib
import json
import os
from typing import Any

from cryptography.fernet import Fernet, InvalidToken


PHI_KEY_ENV_VAR = "VBX_ISPS_PHI_KEY"


def _derive_key(secret: bytes) -> bytes:
    """Derive a Fernet-compatible (urlsafe base64, 32 bytes) key from a secret."""
    return base64.urlsafe_b64encode(hashlib.sha256(secret).digest())


def get_phi_key() -> bytes:
    """Read the PHI encryption key from environment, or auto-generate a session key.

    In v0.1, an auto-generated session key is acceptable for prototype evaluation.
    Production must inject the key from HSM or KMS via the environment.
    """
    secret = os.environ.get(PHI_KEY_ENV_VAR)
    if secret:
        return _derive_key(secret.encode())
    # session key — random per process; chain replay across process boundaries
    # requires the same env-supplied secret. In v0.1 this is acceptable.
    if not hasattr(get_phi_key, "_session_key"):
        get_phi_key._session_key = Fernet.generate_key()
    return get_phi_key._session_key


def encrypt_phi(payload: Any, key: bytes = None) -> str:
    """Encrypt a JSON-serializable payload. Returns urlsafe-base64 ciphertext."""
    key = key or get_phi_key()
    f = Fernet(key)
    plaintext = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return f.encrypt(plaintext).decode()


def decrypt_phi(ciphertext: str, key: bytes = None) -> Any:
    """Decrypt a previously encrypted PHI payload. Raises InvalidToken on failure."""
    key = key or get_phi_key()
    f = Fernet(key)
    plaintext = f.decrypt(ciphertext.encode())
    return json.loads(plaintext.decode())
