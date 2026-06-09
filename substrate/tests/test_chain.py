"""HF-8: Decision provenance, append-every-attempt.

Tests:
  1. Every event appended is signed and chain-linked.
  2. Tampering at any link is detected by verify_integrity().
  3. Red-team injection of falsified entries is detected.
  4. Fraction-unlogged on a 1000-event stream is 0.
"""

import json
import sqlite3
import tempfile
import time
from pathlib import Path

from src.aletheia.chain import AletheiaChain, GENESIS_PREV_HASH


def make_chain(tmpdir):
    db = Path(tmpdir) / "chain.db"
    key = Path(tmpdir) / "key.pem"
    return AletheiaChain.open_or_create(db, key), db


def test_chain_basic_integrity():
    with tempfile.TemporaryDirectory() as tmp:
        chain, _ = make_chain(tmp)
        for i in range(100):
            chain.append("TEST_EVENT", {"i": i})
        result = chain.verify_integrity()
        assert result["entry_count"] == 100
        assert result["integrity_ok"], result["defects"]
        chain.close()


def test_chain_tamper_detection():
    """Modify an entry's payload after the fact; verify_integrity must detect."""
    with tempfile.TemporaryDirectory() as tmp:
        chain, db = make_chain(tmp)
        for i in range(20):
            chain.append("TEST_EVENT", {"i": i})
        chain.close()
        # Tamper directly via sqlite
        conn = sqlite3.connect(db)
        conn.execute("UPDATE chain SET event_payload = ? WHERE seq = 10",
                     (json.dumps({"i": 99999, "tampered": True}, sort_keys=True, separators=(",", ":")),))
        conn.commit()
        conn.close()
        # Reopen and verify
        from cryptography.hazmat.primitives import serialization
        with open(Path(tmp) / "key.pem", "rb") as f:
            key = serialization.load_pem_private_key(f.read(), password=None)
        chain2 = AletheiaChain(db, key)
        result = chain2.verify_integrity()
        assert not result["integrity_ok"], "tampering should be detected"
        # Should flag the tampered entry
        defects_at_10 = [d for d in result["defects"] if d["seq"] == 10]
        assert len(defects_at_10) >= 1, "expected defect at seq=10"
        chain2.close()


def test_red_team_injection_detection():
    """Inject falsified entries; chain integrity walk must flag them.

    Per HF-8 verification: 1000 falsified events injected; chain detects each.
    """
    with tempfile.TemporaryDirectory() as tmp:
        chain, db = make_chain(tmp)
        # Legitimate entries
        for i in range(500):
            chain.append("DECISION_EVENT", {"i": i})
        chain.close()
        # Inject falsified entries directly (no signature; fabricated hashes)
        conn = sqlite3.connect(db)
        n_inject = 1000
        for j in range(n_inject):
            seq = 500 + j
            conn.execute(
                "INSERT INTO chain VALUES (?,?,?,?,?,?,?)",
                (seq, time.time_ns(), "INJECTED", json.dumps({"j": j}), "00" * 32, "ff" * 32, "00" * 64),
            )
        conn.commit()
        conn.close()
        from cryptography.hazmat.primitives import serialization
        with open(Path(tmp) / "key.pem", "rb") as f:
            key = serialization.load_pem_private_key(f.read(), password=None)
        chain2 = AletheiaChain(db, key)
        result = chain2.verify_integrity()
        # Every injected entry should produce at least one defect
        injected_defect_seqs = {d["seq"] for d in result["defects"] if d["seq"] >= 500}
        assert len(injected_defect_seqs) >= n_inject, (
            f"expected >= {n_inject} injected seqs flagged; got {len(injected_defect_seqs)}"
        )
        chain2.close()


def test_fraction_unlogged_is_zero_on_full_log():
    """1000 decision events go through chain; replay log shows zero unlogged."""
    with tempfile.TemporaryDirectory() as tmp:
        chain, _ = make_chain(tmp)
        authoritative = []
        for i in range(1000):
            ts_payload = chain.append("DECISION_ATTEMPT", {"i": i})
            authoritative.append({"event_type": "DECISION_ATTEMPT", "timestamp_ns": ts_payload.timestamp_ns})
        missing = chain.count_unsigned_or_missing(authoritative)
        assert missing == 0, f"expected 0 missing; got {missing}"
        chain.close()
