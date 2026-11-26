"""
JanSeva — AI Call Routing System
BRD v1.0 Prototype Implementation

BRD Sections Implemented:
  §7.1  FR-CAL-01/03/07  — call reception, language detect, consent/recording
  §7.2  FR-NLU-01/02/03/04/05  — multilingual STT, classification, slot extraction, code-mix
  §7.3  FR-URG-01/02/03/04/05  — urgency scoring, Critical escalation, override
  §7.5  FR-FRA-01/02/03/04/05/06  — fraud/spam screening, CLI blacklist
  §7.6  FR-RTE-01/02/03/05  — routing matrix, multi-dept detection
  §7.8  FR-NTF-01  — SMS acknowledgement simulation
  §7.9  FR-ADM-01/02/03/05  — live KPIs, audit log, call search

Run:  streamlit run app.py
"""

import os, sys, json, time, uuid
import streamlit as st

_ffmpeg = r"C:\ffmpeg-8.1-essentials_build\bin"
if os.path.exists(_ffmpeg):
    os.environ["PATH"] = _ffmpeg + ";" + os.environ["PATH"]

sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="JanSeva · AI Emergency & Civic Helpline",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
html,body{font-family:'DM Sans',sans-serif;}
.hero{text-align:center;padding:1.5rem 1rem 0.8rem;}
.hero h1{font-family:'Syne',sans-serif;font-size:2.2rem;font-weight:800;
  background:linear-gradient(135deg,color-mix(in srgb,#2563eb 70%,currentColor) 0%,color-mix(in srgb,#8b5cf6 70%,currentColor) 50%,color-mix(in srgb,#db2777 70%,currentColor) 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0 0 0.2rem;}
.hero p{color:color-mix(in srgb,currentColor 78%,transparent);font-size:0.9rem;font-weight:300;margin:0;}
.card{background:color-mix(in srgb,currentColor 5%,transparent);border:1px solid color-mix(in srgb,currentColor 20%,transparent);border-radius:14px;padding:1.2rem;margin-bottom:0.8rem;}
.card-title{font-family:'Syne',sans-serif;font-size:0.7rem;font-weight:600;letter-spacing:.12em;
  text-transform:uppercase;color:color-mix(in srgb,currentColor 78%,transparent);margin-bottom:0.6rem;}
.stButton>button{width:100%!important;
  background:linear-gradient(135deg,#3b6ff5 0%,#8b5cf6 100%)!important;
  color:white!important;border:none!important;border-radius:10px!important;
  font-family:'Syne',sans-serif!important;font-size:.95rem!important;
  font-weight:700!important;padding:.65rem 1.2rem!important;}
.stButton>button:hover{opacity:.85!important;}
.stButton>button:disabled{opacity:.35!important;}

/* urgency colors */
.urg-critical{background:#7f1d1d22;border:2px solid #ef444488;border-radius:10px;
  padding:.6rem 1rem;color:color-mix(in srgb, #fca5a5 45%, currentColor);font-weight:700;font-family:'Syne',sans-serif;}
.urg-high{background:#78350f22;border:2px solid #f59e0b88;border-radius:10px;
  padding:.6rem 1rem;color:color-mix(in srgb, #fcd34d 45%, currentColor);font-weight:700;font-family:'Syne',sans-serif;}
.urg-medium{background:#1e3a5f22;border:2px solid #3b82f688;border-radius:10px;
  padding:.6rem 1rem;color:color-mix(in srgb, #93c5fd 45%, currentColor);font-weight:700;font-family:'Syne',sans-serif;}
.urg-low{background:#14532d22;border:2px solid #22c55e88;border-radius:10px;
  padding:.6rem 1rem;color:color-mix(in srgb, #86efac 45%, currentColor);font-weight:700;font-family:'Syne',sans-serif;}

.redirect-banner{text-align:center;padding:1rem;border-radius:12px;
  font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;margin-bottom:.8rem;}
.transcript-box{background:color-mix(in srgb,currentColor 5%,transparent);border:1px solid color-mix(in srgb,currentColor 20%,transparent);border-left:3px solid #3b6ff5;
  border-radius:8px;padding:.9rem 1.1rem;font-size:.95rem;line-height:1.75;color:color-mix(in srgb, #c8d4e8 45%, currentColor);font-style:italic;}
.original-box{background:color-mix(in srgb,currentColor 5%,transparent);border:1px solid color-mix(in srgb,currentColor 20%,transparent);border-left:3px solid #22c55e;
  border-radius:8px;padding:.75rem 1rem;margin-top:.4rem;font-size:.88rem;line-height:1.7;color:color-mix(in srgb, #86efac 45%, currentColor);}
.response-box{background:color-mix(in srgb,currentColor 5%,transparent);border:1px solid color-mix(in srgb,currentColor 20%,transparent);border-left:3px solid #34d399;
  border-radius:8px;padding:.9rem 1.1rem;font-size:.91rem;line-height:1.75;color:color-mix(in srgb, #a7f3d0 45%, currentColor);}
.fraud-box{background:color-mix(in srgb,currentColor 5%,transparent);border:1px solid #9f123788;border-radius:10px;
  padding:.9rem 1.1rem;color:color-mix(in srgb, #fda4af 45%, currentColor);font-size:.9rem;}
.sms-box{background:color-mix(in srgb,currentColor 5%,transparent);border:1px solid color-mix(in srgb,currentColor 20%,transparent);border-left:3px solid #60a5fa;
  border-radius:8px;padding:.9rem 1.1rem;font-size:.88rem;color:color-mix(in srgb, #93c5fd 45%, currentColor);}
.kw-pill{display:inline-block;background:color-mix(in srgb,currentColor 5%,transparent);border:1px solid color-mix(in srgb,currentColor 20%,transparent);
  border-radius:20px;padding:.12rem .5rem;font-size:.7rem;color:color-mix(in srgb, #7ba8d0 45%, currentColor);margin:.12rem;}
.slot-pill{display:inline-block;background:color-mix(in srgb,currentColor 5%,transparent);border:1px solid color-mix(in srgb,currentColor 20%,transparent);
  border-radius:20px;padding:.12rem .5rem;font-size:.7rem;color:color-mix(in srgb, #86efac 45%, currentColor);margin:.12rem;}
.audit-row{padding:.4rem .6rem;border-bottom:1px solid color-mix(in srgb,currentColor 20%,transparent);
  font-size:.78rem;color:color-mix(in srgb,currentColor 78%,transparent);font-family:monospace;}
.audit-hash{color:color-mix(in srgb, #3b6ff5 45%, currentColor);font-size:.7rem;}
.multi-dept{background:color-mix(in srgb,currentColor 5%,transparent);border:1px solid #a78bfa44;border-radius:8px;
  padding:.6rem .9rem;font-size:.85rem;color:color-mix(in srgb, #c4b5fd 45%, currentColor);margin-top:.5rem;}
.stat-num{font-size:1.8rem;font-weight:700;font-family:'Syne',sans-serif;}
.lang-badge{display:inline-block;padding:.18rem .6rem;border-radius:20px;
  font-size:.7rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;}
.flow-step{display:flex;align-items:center;gap:.5rem;padding:.35rem 0;font-size:.82rem;}
.flow-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0;}
section[data-testid="stSidebar"]{border-right:1px solid color-mix(in srgb,currentColor 15%,transparent);}
</style>
""", unsafe_allow_html=True)

# ─── imports ─────────────────────────────────────────────────────────────────
from utils.classifier import classify, DEPT_INFO
from utils.fraud      import screen_call, flag_as_fraud, get_fraud_log
from utils.audit      import (log_call_received, log_classification,
                               log_routing, log_fraud_decision,
                               log_operator_action, get_log, verify_chain)
from utils.urgency    import score as urgency_score

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_audio")

SAMPLES = [
    ("call_1_fight.wav",     "🔴 Fight — English"),
    ("call_2_fire.wav",      "🔴 Fire — English"),
    ("call_3_garbage.wav",   "🟢 Garbage — English"),
    ("call_4_theft.wav",     "🔵 Theft — English"),
    ("call_5_water.wav",     "🟢 Water — English"),
    ("call_6_mr_paani.wav",  "🟢 पाणी नाही — Marathi"),
    ("call_7_mr_kachra.wav", "🟢 कचरा — Marathi"),
    ("call_8_mr_aag.wav",    "🔴 आग — Marathi"),
]

LANG_COLORS = {
    "Marathi":"#f472b6","Hindi":"#fb923c","English":"#60a5fa","Unknown":"#94a3b8"
}
URG_COLORS  = {
    "Critical":"#ef4444","High":"#f59e0b","Medium":"#3b82f6","Low":"#22c55e"
}
CONF_COLORS = {"High":"#34d399","Medium":"#fbbf24","Low":"#f87171"}

# ─── Session state ────────────────────────────────────────────────────────────
_defaults = {
    "result":       None,
    "audio_path":   None,
    "call_history": [],  # list of past result dicts
    "kpi":          {"total":0,"critical":0,"high":0,"fraud_blocked":0,"auto_routed":0},
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── SIDEBAR — Admin / KPIs / Audit ──────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:800;
      color:color-mix(in srgb, #60a5fa 45%, currentColor);padding:.5rem 0 .8rem;letter-spacing:.05em">
      🚨 JanSeva Admin
    </div>""", unsafe_allow_html=True)

    # ── Live KPIs (FR-ADM-01) ────────────────────────────────────────────
    st.markdown('<div class="card-title">📊 Live KPIs</div>', unsafe_allow_html=True)
    kpi = st.session_state.kpi
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="stat-num">{kpi["total"]}</div>'
                    f'<div style="font-size:.72rem;color:color-mix(in srgb,currentColor 78%,transparent)">Total Calls</div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="stat-num" style="color:color-mix(in srgb, #ef4444 45%, currentColor)">{kpi["critical"]}</div>'
                    f'<div style="font-size:.72rem;color:color-mix(in srgb,currentColor 78%,transparent)">Critical</div>',
                    unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-num" style="color:color-mix(in srgb, #f59e0b 45%, currentColor)">{kpi["fraud_blocked"]}</div>'
                    f'<div style="font-size:.72rem;color:color-mix(in srgb,currentColor 78%,transparent)">Fraud Blocked</div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="stat-num" style="color:color-mix(in srgb, #22c55e 45%, currentColor)">{kpi["auto_routed"]}</div>'
                    f'<div style="font-size:.72rem;color:color-mix(in srgb,currentColor 78%,transparent)">Auto-Routed</div>',
                    unsafe_allow_html=True)

    st.markdown("---")

    # ── Routing matrix snapshot (FR-RTE-01) ─────────────────────────────
    st.markdown('<div class="card-title">🗺 Routing Matrix</div>', unsafe_allow_html=True)
    for k, v in DEPT_INFO.items():
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;padding:.25rem 0;'
            f'border-bottom:1px solid color-mix(in srgb,currentColor 20%,transparent);font-size:.78rem;">'
            f'<span>{v["emoji"]} {k}</span>'
            f'<span style="color:color-mix(in srgb, {v["color"]} 45%, currentColor);font-family:monospace">{v["phone"]}</span></div>',
            unsafe_allow_html=True)

    st.markdown("---")

    # ── Audit log (FR-ADM-02/05) ─────────────────────────────────────────
    st.markdown('<div class="card-title">🔒 Audit Log</div>', unsafe_allow_html=True)
    chain_ok = verify_chain()
    st.markdown(
        f'<div style="font-size:.72rem;color:{"#34d399" if chain_ok else "#ef4444"};margin-bottom:.4rem">'
        f'{"✅ Chain intact" if chain_ok else "❌ Chain broken!"}</div>',
        unsafe_allow_html=True)
    for entry in get_log(8):
        st.markdown(
            f'<div class="audit-row">'
            f'[{entry["ts"][11:19]}] <b style="color:color-mix(in srgb, #93c5fd 45%, currentColor)">{entry["action"]}</b>'
            f'<span class="audit-hash"> #{entry["hash"]}</span></div>',
            unsafe_allow_html=True)

    st.markdown("---")

    # ── Fraud log ────────────────────────────────────────────────────────
    st.markdown('<div class="card-title">🛡 Fraud Decisions</div>', unsafe_allow_html=True)
    for fd in get_fraud_log()[:5]:
        color = "#ef4444" if fd.get("is_fraud") else "#f59e0b" if fd.get("risk_level") == "Medium" else "#34d399"
        st.markdown(
            f'<div style="font-size:.72rem;color:color-mix(in srgb, {color} 45%, currentColor);padding:.2rem 0;border-bottom:1px solid #1e2a40">'
            f'{fd.get("action","—")} · score={fd.get("risk_score",0)}</div>',
            unsafe_allow_html=True)

    st.markdown("---")

    # ── Operator flag (FR-FRA-06) ────────────────────────────────────────
    st.markdown('<div class="card-title">🚩 Operator Actions</div>', unsafe_allow_html=True)
    flag_cli = st.text_input("Flag CLI as fraud:", placeholder="e.g. 9876543210", label_visibility="collapsed")
    if st.button("🚩 Blacklist Number", key="flag"):
        if flag_cli:
            flag_as_fraud(flag_cli, "operator_flagged")
            log_operator_action("operator", flag_cli, "manually_blacklisted")
            st.success(f"Flagged: {flag_cli}")

    # ── History ──────────────────────────────────────────────────────────
    if st.session_state.call_history:
        st.markdown("---")
        st.markdown('<div class="card-title">📋 Call History</div>', unsafe_allow_html=True)
        for i, h in enumerate(reversed(st.session_state.call_history[-6:])):
            urg_col = URG_COLORS.get(h.get("urgency","Low"),"#94a3b8")
            st.markdown(
                f'<div style="font-size:.75rem;padding:.3rem 0;border-bottom:1px solid color-mix(in srgb,currentColor 20%,transparent);">'
                f'<span style="color:color-mix(in srgb, {urg_col} 45%, currentColor)">●</span> '
                f'<b>{h.get("ref_no","")}</b><br>'
                f'<span style="color:color-mix(in srgb,currentColor 78%,transparent)">{h.get("dept_label","")} · {h.get("urgency","")}</span></div>',
                unsafe_allow_html=True)

# ─── MAIN CONTENT ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🚨 JanSeva — AI Emergency & Civic Helpline</h1>
  <p>FR-CAL-01 · FR-NLU-02 · FR-URG-01 · FR-FRA-01 · FR-RTE-01 · Multilingual: Hindi · Marathi · English</p>
</div>""", unsafe_allow_html=True)

left, right = st.columns([1, 1.7], gap="large")

# ═══════════════════════════ LEFT PANEL ══════════════════════════════════════
with left:

    # ── Input (FR-CAL-01/02) ─────────────────────────────────────────────
    st.markdown('<div class="card"><div class="card-title">📞 Call Input (FR-CAL-01)</div>', unsafe_allow_html=True)
    input_mode = st.radio("Input", ["📂 Sample Calls","📤 Upload Audio"],
                          horizontal=True, label_visibility="collapsed")

    audio_path = None
    if input_mode == "📂 Sample Calls":
        opts    = {label: fn for fn, label in SAMPLES}
        chosen  = st.selectbox("Select sample:", list(opts.keys()))
        fn      = opts[chosen]
        audio_path = os.path.join(SAMPLE_DIR, fn)
        if os.path.exists(audio_path):
            st.audio(audio_path)
        else:
            st.warning("⚠️ Run `python generate_samples.py` first.")
    else:
        up = st.file_uploader("Upload WAV/MP3", type=["wav","mp3"])
        if up:
            import tempfile
            suf = ".wav" if up.name.endswith(".wav") else ".mp3"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suf)
            tmp.write(up.read()); tmp.flush()
            audio_path = tmp.name
            st.audio(up)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Caller info (FR-LOC-03, FR-FRA-01) ──────────────────────────────
    st.markdown('<div class="card"><div class="card-title">👤 Caller Information</div>', unsafe_allow_html=True)
    cli       = st.text_input("Caller Number (CLI):", value="+91-9876543210", label_visibility="collapsed")
    location  = st.text_input("Location / Landmark:", placeholder="e.g. Near Solapur Railway Station", label_visibility="collapsed")
    consent   = st.checkbox("✅ Caller has given consent to record & process (FR-CAL-07)", value=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Settings ─────────────────────────────────────────────────────────
    with st.expander("⚙️ Settings"):
        model_size = st.select_slider("Whisper model",options=["tiny","base","small"],value="base")
        demo_mode  = st.checkbox("⚡ Demo mode (skip Whisper, use labels)", value=False)
        st.caption("tiny=fastest  base=balanced  small=most accurate")

    # ── Process ──────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    process_btn = st.button("🔍  Process Call", disabled=(audio_path is None or not consent))
    if not consent:
        st.caption("⚠️ Enable consent checkbox to process call (FR-CAL-07)")

    # ── System flow diagram ───────────────────────────────────────────────
    result = st.session_state.result
    st.markdown('<div class="card"><div class="card-title">⚙ System Flow</div>', unsafe_allow_html=True)
    steps = [
        ("FR-CAL-01  Call Reception",        "done" if audio_path else ""),
        ("FR-FRA-01  Fraud Screening",        "done" if result else "active" if audio_path else ""),
        ("FR-NLU-01  Speech → Text (Whisper)","done" if result else ""),
        ("FR-CAL-03  Language Detection",     "done" if result else ""),
        ("FR-NLU-02  Intent Classification",  "done" if result else ""),
        ("FR-URG-01  Urgency Scoring",        "done" if result else ""),
        ("FR-NLU-03  Slot Extraction",        "done" if result else ""),
        ("FR-RTE-01  Department Routing",     "done" if result else ""),
        ("FR-NTF-01  SMS Acknowledgement",    "done" if result else ""),
    ]
    for label, state in steps:
        color  = "#60a5fa" if state == "active" else ("#34d399" if state == "done" else "#2a3a58")
        dot_bg = color if state else "#1e2a40"
        st.markdown(
            f'<div class="flow-step">'
            f'<div class="flow-dot" style="background:{dot_bg}"></div>'
            f'<span style="color:color-mix(in srgb, {color} 45%, currentColor);font-size:.78rem">{label}</span></div>',
            unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════ RIGHT PANEL ══════════════════════════════════════
with right:

    if process_btn and audio_path:
        status_box = st.empty()
        with status_box.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            prog = st.progress(0)
            stat = st.empty()
            ref_no = f"JAN-{time.strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

            # Step 1: Fraud screening (FR-FRA-01/02/03)
            stat.markdown("🛡️ **Screening call for fraud/spam...**")
            prog.progress(10)
            fraud_result = screen_call(cli=cli, transcript="", caller_id=ref_no)
            log_fraud_decision(ref_no, cli, fraud_result["action"], fraud_result["risk_score"])
            log_call_received(cli, ref_no, "detecting...")
            time.sleep(0.3)

            if fraud_result["is_fraud"]:
                prog.progress(100)
                stat.markdown("🚫 **Fraud detected — quarantining call**")
                st.session_state.kpi["fraud_blocked"] += 1
                st.session_state.kpi["total"] += 1
                st.markdown('</div>', unsafe_allow_html=True)
                status_box.empty()

                st.markdown(f"""
                <div class="fraud-box">
                  <div style="font-size:1rem;font-weight:700;margin-bottom:.5rem">
                    🚫 Call Quarantined (FR-FRA-04)
                  </div>
                  <div>CLI: <b>{cli}</b></div>
                  <div>Risk Score: <b>{fraud_result["risk_score"]}</b> / 100</div>
                  <div style="margin-top:.5rem">Evidence:</div>
                  <ul style="margin:.3rem 0 0 1rem">
                    {''.join(f"<li>{e}</li>" for e in fraud_result["evidence"])}
                  </ul>
                  <div style="margin-top:.6rem;font-size:.8rem;color:color-mix(in srgb, #fda4af 45%, currentColor)">
                    Caller has been informed of legal consequences (FR-FRA-04)
                  </div>
                </div>""", unsafe_allow_html=True)
                st.session_state.result = None
                st.stop()

            # Step 2: Transcription (FR-NLU-01)
            original_text = ""
            transcript_text = ""
            detected_lang = "en"
            asr_conf = "N/A"

            if demo_mode:
                stat.markdown("⚡ **Demo mode — loading label...**")
                prog.progress(35)
                label_path = os.path.join(SAMPLE_DIR, "labels.json")
                fn_key = os.path.basename(audio_path)
                if os.path.exists(label_path):
                    with open(label_path, encoding="utf-8") as lf:
                        labels = json.load(lf)
                    transcript_text = labels.get(fn_key, "Demo transcript unavailable.")
                    original_text   = transcript_text
                    detected_lang   = "mr" if "_mr_" in fn_key else "en"
                    asr_conf        = "Demo"
            else:
                stat.markdown("🧠 **Whisper: transcribing + detecting language...**")
                prog.progress(25)
                try:
                    from utils.transcriber import transcribe
                    tr = transcribe(audio_path, model_size=model_size)
                    transcript_text = tr["text"]
                    original_text   = tr.get("original_text", transcript_text)
                    detected_lang   = tr.get("language", "en")
                    asr_conf        = tr.get("asr_confidence", "Unknown")
                    prog.progress(60)
                except Exception as e:
                    st.error(f"❌ Whisper failed: {e}\n\nEnable ⚡ Demo mode in Settings.")
                    st.stop()

            # Append location if entered
            if location:
                transcript_text += f" Location: {location}"

            # Step 3: Classification (FR-NLU-02/03/04)
            stat.markdown("🔍 **Classifying intent + extracting slots...**")
            prog.progress(75)
            time.sleep(0.2)
            result_data = classify(transcript_text, detected_language=detected_lang)

            # Step 4: Urgency scoring (FR-URG-01/02)
            stat.markdown("⚡ **Scoring urgency level...**")
            urg = urgency_score(transcript_text, result_data["department"])
            result_data["urgency"]         = urg["level"]
            result_data["urgency_score"]   = urg["score"]
            result_data["urgency_signals"] = urg["signals"]
            prog.progress(90)

            # Enrich result
            result_data.update({
                "transcript":        transcript_text,
                "original_text":     original_text,
                "detected_lang_code": detected_lang,
                "asr_confidence":    asr_conf,
                "cli":               cli,
                "ref_no":            ref_no,
                "fraud":             fraud_result,
                "location_input":    location,
            })

            # Audit entries (FR-ADM-05)
            log_classification(ref_no, result_data["department"],
                               result_data["urgency"], result_data["confidence"])
            log_routing(ref_no, result_data["department"], result_data["phone"])

            # Update KPIs
            st.session_state.kpi["total"]      += 1
            st.session_state.kpi["auto_routed"] += 1
            if result_data["urgency"] == "Critical":
                st.session_state.kpi["critical"] += 1
            if result_data["urgency"] == "High":
                st.session_state.kpi["high"] = st.session_state.kpi.get("high", 0) + 1

            st.session_state.call_history.append(result_data)

            prog.progress(100)
            stat.markdown("✅ **Complete!**")
            time.sleep(0.3)
            st.markdown('</div>', unsafe_allow_html=True)

        status_box.empty()
        st.session_state.result = result_data

    # ─── RESULTS ─────────────────────────────────────────────────────────────
    if st.session_state.result:
        r          = st.session_state.result
        color      = r["color"]
        lang       = r.get("detected_language","English")
        lang_color = LANG_COLORS.get(lang, "#94a3b8")
        urg        = r.get("urgency","Low")
        urg_color  = URG_COLORS.get(urg,"#94a3b8")

        # ── Ref number + redirect banner ─────────────────────────────────
        st.markdown(
            f'<div style="text-align:center;font-size:.75rem;color:color-mix(in srgb,currentColor 78%,transparent);margin-bottom:.3rem">'
            f'Ref: <b style="color:color-mix(in srgb, #60a5fa 45%, currentColor);font-family:monospace">{r.get("ref_no","")}</b>'
            f'  ·  {r.get("classified_at","")[:19].replace("T"," ")} UTC</div>',
            unsafe_allow_html=True)

        st.markdown(
            f'<div class="redirect-banner" style="background:{color}18;border:2px solid {color}44;">'
            f'{r["emoji"]}  Routing to <span style="color:color-mix(in srgb, {color} 45%, currentColor)">{r["dept_label"]}</span>'
            f'  <span style="font-size:.82rem;opacity:.7">· 📞 {r["phone"]}</span>'
            f'</div>', unsafe_allow_html=True)

        # ── Multi-department alert (FR-RTE-05) ────────────────────────────
        multi = r.get("multi_departments",[])
        if multi:
            icons = {"Fire":"🚒","Police":"🚔","Ambulance":"🚑","Municipal":"🏛️","General":"📋"}
            dept_str = "  +  ".join(f'{icons.get(d,"")}{d}' for d in multi)
            st.markdown(
                f'<div class="multi-dept">⚠️ <b>Multi-Department Alert (FR-RTE-05)</b><br>'
                f'Bridging: {dept_str}</div>',
                unsafe_allow_html=True)

        # ── Urgency + stat cards ──────────────────────────────────────────
        urg_class = f"urg-{urg.lower()}"
        st.markdown(
            f'<div class="{urg_class}" style="margin-bottom:.8rem">'
            f'⚡ Urgency: {urg}  (Score: {r.get("urgency_score",0)}/100)'
            f'  ·  Signals: {", ".join(r.get("urgency_signals",[])[:3]) or "—"}'
            f'<span style="float:right;font-size:.75rem;opacity:.6">FR-URG-01</span></div>',
            unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="card" style="text-align:center;">
              <div class="card-title">Department</div>
              <div style="font-size:1.8rem">{r['emoji']}</div>
              <div style="font-family:'Syne',sans-serif;font-weight:700;color:color-mix(in srgb, {color} 45%, currentColor);font-size:.9rem">
                {r['dept_label']}</div></div>""", unsafe_allow_html=True)
        with c2:
            cc = CONF_COLORS[r["confidence"]]
            st.markdown(f"""
            <div class="card" style="text-align:center;">
              <div class="card-title">NLU Confidence</div>
              <div style="font-size:1.8rem">📊</div>
              <div style="font-family:'Syne',sans-serif;font-weight:700;color:color-mix(in srgb, {cc} 45%, currentColor);font-size:.9rem">
                {r['confidence']}</div></div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="card" style="text-align:center;">
              <div class="card-title">Language (FR-CAL-03)</div>
              <div style="font-size:1.8rem">🌐</div>
              <div class="lang-badge" style="background:{lang_color}22;color:color-mix(in srgb, {lang_color} 45%, currentColor);
                border:1px solid {lang_color}44">{lang}</div>
              <div style="font-size:.7rem;color:color-mix(in srgb,currentColor 78%,transparent);margin-top:.3rem">
                ASR: {r.get("asr_confidence","—")}</div></div>""", unsafe_allow_html=True)

        # ── Transcript (FR-NLU-01/04) ─────────────────────────────────────
        st.markdown('<div class="card"><div class="card-title">📝 Transcript (FR-NLU-01 · FR-NLU-04 code-mixed)</div>',
                    unsafe_allow_html=True)
        orig  = r.get("original_text","")
        trans = r.get("transcript","")
        if orig and orig != trans:
            st.markdown(f'<div class="original-box">🗣️ <b>Original ({lang}):</b><br>"{orig}"</div>',
                        unsafe_allow_html=True)
            st.markdown(f'<div class="transcript-box" style="margin-top:.4rem">🔤 <b>English:</b><br>"{trans}"</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="transcript-box">"{trans}"</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ── Slots + Keywords (FR-NLU-03) ─────────────────────────────────
        col_a, col_b = st.columns([1,2])
        with col_a:
            st.markdown('<div class="card"><div class="card-title">🔑 Keywords + Slots (FR-NLU-03)</div>',
                        unsafe_allow_html=True)
            if r["matched_kw"]:
                pills = "".join(f'<span class="kw-pill">{kw}</span>' for kw in r["matched_kw"])
                st.markdown(f'<div style="margin-bottom:.4rem">{pills}</div>', unsafe_allow_html=True)

            slots = r.get("slots",{})
            if slots:
                st.markdown('<div style="font-size:.7rem;color:color-mix(in srgb,currentColor 78%,transparent);margin:.4rem 0 .2rem">Extracted Slots:</div>',
                            unsafe_allow_html=True)
                for k, v in slots.items():
                    st.markdown(f'<span class="slot-pill">📍 {k}: {v}</span>', unsafe_allow_html=True)

            if r.get("location_input"):
                st.markdown(f'<div style="margin-top:.4rem"><span class="slot-pill">📍 location: {r["location_input"]}</span></div>',
                            unsafe_allow_html=True)

            if not r["matched_kw"] and not slots:
                st.markdown('<span style="color:color-mix(in srgb,currentColor 78%,transparent);font-size:.8rem">No keywords — defaulted to General</span>',
                            unsafe_allow_html=True)
            st.markdown(f'<br><div class="card-title">📋 Service</div>'
                        f'<span style="color:color-mix(in srgb,currentColor 78%,transparent);font-size:.8rem">{r["description"]}</span>',
                        unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Response + TTS (FR-NLU-01 output) ────────────────────────────
        with col_b:
            resp_lang  = r.get("response_lang","English")
            resp_color = LANG_COLORS.get(resp_lang,"#94a3b8")
            st.markdown(
                f'<div class="card"><div class="card-title">🤖 AI Response '
                f'<span class="lang-badge" style="background:{resp_color}22;'
                f'color:color-mix(in srgb, {resp_color} 45%, currentColor);border:1px solid {resp_color}44">{resp_lang}</span></div>',
                unsafe_allow_html=True)
            st.markdown(f'<div class="response-box">{r["response"]}</div>', unsafe_allow_html=True)

            try:
                from gtts import gTTS
                import tempfile
                tts_lang = "mr" if resp_lang=="Marathi" else "hi" if resp_lang=="Hindi" else "en"
                tts = gTTS(text=r["response"], lang=tts_lang, slow=False)
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                tts.save(tmp.name)
                st.audio(open(tmp.name,"rb").read(), format="audio/mp3", autoplay=True)
            except Exception as e:
                st.caption(f"TTS unavailable: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

        # ── SMS Acknowledgement simulation (FR-NTF-01) ────────────────────
        from datetime import datetime as dt
        sms_text = (
            f"JanSeva Alert: Your complaint (Ref: {r.get('ref_no','')}) has been received. "
            f"Dept: {r['dept_label']} | Urgency: {urg} | "
            f"Helpline: {r['phone']}. Thank you."
        )
        st.markdown(
            f'<div class="sms-box"><b>📱 SMS Acknowledgement (FR-NTF-01)</b><br>'
            f'{sms_text}</div>',
            unsafe_allow_html=True)

        # ── Fraud screening result (FR-FRA-01/02) ────────────────────────
        fraud = r.get("fraud",{})
        if fraud and fraud.get("risk_level") != "Low":
            st.markdown(
                f'<div style="margin-top:.6rem;background:#2d1b0022;border:1px solid #f59e0b44;'
                f'border-radius:8px;padding:.7rem 1rem;font-size:.82rem;color:color-mix(in srgb, #fcd34d 45%, currentColor)">'
                f'⚠️ Fraud Screen (FR-FRA-01): Risk={fraud.get("risk_level","Low")} '
                f'(score={fraud.get("risk_score",0)}) · Action: {fraud.get("action","allow")}'
                f'</div>', unsafe_allow_html=True)

        # ── Urgency override (FR-URG-04) ──────────────────────────────────
        st.markdown("---")
        ov_col1, ov_col2 = st.columns([2,1])
        with ov_col1:
            new_urg = st.selectbox("⚡ Override Urgency (FR-URG-04):",
                                   ["Critical","High","Medium","Low"],
                                   index=["Critical","High","Medium","Low"].index(urg),
                                   label_visibility="collapsed")
        with ov_col2:
            if st.button("Apply Override", key="override_urg"):
                st.session_state.result["urgency"] = new_urg
                log_operator_action("operator","call_override",
                                    f"urgency changed to {new_urg}", r.get("ref_no",""))
                st.success(f"Urgency updated to {new_urg}")
                st.rerun()

    else:
        st.markdown("""
        <div class="card" style="text-align:center;padding:3rem 2rem;border-style:dashed;">
          <div style="font-size:2.8rem;margin-bottom:.7rem">🚨</div>
          <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;
            color:color-mix(in srgb,currentColor 78%,transparent);margin-bottom:.4rem">No call processed yet</div>
          <div style="color:color-mix(in srgb,currentColor 78%,transparent);font-size:.85rem">
            Select a sample · fill caller info · click <b>Process Call</b>
          </div>
        </div>""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("""
<div style="text-align:center;color:color-mix(in srgb,currentColor 78%,transparent);font-size:.75rem;padding:.3rem 0 .6rem">
  JanSeva v1.0 · BRD Prototype · FR-CAL · FR-NLU · FR-URG · FR-FRA · FR-RTE · FR-NTF · FR-ADM
</div>""", unsafe_allow_html=True)
