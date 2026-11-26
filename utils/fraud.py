"""
utils/fraud.py
BRD: FR-FRA-01 to FR-FRA-06
Spam / prank / fraud screening (prototype-level, no real biometrics).

Implements:
  FR-FRA-01 — CLI reputation check (local blacklist)
  FR-FRA-02 — repeat caller detection (rolling window, in-memory)
  FR-FRA-03 — synthetic/prank pattern detection (text signals)
  FR-FRA-04 — throttle/quarantine flagged callers
  FR-FRA-05 — fraud decision logged with evidence
"""

import re
from datetime import datetime, timedelta
from collections import defaultdict

# In-memory stores (replaced by DB in production)
_blacklist  = set(["0000000000", "1111111111", "9999999999"])  # demo blacklist
_call_log   = defaultdict(list)   # cli -> [timestamps]
_fraud_log  = []

# Prank / spam text signals
_PRANK_SIGNALS = [
    "testing","test call","hello hello","checking","dummy",
    "prank","joke","haha","lol","just checking",
    "no problem","nothing","never mind","wrong number",
]

_SPAM_PHRASES = [
    "offer","discount","prize","won","lottery","credit card",
    "loan","insurance","free","click","link","otp",
]


def screen_call(cli: str, transcript: str = "", caller_id: str = "") -> dict:
    """
    FR-FRA-01/02/03: Screen call for fraud/spam/prank.
    Returns dict with is_fraud, risk_level, reason, action.
    """
    cli_clean = re.sub(r'\D', '', cli or "")
    evidence  = []
    risk      = 0

    # FR-FRA-01: CLI blacklist
    if cli_clean in _blacklist:
        evidence.append(f"CLI {cli_clean} on blacklist")
        risk += 60

    # FR-FRA-02: Repeat caller (>5 calls in 10 min)
    now = datetime.utcnow()
    _call_log[cli_clean].append(now)
    _call_log[cli_clean] = [t for t in _call_log[cli_clean]
                             if now - t < timedelta(minutes=10)]
    call_count = len(_call_log[cli_clean])
    if call_count > 5:
        evidence.append(f"Repeat caller: {call_count} calls in 10 min")
        risk += 40
    elif call_count > 3:
        evidence.append(f"Frequent caller: {call_count} calls in 10 min")
        risk += 20

    # FR-FRA-03: Prank text signals
    if transcript:
        t = transcript.lower()
        prank_hits = [p for p in _PRANK_SIGNALS if p in t]
        spam_hits  = [p for p in _SPAM_PHRASES  if p in t]
        if prank_hits:
            evidence.append(f"Prank signals: {prank_hits}")
            risk += 35
        if spam_hits:
            evidence.append(f"Spam signals: {spam_hits}")
            risk += 25
        # Very short or meaningless transcript
        if len(transcript.strip()) < 8:
            evidence.append("Transcript too short / empty")
            risk += 20

    # FR-FRA-04: Determine action
    if risk >= 60:
        is_fraud   = True
        risk_level = "High"
        action     = "quarantine"
    elif risk >= 35:
        is_fraud   = False
        risk_level = "Medium"
        action     = "flag_for_review"
    else:
        is_fraud   = False
        risk_level = "Low"
        action     = "allow"

    decision = {
        "cli":        cli_clean,
        "is_fraud":   is_fraud,
        "risk_level": risk_level,
        "risk_score": risk,
        "action":     action,
        "evidence":   evidence,
        "call_count": call_count,
        "checked_at": datetime.utcnow().isoformat() + "Z",
    }

    # FR-FRA-05: log every fraud decision
    _fraud_log.append(decision)
    return decision


def flag_as_fraud(cli: str, reason: str = "operator_flagged"):
    """FR-FRA-06: Operator one-click flag."""
    cli_clean = re.sub(r'\D', '', cli or "")
    _blacklist.add(cli_clean)
    _fraud_log.append({
        "cli": cli_clean, "action": "manually_blacklisted",
        "reason": reason, "flagged_at": datetime.utcnow().isoformat() + "Z",
    })
    return True


def get_fraud_log():
    return list(reversed(_fraud_log[-50:]))
