"""Aletheia-style append-only signed chain.

HF-8 implementation: every decision event (autonomous resolution, gate request,
gate approval, gate rejection, timeout, fallback-to-safe-passive) appends to
this chain. Each entry is Ed25519-signed and hash-linked to predecessor.
Tamper-evident; chain integrity verifiable in linear time.
"""

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization


GENESIS_PREV_HASH = "0" * 64


@dataclass
class ChainEntry:
    seq: int
    timestamp_ns: int
    event_type: str
    event_payload: dict
    prev_hash: str
    entry_hash: str
    signature_hex: str

    def to_dict(self):
        return asdict(self)


def _canonical_json(obj) -> bytes:
    """Deterministic JSON serialization for hashing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def _compute_entry_hash(seq, timestamp_ns, event_type, event_payload, prev_hash) -> str:
    body = {
        "seq": seq,
        "timestamp_ns": timestamp_ns,
        "event_type": event_type,
        "event_payload": event_payload,
        "prev_hash": prev_hash,
    }
    return hashlib.sha256(_canonical_json(body)).hexdigest()


class AletheiaChain:
    """Append-only Ed25519-signed chain backed by SQLite.

    Append latency target: < 20 ms p99 on commodity hardware (HF-13 budget driver).
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS chain (
        seq INTEGER PRIMARY KEY,
        timestamp_ns INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        event_payload TEXT NOT NULL,
        prev_hash TEXT NOT NULL,
        entry_hash TEXT NOT NULL,
        signature_hex TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_event_type ON chain(event_type);
    """

    def __init__(self, db_path: Path, signing_key: Ed25519PrivateKey):
        self.db_path = Path(db_path)
        self.signing_key = signing_key
        self.public_key = signing_key.public_key()
        self._conn = sqlite3.connect(self.db_path, isolation_level=None, check_same_thread=False)
        self._conn.executescript(self.SCHEMA)
        # S-5: serialize concurrent appends
        self._append_lock = __import__("threading").Lock()
        # O-3 partial mitigation: witness file holds the current chain head hash.
        # External observers (ground station, replicated chain, OpenTimestamps anchor)
        # would observe this monotonic value. Truncation produces a head-hash that
        # does not match an externally-recorded prior anchor.
        self._witness_path = self.db_path.parent / (self.db_path.stem + ".witness")

    @classmethod
    def open_or_create(cls, db_path: Path, key_path: Path) -> "AletheiaChain":
        key_path = Path(key_path)
        if key_path.exists():
            with open(key_path, "rb") as f:
                key = serialization.load_pem_private_key(f.read(), password=None)
        else:
            key = Ed25519PrivateKey.generate()
            key_path.parent.mkdir(parents=True, exist_ok=True)
            with open(key_path, "wb") as f:
                f.write(
                    key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption(),
                    )
                )
        return cls(db_path, key)

    def _last_entry(self) -> Optional[ChainEntry]:
        row = self._conn.execute(
            "SELECT seq, timestamp_ns, event_type, event_payload, prev_hash, entry_hash, signature_hex FROM chain ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        return ChainEntry(
            seq=row[0],
            timestamp_ns=row[1],
            event_type=row[2],
            event_payload=json.loads(row[3]),
            prev_hash=row[4],
            entry_hash=row[5],
            signature_hex=row[6],
        )

    def append(self, event_type: str, event_payload: dict) -> ChainEntry:
        """Append an event. Returns the committed ChainEntry.

        Phase 6 hardenings:
          S-5: lock-serialized to prevent concurrent-append seq collisions.
          O-3: writes a witness file holding the current chain head hash on
               every append. External monitoring (OpenTimestamps anchor,
               replicated mirror) would detect truncation by observing a
               head-hash regression.
        """
        with self._append_lock:
            last = self._last_entry()
            seq = (last.seq + 1) if last else 0
            prev_hash = last.entry_hash if last else GENESIS_PREV_HASH
            ts = time.time_ns()
            entry_hash = _compute_entry_hash(seq, ts, event_type, event_payload, prev_hash)
            signature = self.signing_key.sign(bytes.fromhex(entry_hash))

            self._conn.execute(
                "INSERT INTO chain VALUES (?,?,?,?,?,?,?)",
                (
                    seq,
                    ts,
                    event_type,
                    json.dumps(event_payload, sort_keys=True, separators=(",", ":")),
                    prev_hash,
                    entry_hash,
                    signature.hex(),
                ),
            )
            # O-3 witness
            try:
                self._witness_path.write_text(json.dumps({
                    "head_seq": seq,
                    "head_hash": entry_hash,
                    "head_ts_ns": ts,
                }))
            except Exception:
                pass  # witness is advisory; don't fail the append
            return ChainEntry(seq, ts, event_type, event_payload, prev_hash, entry_hash, signature.hex())

    def replay(self):
        """Yield every entry in chain order."""
        cursor = self._conn.execute(
            "SELECT seq, timestamp_ns, event_type, event_payload, prev_hash, entry_hash, signature_hex FROM chain ORDER BY seq ASC"
        )
        for row in cursor:
            yield ChainEntry(
                seq=row[0],
                timestamp_ns=row[1],
                event_type=row[2],
                event_payload=json.loads(row[3]),
                prev_hash=row[4],
                entry_hash=row[5],
                signature_hex=row[6],
            )

    def verify_integrity(self) -> dict:
        """Walk the chain end-to-end. Returns dict with summary + any defects.

        HF-8 verification function.
        """
        defects = []
        count = 0
        expected_prev = GENESIS_PREV_HASH
        expected_seq = 0
        for entry in self.replay():
            count += 1
            # Sequence continuity
            if entry.seq != expected_seq:
                defects.append({"seq": entry.seq, "defect": "sequence_break", "expected": expected_seq})
            # Previous-hash linkage
            if entry.prev_hash != expected_prev:
                defects.append({"seq": entry.seq, "defect": "prev_hash_mismatch"})
            # Entry hash recomputation
            recomputed = _compute_entry_hash(
                entry.seq, entry.timestamp_ns, entry.event_type, entry.event_payload, entry.prev_hash
            )
            if recomputed != entry.entry_hash:
                defects.append({"seq": entry.seq, "defect": "entry_hash_mismatch"})
            # Signature verification
            try:
                self.public_key.verify(bytes.fromhex(entry.signature_hex), bytes.fromhex(entry.entry_hash))
            except Exception as e:
                defects.append({"seq": entry.seq, "defect": f"signature_invalid:{type(e).__name__}"})
            expected_prev = entry.entry_hash
            expected_seq = entry.seq + 1
        return {"entry_count": count, "defects": defects, "integrity_ok": len(defects) == 0}

    def count_unsigned_or_missing(self, authoritative_event_log: list) -> int:
        """For HF-8 fraction-unlogged audit.

        Given an authoritative source-of-truth log of events that *should* be on chain,
        count how many are missing or unsigned.
        """
        chain_signatures = {(e.event_type, e.timestamp_ns) for e in self.replay()}
        missing = 0
        for ev in authoritative_event_log:
            if (ev["event_type"], ev["timestamp_ns"]) not in chain_signatures:
                missing += 1
        return missing

    def verify_against_witness(self) -> dict:
        """O-3 partial mitigation. Compare current chain head against witness file.

        If the witness file records a higher head_seq than the current chain
        contains, the chain has been truncated. In production, the witness
        would be co-located with an external anchor (ground replica,
        OpenTimestamps) so an attacker who truncates the chain cannot also
        forge a rewinded witness.
        """
        import json as _json
        result = {"witness_present": False, "truncation_suspected": False}
        if not self._witness_path.exists():
            return result
        try:
            witness = _json.loads(self._witness_path.read_text())
        except Exception:
            return result
        result["witness_present"] = True
        result["witness"] = witness
        last = self._last_entry()
        current_head_seq = last.seq if last else -1
        current_head_hash = last.entry_hash if last else None
        result["current_head_seq"] = current_head_seq
        result["current_head_hash"] = current_head_hash
        if witness.get("head_seq", -1) > current_head_seq:
            result["truncation_suspected"] = True
        if witness.get("head_hash") != current_head_hash and witness.get("head_seq") == current_head_seq:
            result["head_hash_mismatch"] = True
        return result

    def close(self):
        self._conn.close()
