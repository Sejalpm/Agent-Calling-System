"""
utils/classifier.py
BRD Requirements implemented:
  FR-NLU-02  — intent classification into published categories (95% accuracy target)
  FR-URG-01  — severity score: Critical / High / Medium / Low within 5 sec
  FR-URG-02  — lexical cues for fire/medical/police/civic urgency
  FR-NLU-04  — code-mixed speech (Hinglish, Marathi-English)
  FR-RTE-05  — multi-department detection (gas leak + injury → Fire + Ambulance)
  FR-NLU-03  — slot extraction: complaint_type, location hints, asset refs
"""

import re
import uuid
from datetime import datetime

# ─── Keyword banks ────────────────────────────────────────────────────────────

POLICE_KEYWORDS = [
    # English
    "fight","fighting","brawl","assault","attack","attacked","beating","hit",
    "steal","stealing","stolen","theft","thief","rob","robbery","loot","looting",
    "murder","killed","dead body","shooting","gun","pistol","knife","weapon","armed",
    "broke in","break in","burglary","burglar","trespass",
    "threat","threatening","blackmail","extortion","ransom",
    "violence","violent","riot","mob","rowdy","vandalism","arson",
    "drunk driving","harass","harassment","molestation","eve teasing",
    "rape","sexual assault","domestic violence","abuse",
    "missing","kidnap","kidnapping","abduction","hostage",
    "suspicious","crime","criminal","illegal","drug","drugs",
    "accident","hit and run","rash driving","road rage",
    # Hindi transliterated + Devanagari
    "chor","chori","maar","maarpeet","jhagda","danga","ladai","loot","dakait",
    "धमकी","मारपीट","चोरी","झगड़ा","लूट","हत्या","बलात्कार","दंगा","अपहरण","छेड़खानी",
    # Marathi Devanagari
    "चोर","चोरी","मारामारी","भांडण","दरोडा","खून","हत्या","बलात्कार",
    "जबरदस्ती","धमकी","दंगल","लूट","अपहरण","बेपत्ता","संशयित",
    "गुन्हा","गुंड","मद्यपान","छेडछाड","जाळपोळ","तोडफोड",
    "मार","मारहाण","शस्त्र","पिस्तूल","चाकू",
]

FIRE_KEYWORDS = [
    # English
    "fire","flame","flames","burning","burn","burnt","on fire","blaze",
    "smoke","smoky","fumes","explosion","explode","blast",
    "gas leak","gas pipe","lpg","cylinder","cylinder blast",
    "short circuit","electrical fire","live wire","spark",
    "wildfire","forest fire","field fire",
    "rescue","trapped","collapse","collapsed","building collapse",
    "chemical","acid","hazmat","toxic",
    # Hindi
    "aag","aag lagi","dhua","gas","bachao","jal raha",
    "आग","धुआं","विस्फोट","गैस","बचाओ","फंसा","जल",
    # Marathi
    "आग","आग लागली","धूर","स्फोट","गॅस गळती","गॅस",
    "जळत","जळाले","वाचवा","अडकलो","इमारत कोसळली",
    "विद्युत","शॉर्ट सर्किट","रसायन",
]

MEDICAL_KEYWORDS = [
    # English
    "ambulance","hospital","doctor","injured","injury","accident",
    "unconscious","fainted","fainting","not breathing","heart attack",
    "stroke","bleeding","blood","fracture","broken bone","overdose",
    "poisoning","allergic","anaphylaxis","seizure","epilepsy",
    "chest pain","breathless","choking","drowning","electrocuted",
    "pregnant","labour","delivery","baby","newborn",
    "suicide","self harm","attempted",
    # Hindi
    "ambulance","doctor","dawa","behosh","khoon","dard","hospital",
    "बेहोश","खून","दर्द","सांस","दिल","दुर्घटना","चोट",
    # Marathi
    "रुग्णवाहिका","डॉक्टर","बेशुद्ध","रक्त","श्वास","हृदय",
    "दुखापत","अपघात","जखमी","रुग्णालय","वेदना",
]

MUNICIPAL_KEYWORDS = [
    # Water
    "water","no water","water supply","water cut","dirty water",
    "water leak","pipe burst","water pressure","contaminated water",
    "drainage","sewer","sewage","overflow","waterlogging","flooding","flood",
    # Road / Infrastructure
    "pothole","road","road damage","broken road","street light","streetlight",
    "footpath","road repair","signal","traffic signal","bridge","flyover",
    # Garbage / Sanitation
    "garbage","waste","trash","litter","dustbin","dumping","open dump",
    "sanitation","sweeping","cleaning","dirty","stink","smell",
    # Electricity / Civic
    "electricity","power cut","power outage","no power","light gone",
    "voltage","low voltage","transformer","electric pole","wire",
    "noise","pollution","stray dog","stray animal","mosquito","pest",
    "park","encroachment","illegal construction","tree fell","fallen tree",
    # Hindi
    "pani","paani","kachra","rasta","sadak","bijli","light","naali",
    "पानी","कचरा","सड़क","बिजली","नाली","सफाई","बिजली कटी",
    # Marathi — Water
    "पाणी","पाणीपुरवठा","पाणी नाही","पाणी गेले","गळती","पाईप",
    "गटार","नाली","सांडपाणी","पूर","पाणी तुंबले",
    # Marathi — Road
    "रस्ता","खड्डा","रस्त्यावर","दिवाबत्ती","पथदीप","सिग्नल","पूल",
    # Marathi — Garbage
    "कचरा","घाण","सफाई","स्वच्छता","डस्टबिन","कचरा उचलला नाही",
    "दुर्गंधी","घाण पाणी","कचरागाडी",
    # Marathi — Electricity
    "वीज","वीज गेली","लाईट","लाइट नाही","विद्युत","ट्रान्सफॉर्मर",
    "वीज खंडित","दिवा","विद्युत खांब",
]

# ─── Critical / urgency signal words (FR-URG-02) ──────────────────────────────

CRITICAL_SIGNALS = [
    "not breathing","unconscious","fainted","heart attack","stroke","choking",
    "drowning","electrocuted","trapped","collapse","collapsed","explosion","blast",
    "gas leak","dead","dying","blood","bleeding heavily","critical","emergency",
    "immediately","right now","hurry","fast","urgent","please help",
    # Hindi
    "मर रहा","बेहोश","खून","तुरंत","जल्दी","bachao","bachaaoo",
    # Marathi
    "मरत आहे","बेशुद्ध","रक्त","लवकर","तातडीने","वाचवा","अडकले",
]

HIGH_SIGNALS = [
    "fire","fight","assault","robbery","accident","injured","missing",
    "आग","चोरी","मारामारी","अपघात","जखमी","बेपत्ता",
    "चोर","हत्या","दरोडा",
]

# ─── Dept config (FR-RTE-01 routing matrix) ───────────────────────────────────

DEPT_INFO = {
    "Police":    {"label":"Police Department",         "emoji":"🚔","color":"#3b82f6","description":"Law enforcement, crime & accident response","phone":"100"},
    "Fire":      {"label":"Fire & Emergency Services", "emoji":"🚒","color":"#ef4444","description":"Fire, rescue, gas leak & emergency response","phone":"101"},
    "Ambulance": {"label":"Ambulance / Medical",       "emoji":"🚑","color":"#f97316","description":"Medical emergency & trauma response","phone":"102"},
    "Municipal": {"label":"Municipal Corporation",     "emoji":"🏛️","color":"#22c55e","description":"Water, roads, garbage & electricity","phone":"1916"},
    "General":   {"label":"General Helpline",          "emoji":"📋","color":"#94a3b8","description":"General civic queries & information","phone":"1800"},
}

# ─── Multilingual response templates (FR-NLU-01 + BRD §7.2) ──────────────────

_RESPONSES = {
    "Police": {
        "en": "Your complaint has been received and logged. This is a law enforcement matter. Your call is being redirected to the {label} (Dial {phone}). Officers will be dispatched. Please stay safe.",
        "mr": "तुमची तक्रार नोंदवली गेली आहे. हे कायदा व सुव्यवस्थेचे प्रकरण आहे. तुमचा कॉल {label} कडे पाठवला जात आहे (डायल {phone}). पोलीस अधिकारी लवकरच येतील. कृपया सुरक्षित राहा.",
        "hi": "आपकी शिकायत दर्ज की गई है। यह कानून व्यवस्था का मामला है। आपका कॉल {label} को भेजा जा रहा है (डायल {phone})। पुलिस अधिकारी जल्द आएंगे।",
    },
    "Fire": {
        "en": "⚠️ URGENT — Fire or emergency hazard detected. Your call is being IMMEDIATELY redirected to {label} (Dial {phone}). Please EVACUATE now. Do NOT use lifts. Stay low if there is smoke.",
        "mr": "⚠️ तातडीचे — आग किंवा आणीबाणी आढळली. तुमचा कॉल {label} कडे तत्काळ पाठवला जात आहे (डायल {phone}). कृपया आत्ताच बाहेर पडा. लिफ्ट वापरू नका.",
        "hi": "⚠️ तत्काल — आग या आपात स्थिति का पता चला। आपका कॉल {label} को तत्काल भेजा जा रहा है (डायल {phone})। कृपया अभी बाहर निकलें।",
    },
    "Ambulance": {
        "en": "🚑 MEDICAL EMERGENCY — Your call is being redirected to {label} (Dial {phone}). Please keep the patient still. Do not move them if there is a spinal injury. Help is on the way.",
        "mr": "🚑 वैद्यकीय आणीबाणी — तुमचा कॉल {label} कडे पाठवला जात आहे (डायल {phone}). रुग्णाला हलवू नका. मदत येत आहे.",
        "hi": "🚑 चिकित्सा आपात — आपका कॉल {label} को भेजा जा रहा है (डायल {phone})। मरीज को हिलाएं नहीं। मदद आ रही है।",
    },
    "Municipal": {
        "en": "Your civic complaint has been recorded. Your call is being redirected to {label} (Helpline: {phone}). A municipal officer will follow up within 24–48 hours.",
        "mr": "तुमची नागरी तक्रार नोंदवली गेली आहे. तुमचा कॉल {label} कडे पाठवला जात आहे (हेल्पलाइन: {phone}). एक महापालिका अधिकारी २४-४८ तासांत संपर्क करेल.",
        "hi": "आपकी नागरिक शिकायत दर्ज की गई है। आपका कॉल {label} को भेजा जा रहा है (हेल्पलाइन: {phone})। एक नगर पालिका अधिकारी 24-48 घंटों में संपर्क करेगा।",
    },
    "General": {
        "en": "Your complaint has been received. Your call is being redirected to {label} (Helpline: {phone}). We will get back to you shortly.",
        "mr": "तुमची तक्रार मिळाली आहे. तुमचा कॉल {label} कडे पाठवला जात आहे (हेल्पलाइन: {phone}). आम्ही लवकरच संपर्क करू.",
        "hi": "आपकी शिकायत प्राप्त हुई है। आपका कॉल {label} को भेजा जा रहा है (हेल्पलाइन: {phone})। हम जल्द ही आपसे संपर्क करेंगे।",
    },
}

_LANG_NAMES = {
    "en":"English","mr":"Marathi","hi":"Hindi",
    "te":"Telugu","ta":"Tamil","kn":"Kannada","gu":"Gujarati","unknown":"Unknown",
}

# ─── Matching helpers ─────────────────────────────────────────────────────────

def _is_ascii(s):
    try: s.encode("ascii"); return True
    except UnicodeEncodeError: return False

def _match(keywords, text):
    """
    ASCII keywords → word-boundary regex.
    Devanagari keywords → plain substring (\\b breaks on Unicode).
    """
    found = []
    for kw in keywords:
        if _is_ascii(kw):
            if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text.lower()):
                found.append(kw)
        else:
            if kw in text:
                found.append(kw)
    return found

def _urgency_score(text, dept, hits):
    """
    FR-URG-01/02: Score every call on Critical/High/Medium/Low.
    Uses lexical signals + department type + hit count.
    """
    crit_hits = _match(CRITICAL_SIGNALS, text)
    high_hits = _match(HIGH_SIGNALS, text)

    if crit_hits or dept in ("Fire","Ambulance"):
        return "Critical", crit_hits or high_hits
    elif high_hits or (dept == "Police" and len(hits) >= 1):
        return "High", high_hits
    elif len(hits) >= 2:
        return "Medium", hits[:3]
    else:
        return "Low", hits[:2]

def _multi_dept(fire_h, police_h, med_h, muni_h, text):
    """
    FR-RTE-05: detect cases needing MULTIPLE departments.
    e.g. gas leak + injury → Fire + Ambulance
         accident + injury → Police + Ambulance
    """
    departments = []
    if fire_h:   departments.append("Fire")
    if med_h:    departments.append("Ambulance")
    if police_h and "Ambulance" not in departments: departments.append("Police")
    if muni_h and not departments: departments.append("Municipal")

    # Bridge conditions
    if "Fire" in departments and med_h:
        if "Ambulance" not in departments:
            departments.append("Ambulance")
    if "Police" in departments and med_h:
        if "Ambulance" not in departments:
            departments.append("Ambulance")

    return departments if len(departments) > 1 else []

def _extract_slots(text):
    """
    FR-NLU-03: extract structured slots from utterance.
    Returns dict of extracted structured information.
    """
    slots = {}

    # Location hints — simple pattern matching
    loc_patterns = [
        r'\bnear\s+([\w\s]+)',
        r'\bin\s+([\w\s]+(?:area|nagar|ward|road|lane|colony|chowk|bazaar|peth|wadi))',
        r'\bat\s+([\w\s]+)',
        r'(\w+\s+road|\w+\s+street|\w+\s+nagar|\w+\s+colony)',
    ]
    for p in loc_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            slots["location_hint"] = m.group(1).strip()
            break

    # Asset / vehicle references
    vehicle = re.search(r'\b(bike|motorcycle|car|truck|bus|auto|scooter|vehicle)\b', text, re.IGNORECASE)
    if vehicle:
        slots["asset"] = vehicle.group(1)

    # Duration references
    duration = re.search(r'(\d+)\s*(day|days|hour|hours|din|ghanta|divas)', text, re.IGNORECASE)
    if duration:
        slots["duration"] = f"{duration.group(1)} {duration.group(2)}"

    # Person count hints
    count = re.search(r'(\d+)\s*(people|persons|log|manus|jaan)', text, re.IGNORECASE)
    if count:
        slots["affected_count"] = count.group(1)

    return slots


# ─── Main classify function ────────────────────────────────────────────────────

def classify(text: str, detected_language: str = "en") -> dict:
    """
    FR-NLU-02: classify complaint + extract urgency + detect multi-dept.
    detected_language: Whisper language code (en/mr/hi/...)
    """
    fire_h   = _match(FIRE_KEYWORDS,     text)
    police_h = _match(POLICE_KEYWORDS,   text)
    med_h    = _match(MEDICAL_KEYWORDS,  text)
    muni_h   = _match(MUNICIPAL_KEYWORDS,text)

    # FR-RTE-05: multi-department detection
    multi = _multi_dept(fire_h, police_h, med_h, muni_h, text)

    # Primary department: Fire > Ambulance > Police > Municipal > General
    if fire_h:
        dept, hits = "Fire",      fire_h
    elif med_h:
        dept, hits = "Ambulance", med_h
    elif police_h:
        dept, hits = "Police",    police_h
    elif muni_h:
        dept, hits = "Municipal", muni_h
    else:
        dept, hits = "General",   []

    # FR-URG-01/02: urgency scoring
    urgency, urgency_signals = _urgency_score(text, dept, hits)

    # FR-NLU-03: slot extraction
    slots = _extract_slots(text)

    # Response language
    resp_lang = detected_language if detected_language in ("mr","hi") else "en"
    info      = DEPT_INFO[dept]
    tmpl      = _RESPONSES[dept][resp_lang]
    response  = tmpl.format(label=info["label"], phone=info["phone"])

    # Complaint reference number
    ref_no = f"JAN-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

    return {
        # Core classification
        "department":          dept,
        "dept_label":          info["label"],
        "emoji":               info["emoji"],
        "color":               info["color"],
        "description":         info["description"],
        "phone":               info["phone"],

        # Confidence & urgency (FR-URG-01)
        "confidence":          "High" if len(hits) >= 2 else ("Medium" if hits else "Low"),
        "urgency":             urgency,
        "urgency_signals":     urgency_signals[:5],

        # Keywords & slots (FR-NLU-03)
        "matched_kw":          hits[:8],
        "slots":               slots,

        # Multi-department (FR-RTE-05)
        "multi_departments":   multi,

        # Response
        "response":            response,
        "response_lang":       _LANG_NAMES.get(resp_lang, "English"),
        "detected_language":   _LANG_NAMES.get(detected_language, detected_language),

        # Audit fields (FR-ADM-01 / FR-FRA-05)
        "ref_no":              ref_no,
        "classified_at":       datetime.utcnow().isoformat() + "Z",
    }
