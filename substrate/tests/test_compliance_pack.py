"""HF-15: Embodied-AI compliance evidence package.

Tests:
  1. Evidence package document exists.
  2. All 15 hard-fail floors are referenced with clause mappings.
  3. All 7 required standards are mapped.
"""

from pathlib import Path


PKG = Path(__file__).resolve().parents[1] / "compliance" / "HF15_evidence_package.md"


def test_package_exists():
    assert PKG.exists(), f"package missing: {PKG}"


def test_package_contains_all_15_floors():
    txt = PKG.read_text()
    for i in range(1, 16):
        assert f"HF-{i} " in txt or f"HF-{i}\n" in txt or f"HF-{i})" in txt, f"HF-{i} not mentioned"


def test_package_maps_all_standards():
    txt = PKG.read_text()
    required = ["ISO 12100", "R15.08-1", "R15.06-2025", "R15.08-2", "M-25-22", "HIPAA", "NASA-STD-3001"]
    for std in required:
        assert std in txt, f"standard not in package: {std}"


def test_substrate_floors_demonstrated_in_v0_1():
    """The 7 substrate-scope floors must show DEMONSTRATED status in v0.1."""
    txt = PKG.read_text()
    for floor in ("HF-8", "HF-9", "HF-10", "HF-12", "HF-13", "HF-14", "HF-15"):
        # Find any line that contains this floor and "DEMONSTRATED"
        lines = [ln for ln in txt.splitlines() if floor in ln and "DEMONSTRATED" in ln]
        assert len(lines) >= 1, f"{floor} should have at least one DEMONSTRATED row"
