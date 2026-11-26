"""
generate_samples.py  —  Generate sample WAV files including Marathi

Creates 8 sample calls: 5 English + 3 Marathi
Run once before launching the app.
"""
import os, json, wave, struct, math

SAMPLE_DIR = "sample_audio"
os.makedirs(SAMPLE_DIR, exist_ok=True)

SAMPLES = [
    # English samples
    ("call_1_fight.wav",     "en", "There is a fight happening in my area. Someone is attacking people. Please send police immediately."),
    ("call_2_fire.wav",      "en", "There is a fire in my building. The flames are spreading fast. Please send the fire brigade."),
    ("call_3_garbage.wav",   "en", "Garbage is not collected in our street for two weeks. It smells very bad. Please send someone."),
    ("call_4_theft.wav",     "en", "Someone is stealing bikes from the parking lot near my house. I can see the thief right now."),
    ("call_5_water.wav",     "en", "There is no water supply in my area since yesterday. Please fix the water problem urgently."),

    # Marathi samples — real sentences a citizen would say
    ("call_6_mr_paani.wav",  "mr", "आमच्या भागात तीन दिवसांपासून पाणी नाही. पाणीपुरवठा बंद आहे. कृपया लवकर दुरुस्ती करा."),
    ("call_7_mr_kachra.wav", "mr", "आमच्या रस्त्यावर पाच दिवसांपासून कचरा उचलला नाही. खूप दुर्गंधी येत आहे. कृपया कचरागाडी पाठवा."),
    ("call_8_mr_aag.wav",    "mr", "इमारतीला आग लागली आहे. धूर येत आहे. लोक अडकले आहेत. कृपया अग्निशमन दल पाठवा."),
]

LABELS = {fn: {"text": txt, "lang": lang} for fn, lang, txt in SAMPLES}


def save_labels():
    path = os.path.join(SAMPLE_DIR, "labels.json")
    # Save simple text labels for demo mode
    simple = {fn: info["text"] for fn, info in LABELS.items()}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(simple, f, indent=2, ensure_ascii=False)

    # Save full labels with language info
    full_path = os.path.join(SAMPLE_DIR, "labels_full.json")
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(LABELS, f, indent=2, ensure_ascii=False)
    print("  ✓ labels.json + labels_full.json saved")


def _tone_wav(path, freq=440, duration=2, rate=16000):
    samples = [int(32767 * 0.15 * math.sin(2 * math.pi * freq * i / rate))
               for i in range(rate * duration)]
    with wave.open(path, "w") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def generate_gtts():
    """Use gTTS with correct language per sample."""
    from gtts import gTTS
    for fn, lang, txt in SAMPLES:
        p = os.path.join(SAMPLE_DIR, fn)
        if os.path.exists(p):
            print(f"  ✓ exists: {fn}")
            continue
        try:
            # Use correct language — 'mr' for Marathi, 'en' for English
            tts = gTTS(text=txt, lang=lang, slow=False)
            mp3 = p.replace(".wav", ".mp3")
            tts.save(mp3)
            # Convert mp3 -> wav
            try:
                from pydub import AudioSegment
                AudioSegment.from_mp3(mp3).export(p, format="wav")
                os.remove(mp3)
            except Exception:
                # If pydub not available, keep mp3 renamed as wav (Streamlit can still play it)
                os.rename(mp3, p)
            print(f"  ✓ created [{lang}]: {fn}")
        except Exception as e:
            print(f"  ✗ gTTS failed for {fn}: {e}")
            _tone_wav(p)
            print(f"  ⚠ tone placeholder: {fn}")


def generate_pyttsx3():
    """Offline TTS — only supports English well."""
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty("rate", 145)
    for fn, lang, txt in SAMPLES:
        if lang != "en":
            continue   # pyttsx3 can't do Marathi
        p = os.path.join(SAMPLE_DIR, fn)
        if os.path.exists(p):
            print(f"  ✓ exists: {fn}")
            continue
        engine.save_to_file(txt, p)
        engine.runAndWait()
        print(f"  ✓ created [en]: {fn}")


if __name__ == "__main__":
    print("\n🎙  Generating sample audio files...\n")
    save_labels()

    # Try gTTS first (supports Marathi)
    try:
        generate_gtts()
        print("\n✅  Done with gTTS!\n")
    except ImportError:
        print("  gTTS not found, trying pyttsx3...")
        try:
            generate_pyttsx3()
            # Create tone placeholders for Marathi files
            for fn, lang, _ in SAMPLES:
                if lang == "mr":
                    p = os.path.join(SAMPLE_DIR, fn)
                    if not os.path.exists(p):
                        _tone_wav(p)
                        print(f"  ⚠ tone placeholder (Marathi): {fn}")
        except Exception as e:
            print(f"  pyttsx3 failed: {e}")
            print("  Creating tone placeholders for all files...")
            for fn, _, _ in SAMPLES:
                p = os.path.join(SAMPLE_DIR, fn)
                if not os.path.exists(p):
                    _tone_wav(p)
