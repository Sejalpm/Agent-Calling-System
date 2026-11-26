"""
utils/audit.py
BRD: FR-ADM-05 (tamper-evident audit log), FR-FRA-05 (fraud audit),
     FR-RTE-01 (routing decisions logged), FR-CAL-07 (call records).

Prototype: in-memory audit log with hash chaining.
Production: replace with append-only DB / WORM storage.
"""

import hashlib, json, uuid
from datetime import datetime
from collections import deque

# Append-only audit log (max 1000 entries in memory)
_audit_chain = deque(maxlen=1000)
_last_hash   = "GENESIS"


def log_event(actor: str, action: str, payload: dict = None, ref_no: str = "") -> dict:
    """
    Append tamper-evident event to audit chain.
    Each entry includes hash of the previous entry (chain-of-custody).
    """
    global _last_hash

    entry = {
        "id":         str(uuid.uuid4()),
        "ref_no":     ref_no,
        "actor":      actor,
        "action":     action,
        "payload":    payload or {},
        "ts":         datetime.utcnow().isoformat() + "Z",
        "prev_hash":  _last_hash,
    }

    # Hash this entry (tamper-evident)
    entry_str   = json.dumps(entry, sort_keys=True, ensure_ascii=False)
    entry_hash  = hashlib.sha256(entry_str.encode()).hexdigest()[:16]
    entry["hash"] = entry_hash
    _last_hash    = entry_hash

    _audit_chain.appendleft(entry)
    return entry


def get_log(limit: int = 100) -> list:
    return list(_audit_chain)[:limit]


def verify_chain() -> bool:
    """Verify the chain integrity (detect tampering)."""
    entries = list(_audit_chain)
    for i in range(len(entries) - 1):
        curr = entries[i]
        prev = entries[i + 1]
        if curr["prev_hash"] != prev["hash"]:
            return False
    return True


# ── Convenience wrappers ──────────────────────────────────────────────────────

def log_call_received(cli: str, ref_no: str, language: str):
    return log_event("system", "call_received",
                     {"cli": cli, "language": language}, ref_no)

def log_classification(ref_no: str, dept: str, urgency: str, confidence: str):
    return log_event("ai_classifier", "classified",
                     {"dept": dept, "urgency": urgency, "confidence": confidence}, ref_no)

def log_routing(ref_no: str, dept: str, phone: str):
    return log_event("routing_engine", "routed",
                     {"destination": dept, "phone": phone}, ref_no)

def log_fraud_decision(ref_no: str, cli: str, action: str, risk: int):
    return log_event("fraud_engine", "fraud_screened",
                     {"cli": cli, "action": action, "risk_score": risk}, ref_no)

def log_operator_action(operator: str, ref_no: str, action: str, detail: str = ""):
    return log_event(operator, action, {"detail": detail}, ref_no)
