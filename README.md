# 📞 AI Call Complaint Routing System

A fully free, local demo that simulates an emergency call centre:

- 🎙️ **Speech → Text** via OpenAI Whisper (offline)
- 🔍 **Classification** into Police / Fire / General
- 🖥️ **Streamlit Dashboard** with live results

---

## 📁 Project Structure

```
ai_call_routing/
├── app.py                  ← Main Streamlit app
├── generate_samples.py     ← Creates 5 sample WAV files
├── requirements.txt
├── README.md
├── sample_audio/
│   ├── call_1_fight.wav
│   ├── call_2_fire.wav
│   ├── call_3_garbage.wav
│   ├── call_4_theft.wav
│   ├── call_5_water.wav
│   └── labels.json         ← Pre-set transcripts for demo mode
└── utils/
    ├── __init__.py
    ├── transcriber.py      ← Whisper wrapper
    └── classifier.py       ← Keyword classification logic
```

---

## 🚀 Setup & Run

### Step 1 — Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### Step 2 — Install dependencies
```bash
pip install streamlit openai-whisper torch pyttsx3
```
> **Note:** `torch` is large (~2 GB). Be patient on first install.

### Step 3 — Generate sample audio files
```bash
python generate_samples.py
```
This creates 5 `.wav` files in `sample_audio/`.

### Step 4 — Run the app
```bash
streamlit run app.py
```
Open your browser at **http://localhost:8501**

---

## ⚡ Quick Demo (no Whisper needed)

If you haven't installed Whisper yet:

1. Run `python generate_samples.py` (creates `labels.json`)
2. Launch the app: `streamlit run app.py`
3. In **⚙️ Whisper Model Settings**, tick **"Demo mode"**
4. Select a sample call and click **Process Call**

The app uses pre-set transcripts instead of Whisper — perfect for a quick walkthrough.

---

## 🗂️ Sample Calls & Expected Results

| File | Complaint | Department |
|------|-----------|------------|
| call_1_fight.wav | "There is a fight happening in my area" | 🚔 Police |
| call_2_fire.wav  | "There is a fire in my building" | 🚒 Fire Department |
| call_3_garbage.wav | "Garbage is not collected" | 🏛️ General Services |
| call_4_theft.wav | "Someone is stealing bikes" | 🚔 Police |
| call_5_water.wav | "Water problem in my area" | 🏛️ General Services |

---

## 🔑 Classification Logic

```
Text → lowercase
  ├── Contains fire/flame/smoke/explosion? → Fire Department
  ├── Contains fight/steal/theft/gun/crime? → Police Department
  └── Everything else → General Services
```

Keywords are defined in `utils/classifier.py` — easy to extend.

---

## 🧠 Whisper Model Sizes

| Size  | RAM   | Speed  | Accuracy |
|-------|-------|--------|----------|
| tiny  | ~1 GB | Fast   | Basic    |
| base  | ~1 GB | Good   | Good ✅  |
| small | ~2 GB | Slower | Better   |

`base` is recommended for demos.

---

## 💡 Tips

- **First run downloads Whisper model** (~150 MB for base) — needs internet once.
- After that, everything runs **100% offline**.
- Upload your own `.wav` / `.mp3` files to test custom complaints.
- Add keywords in `utils/classifier.py` to improve accuracy.
