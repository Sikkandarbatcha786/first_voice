"""
FirstVoice - Voice Engine (Cloud Version)
-----------------------------------------
Cloud-compatible version for Streamlit deployment.

Handles:
  - Transcribing uploaded audio using Whisper
  - Detecting language automatically
  - Generating speech using gTTS (returns audio file path)
"""

import os
import tempfile
import whisper
from gtts import gTTS


# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

WHISPER_MODEL = "base"   # tiny=fastest | base=balanced | small=better accuracy

GTTS_LANGUAGE_MAP = {
    "tamil":     "ta",
    "hindi":     "hi",
    "telugu":    "te",
    "kannada":   "kn",
    "bengali":   "bn",
    "marathi":   "mr",
    "malayalam": "ml",
    "punjabi":   "pa",
    "odia":      "or",
    "english":   "en",
    "gujarati":  "gu",
    "urdu":      "ur",
}


# ─────────────────────────────────────────────
# LOAD WHISPER MODEL (once)
# ─────────────────────────────────────────────

_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        print(f"🔄 Loading Whisper '{WHISPER_MODEL}' model...")
        _whisper_model = whisper.load_model(WHISPER_MODEL)
        print("✅ Whisper model ready.")
    return _whisper_model


# ─────────────────────────────────────────────
# TRANSCRIPTION
# ─────────────────────────────────────────────

def transcribe(audio_path, language=None):
    """
    Transcribe audio file using Whisper.
    Returns dict: text, language, language_name
    """

    if not audio_path or not os.path.exists(audio_path):
        return {"text": "", "language": "en", "language_name": "English"}

    model = get_whisper_model()

    options = {}
    if language:
        options["language"] = language

    result = model.transcribe(audio_path, **options)

    text = result["text"].strip()
    detected_lang = result.get("language", "en")
    lang_name = _code_to_name(detected_lang)

    try:
        os.remove(audio_path)
    except:
        pass

    return {
        "text": text,
        "language": detected_lang,
        "language_name": lang_name,
    }


def _code_to_name(code):
    names = {
        "ta": "Tamil",   "hi": "Hindi",    "te": "Telugu",
        "kn": "Kannada", "bn": "Bengali",  "mr": "Marathi",
        "ml": "Malayalam","pa": "Punjabi", "or": "Odia",
        "en": "English", "gu": "Gujarati", "ur": "Urdu",
    }
    return names.get(code, code.upper())


# ─────────────────────────────────────────────
# STREAMLIT HELPER
# ─────────────────────────────────────────────

def transcribe_uploaded_file(uploaded_file):
    """
    For Streamlit mic or file uploader.
    """
    tmp = tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False
    )
    tmp.write(uploaded_file.read())
    tmp.close()

    return transcribe(tmp.name)


# ─────────────────────────────────────────────
# TEXT TO SPEECH (Cloud Safe)
# ─────────────────────────────────────────────

def speak(text, language_name="english"):
    """
    Returns path to generated MP3 file.
    (Streamlit should use st.audio() to play it)
    """

    if not text:
        return None

    lang_code = GTTS_LANGUAGE_MAP.get(language_name.lower(), "en")

    try:
        tts = gTTS(text=text, lang=lang_code, slow=False)

        tmp = tempfile.NamedTemporaryFile(
            suffix=".mp3",
            delete=False
        )
        tts.save(tmp.name)

        return tmp.name

    except Exception as e:
        print(f"⚠️ Speech error: {e}")
        return None
