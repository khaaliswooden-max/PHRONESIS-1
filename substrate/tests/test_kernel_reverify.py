"""HF-14: Kernel re-verification on modification.

Process audit:
  - 10 kernel modification cycles simulated.
  - Each authorized deployment requires a signed re-verification artifact
    committed to the chain BEFORE the kernel modification takes effect.
  - Unauthorized deployment attempts are rejected.

v0.1 implementation: deployment is gated by a check that the kernel firmware
hash has a matching re-verification record on chain. Test simulates the
process; unauthorized firmware hash -> reject.
"""

import hashlib
import tempfile
from pathlib import Path

from src.aletheia.chain import AletheiaChain


class KernelDeployer:
    """v0.1 deployment gate.

    Deploys a kernel firmware blob only if its sha256 hash has an antecedent
    'KERNEL_REVERIFICATION' chain entry with a matching hash and signed
    authorization.
    """

    def __init__(self, chain: AletheiaChain):
        self.chain = chain
        self.deployed_hash = None

    def authorize_reverification(self, firmware_hash: str, authorizer: str):
        self.chain.append("KERNEL_REVERIFICATION", {
            "firmware_hash": firmware_hash,
            "authorizer": authorizer,
            "verification_artifacts": ["formal_proof_v0_1.coq", "wcet_analysis_v0_1.pdf"],
        })

    def deploy(self, firmware_bytes: bytes) -> bool:
        firmware_hash = hashlib.sha256(firmware_bytes).hexdigest()
        # Walk the chain looking for a matching reverification record
        for entry in self.chain.replay():
            if entry.event_type == "KERNEL_REVERIFICATION" and entry.event_payload.get("firmware_hash") == firmware_hash:
                self.chain.append("KERNEL_DEPLOYMENT_SUCCESS", {
                    "firmware_hash": firmware_hash,
                })
                self.deployed_hash = firmware_hash
                return True
        # No matching record -> reject
        self.chain.append("KERNEL_DEPLOYMENT_REJECTED", {
            "firmware_hash": firmware_hash,
            "reason": "no matching reverification record on chain",
        })
        return False


def test_authorized_deployment_succeeds():
    with tempfile.TemporaryDirectory() as tmp:
        chain = AletheiaChain.open_or_create(Path(tmp) / "chain.db", Path(tmp) / "key.pem")
        deployer = KernelDeployer(chain)
        firmware = b"kernel firmware bytes v0.1"
        h = hashlib.sha256(firmware).hexdigest()
        deployer.authorize_reverification(h, authorizer="A. Khaalis Wooden, Sr.")
        assert deployer.deploy(firmware) is True
        chain.close()


def test_unauthorized_deployment_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        chain = AletheiaChain.open_or_create(Path(tmp) / "chain.db", Path(tmp) / "key.pem")
        deployer = KernelDeployer(chain)
        # No reverification record beforehand
        firmware = b"unauthorized kernel bytes"
        assert deployer.deploy(firmware) is False
        # And a rejection event was logged
        events = [e.event_type for e in chain.replay()]
        assert "KERNEL_DEPLOYMENT_REJECTED" in events
        chain.close()


def test_10_modification_cycles_all_audited():
    """Simulate 10 cycles. Each authorized -> deployed. One unauthorized -> rejected."""
    with tempfile.TemporaryDirectory() as tmp:
        chain = AletheiaChain.open_or_create(Path(tmp) / "chain.db", Path(tmp) / "key.pem")
        deployer = KernelDeployer(chain)
        for i in range(10):
            firmware = f"kernel v0.{i}".encode()
            h = hashlib.sha256(firmware).hexdigest()
            deployer.authorize_reverification(h, authorizer="A. Khaalis Wooden, Sr.")
            assert deployer.deploy(firmware), f"cycle {i} should succeed"
        # One unauthorized attempt
        rogue = b"rogue firmware"
        assert deployer.deploy(rogue) is False
        # Chain should have 10 reverifications + 10 successes + 1 rejection = 21 events
        events = list(chain.replay())
        success_count = sum(1 for e in events if e.event_type == "KERNEL_DEPLOYMENT_SUCCESS")
        reject_count = sum(1 for e in events if e.event_type == "KERNEL_DEPLOYMENT_REJECTED")
        reverif_count = sum(1 for e in events if e.event_type == "KERNEL_REVERIFICATION")
        assert success_count == 10
        assert reject_count == 1
        assert reverif_count == 10
        chain.close()
