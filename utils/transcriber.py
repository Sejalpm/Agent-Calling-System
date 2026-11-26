"""
utils/transcriber.py
BRD: FR-NLU-01 (≥92% WA), FR-NLU-04 (code-mixed), FR-CAL-03 (language detect)
Whisper: multilingual, auto language detection, proper source-lang translation.
"""
import os, re

_model_cache = {}

_LANG_MAP = {
    "mr":"mr","hi":"hi","en":"en","te":"te",
    "ta":"ta","kn":"kn","gu":"gu","pa":"pa",
}
_NEEDS_TRANSLATION = {"mr","hi","te","ta","kn","gu","pa"}


def load_whisper(model_size="base"):
    if model_size not in _model_cache:
        import whisper
        _model_cache[model_size] = whisper.load_model(model_size)
    return _model_cache[model_size]


def transcribe(audio_path: str, model_size: str = "base") -> dict:
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    import subprocess
    try:
        subprocess.run(["ffmpeg","-version"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception:
        raise RuntimeError("ffmpeg not found. Install from https://ffmpeg.org or run with Demo Mode.")

    model  = load_whisper(model_size)
    result = model.transcribe(audio_path, fp16=False, temperature=0.0)

    original_text = result["text"].strip()
    detected_lang = result.get("language","en")
    confidence    = _asr_confidence(result)

    translated_text = original_text
    if detected_lang in _NEEDS_TRANSLATION:
        translated_text = _translate(original_text, detected_lang)

    return {
        "text":          translated_text,
        "original_text": original_text,
        "language":      detected_lang,
        "source":        "whisper",
        "asr_confidence": confidence,
    }


def _translate(text: str, source_lang: str) -> str:
    """Explicit source lang → no misdetection of Marathi as Hindi."""
    try:
        from deep_translator import GoogleTranslator
        t = GoogleTranslator(
            source=_LANG_MAP.get(source_lang, source_lang),
            target="en"
        ).translate(text)
        return t or text
    except Exception:
        return text


def _asr_confidence(result: dict) -> str:
    """Estimate ASR confidence from segment avg_logprob."""
    segs = result.get("segments", [])
    if not segs:
        return "Unknown"
    avg = sum(s.get("avg_logprob", -1) for s in segs) / len(segs)
    if avg > -0.3:   return "High"
    elif avg > -0.6: return "Medium"
    else:            return "Low"
