"""
utils/urgency.py
BRD: FR-URG-01 to FR-URG-05
Urgency / severity scoring with acoustic simulation for demo.

Levels: Critical > High > Medium > Low
Signals: lexical (text) + acoustic proxy (audio length/features) + contextual (time of day)
"""

import re
from datetime import datetime

# Lexical signals by urgency level (FR-URG-02)
_CRITICAL_WORDS = [
    "not breathing","unconscious","fainted","heart attack","stroke",
    "choking","drowning","electrocuted","trapped","collapse","collapsed",
    "explosion","blast","gas leak","dead","dying","blood loss","critical",
    # Marathi
    "मरत आहे","बेशुद्ध","रक्त","अडकले","स्फोट","आग लागली",
    # Hindi
    "मर रहा","बेहोश","खून बह","धमाका","फंसा",
]
_HIGH_WORDS = [
    "fire","fight","assault","robbery","accident","injured","injury",
    "attacked","bleeding","trapped","missing","kidnap","gas","smoke",
    "आग","चोरी","मारामारी","अपघात","जखमी","बेपत्ता","धूर",
    "आग","चोर","हत्या","दरोडा",
]
_MEDIUM_WORDS = [
    "urgent","hurry","please help","immediately","right now","fast",
    "no water","power cut","pothole","road damage","garbage",
    "तातडीने","लवकर","कृपया","मदत","urgente",
]

# Time-of-day risk boost (FR-URG-02 contextual)
def _time_boost() -> int:
    h = datetime.now().hour
    if 22 <= h or h < 5:  return 10   # night — higher risk
    if 5  <= h < 7:        return 5
    return 0


def score(text: str, dept: str, audio_duration_sec: float = 0) -> dict:
    """
    Compute urgency score and level.
    Returns: level, score (0-100), signals, override_allowed=True
    """
    t = text
    pts = 0
    signals = []

    crit = _match_list(_CRITICAL_WORDS, t)
    high = _match_list(_HIGH_WORDS,     t)
    med  = _match_list(_MEDIUM_WORDS,   t)

    if crit:
        pts += 60
        signals.extend(crit[:3])
    if high:
        pts += 25
        signals.extend(high[:2])
    if med:
        pts += 10
        signals.extend(med[:1])

    # Department boost
    if dept == "Fire":     pts += 20
    elif dept == "Ambulance": pts += 15
    elif dept == "Police":    pts += 5

    # Time-of-day boost
    tb = _time_boost()
    if tb:
        pts += tb
        signals.append(f"Night-time (+{tb}pts)")

    # Acoustic proxy: very short call with emergency dept → boost
    if 0 < audio_duration_sec < 5 and dept in ("Fire","Ambulance"):
        pts += 10
        signals.append("Short call on emergency line")

    pts = min(pts, 100)

    if pts >= 70:   level = "Critical"
    elif pts >= 45: level = "High"
    elif pts >= 20: level = "Medium"
    else:           level = "Low"

    return {
        "level":           level,
        "score":           pts,
        "signals":         list(dict.fromkeys(signals))[:6],  # deduplicate
        "override_allowed": True,    # FR-URG-04
        "scored_at":       datetime.utcnow().isoformat() + "Z",
    }


def _match_list(words, text):
    found = []
    for w in words:
        try:
            w.encode("ascii")
            if re.search(r'\b' + re.escape(w.lower()) + r'\b', text.lower()):
                found.append(w)
        except UnicodeEncodeError:
            if w in text:
                found.append(w)
    return found
