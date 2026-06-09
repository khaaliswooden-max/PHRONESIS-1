"""Biomedical alert pipeline (Phase 6 hardened).

HF-13 implementation: end-to-end latency from sensor event to crew-perceptible
alert <= 5 seconds INCLUDING chain signing of the alert event.

Phase 6 hardenings (v0.1.1):
  - S-6: chain layer applies its own ingress timestamp; sensor-reported time
    becomes an audit field, not the authoritative latency anchor.
  - C-1: PHI fields in the alert payload are encrypted via Fernet before chain
    write. Plain metadata (alert_class, sensor_id, timestamps) remains in the
    clear for routing/audit; sensitive payload is sealed.
"""

import time
from dataclasses import dataclass

from src.aletheia.phi import encrypt_phi


@dataclass
class AlertEvent:
    sensor_id: str
    alert_class: str
    payload: dict
    detected_at_ns: int


ALERT_CLASSES = (
    "cardiac_arrhythmia",
    "hypoxia",
    "hypercapnia",
    "hyperthermia",
    "pressure_loss",
    "sudden_loc",
)


def classify(sensor_event: dict) -> AlertEvent:
    return AlertEvent(
        sensor_id=sensor_event["sensor_id"],
        alert_class=sensor_event["alert_class"],
        payload=sensor_event.get("payload", {}),
        detected_at_ns=sensor_event.get("detected_at_ns", time.time_ns()),
    )


def emit_alert(alert: AlertEvent, chain, crew_interface_fn=None) -> dict:
    """Process an alert: sign-on-chain (PHI-encrypted), then surface to crew."""
    chain_ingress_ns = time.time_ns()
    # C-1: encrypt PHI payload; keep routing metadata in clear
    phi_cipher = encrypt_phi(alert.payload) if alert.payload else None
    t_chain_start = time.time_ns()
    chain.append("BIOMEDICAL_ALERT", {
        "alert_class": alert.alert_class,
        "sensor_id": alert.sensor_id,
        "phi_cipher": phi_cipher,
        "phi_scheme": "fernet-v0.1" if phi_cipher else None,
        "sensor_reported_ts_ns": alert.detected_at_ns,
        "chain_ingress_ts_ns": chain_ingress_ns,
        "ingress_skew_ms": (chain_ingress_ns - alert.detected_at_ns) / 1e6,
    })
    t_chain_done = time.time_ns()
    if crew_interface_fn is not None:
        crew_interface_fn(alert)
    t_crew = time.time_ns()
    return {
        "alert_class": alert.alert_class,
        # Latency is measured from chain_ingress (chain's own authoritative time),
        # not the caller-supplied detected_at_ns (which is audited via ingress_skew).
        "chain_ingress_to_chain_done_ns": t_chain_done - chain_ingress_ns,
        "chain_to_crew_ns": t_crew - t_chain_done,
        "total_latency_ns": t_crew - chain_ingress_ns,
        "total_latency_s": (t_crew - chain_ingress_ns) / 1e9,
        "sensor_reported_ts_ns": alert.detected_at_ns,
        "chain_ingress_ts_ns": chain_ingress_ns,
    }
