"""
FirstVoice - Voice Engine (voice_input.py)
------------------------------------------
Handles:
  - Recording audio from microphone
  - Transcribing speech using Whisper (runs locally, free)
  - Detecting language automatically
  - Speaking responses back using gTTS

Windows compatible. No internet needed for Whisper.
"""

import os
import time
import tempfile
import threading
import numpy as np
import sounddevice as sd
import soundfile as sf
import whisper
from gtts import gTTS


# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

SAMPLE_RATE = 16000       # Whisper works best at 16kHz
CHANNELS = 1              # Mono audio
WHISPER_MODEL = "base"    # tiny=fastest, base=balanced, small=accurate

# Language codes for gTTS (speaking back to user)
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
# LOAD WHISPER MODEL (once at startup)
# ─────────────────────────────────────────────

_whisper_model = None

def get_whisper_model():
    """Load Whisper model once and reuse."""
    global _whisper_model
    if _whisper_model is None:
        print(f"🔄 Loading Whisper '{WHISPER_MODEL}' model...")
        _whisper_model = whisper.load_model(WHISPER_MODEL)
        print("✅ Whisper model ready.")
    return _whisper_model


# ─────────────────────────────────────────────
# RECORDING
# ─────────────────────────────────────────────

class AudioRecorder:
    """
    Records audio from mic until stopped.

    Usage:
        recorder = AudioRecorder()
        recorder.start()
        time.sleep(5)
        path = recorder.stop()
    """

    def __init__(self):
        self.recording = False
        self.audio_data = []
        self.thread = None

    def start(self):
        self.recording = True
        self.audio_data = []
        self.thread = threading.Thread(target=self._record)
        self.thread.start()
        print("🎙️  Recording... (call .stop() to finish)")

    def _record(self):
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32"
        ) as stream:
            while self.recording:
                chunk, _ = stream.read(1024)
                self.audio_data.append(chunk)

    def stop(self):
        """Stop and save to WAV. Returns file path."""
        self.recording = False
        if self.thread:
            self.thread.join()

        if not self.audio_data:
            print("⚠️  No audio recorded.")
            return None

        audio_array = np.concatenate(self.audio_data, axis=0)

        tmp = tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False,
            dir=tempfile.gettempdir()
        )
        sf.write(tmp.name, audio_array, SAMPLE_RATE)
        print(f"✅ Audio saved: {tmp.name}")
        return tmp.name


def record_for_seconds(seconds=6):
    """Record for fixed duration. Returns file path."""
    recorder = AudioRecorder()
    recorder.start()
    for i in range(seconds, 0, -1):
        print(f"   ⏱️  {i}s...")
        time.sleep(1)
    return recorder.stop()


# ─────────────────────────────────────────────
# TRANSCRIPTION
# ─────────────────────────────────────────────

def transcribe(audio_path, language=None):
    """
    Transcribe audio file using Whisper.

    Args:
        audio_path : path to .wav file
        language   : hint e.g. "ta", "hi" — or None for auto-detect

    Returns dict:
        text          : transcribed string
        language      : detected code e.g. "ta"
        language_name : readable e.g. "Tamil"
    """
    if not audio_path or not os.path.exists(audio_path):
        return {"text": "", "language": "en", "language_name": "English"}

    model = get_whisper_model()
    print("🔍 Transcribing...")

    options = {}
    if language:
        options["language"] = language

    result = model.transcribe(audio_path, **options)

    text          = result["text"].strip()
    detected_lang = result.get("language", "en")
    lang_name     = _code_to_name(detected_lang)

    print(f"📝 [{lang_name}] {text}")

    try:
        os.remove(audio_path)
    except Exception:
        pass

    return {
        "text":          text,
        "language":      detected_lang,
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
# TEXT TO SPEECH
# ─────────────────────────────────────────────

def speak(text, language_name="english"):
    if not text:
        return
    lang_code = GTTS_LANGUAGE_MAP.get(language_name.lower(), "en")
    print(f"🔊 Speaking [{language_name}]: {text[:60]}...")
    try:
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tmp = tempfile.NamedTemporaryFile(
            suffix=".mp3", delete=False, dir=tempfile.gettempdir()
        )
        tts.save(tmp.name)
        os.system(f'start /wait wmplayer "{tmp.name}"')
        try:
            os.remove(tmp.name)
        except:
            pass
    except Exception as e:
        print(f"⚠️ Speech error: {e}")

# ─────────────────────────────────────────────
# MAIN PIPELINE — listen() 
# ─────────────────────────────────────────────

def listen(duration=8, language=None):
    """
    Full pipeline: record mic → transcribe → return result.

    Args:
        duration : seconds to record
        language : language hint or None for auto-detect

    Returns dict: text, language, language_name
    """
    print(f"\n🎙️  Listening for {duration} seconds...")
    audio_path = record_for_seconds(duration)
    if not audio_path:
        return {"text": "", "language": "en", "language_name": "English"}
    return transcribe(audio_path, language)


# ─────────────────────────────────────────────
# STREAMLIT HELPERS
# ─────────────────────────────────────────────

def transcribe_uploaded_file(uploaded_file):
    """
    For Streamlit: transcribe a file uploaded via st.file_uploader.

    Args:
        uploaded_file : Streamlit UploadedFile object

    Returns dict: text, language, language_name
    """
    tmp = tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False,
        dir=tempfile.gettempdir()
    )
    tmp.write(uploaded_file.read())
    tmp.close()
    return transcribe(tmp.name)


# ─────────────────────────────────────────────
# TEST — python voice_input.py
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  FirstVoice — Voice Engine Test  ")
    print("=" * 50)

    # Test 1: TTS
    print("\n[TEST 1] Speaking in English and Tamil")
    speak("Hello. I am FirstVoice. I will help you prove who you are.", "english")
    speak("வணக்கம். நான் FirstVoice. உங்கள் கதையை சொல்லுங்கள்.", "tamil")

    # Test 2: Record + Transcribe
    print("\n[TEST 2] Speak anything — I will transcribe it.")
    print("You have 6 seconds. Speak now...")
    result = listen(duration=6)

    print("\n── RESULT ──────────────────")
    print(f"  Text     : {result['text']}")
    print(f"  Language : {result['language_name']}")
    print("────────────────────────────")
    print("✅ Voice engine is working!\n")