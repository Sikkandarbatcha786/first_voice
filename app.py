"""
FirstVoice - Main App (app.py)
Full Premium Version - Cloud Safe
"""

import os
import io
import time
import tempfile
import streamlit as st
from datetime import datetime
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder

from voice_input import (
    transcribe,
    speak,
    transcribe_uploaded_file,
    get_whisper_model
)

from conversation import (
    INTERVIEW_QUESTIONS,
    translate_question,
    conduct_interview,
    generate_legal_summary,
    get_next_steps
)

from pdf_gen import generate_dossier_pdf


# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="FirstVoice",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ─────────────────────────────────────────────
# CACHE WHISPER MODEL (CLOUD SAFE)
# ─────────────────────────────────────────────

@st.cache_resource
def load_whisper():
    try:
        return get_whisper_model()
    except Exception:
        return None

WHISPER_MODEL = load_whisper()


# ─────────────────────────────────────────────
# CUSTOM CSS (UNCHANGED)
# ─────────────────────────────────────────────

st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background: #0a0a0f; }
    .block-container { padding-top: 2rem; max-width: 720px; }
    .fv-title { text-align:center; font-size:3.5rem; color:#f0e8d8; }
    .fv-title span { color:#c9a96e; }
    .fv-tagline { text-align:center; color:#806050; font-size:1.1rem; font-style:italic; margin-bottom:2rem; }
    .fv-card { background:rgba(255,255,255,0.03); border:1px solid rgba(201,169,110,0.2); border-radius:12px; padding:1.5rem; margin-bottom:1rem; }
    .q-card { background:rgba(201,169,110,0.05); border-left:3px solid #c9a96e; border-radius:0 8px 8px 0; padding:1rem 1.2rem; margin-bottom:1rem; font-size:1.1rem; color:#f0e8d8; }
    .mic-box { background:rgba(201,169,110,0.05); border:2px dashed rgba(201,169,110,0.3); border-radius:16px; padding:1.5rem; text-align:center; margin-bottom:1rem; }
    .stButton > button { background:linear-gradient(135deg,#c9a96e,#a07840) !important; color:#0a0a0f !important; border:none !important; border-radius:50px !important; font-weight:bold !important; }
    #MainMenu{visibility:hidden;} footer{visibility:hidden;} header{visibility:hidden;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SAFE TRANSCRIBE WRAPPER
# ─────────────────────────────────────────────

def safe_transcribe(path):
    try:
        return transcribe(path)
    except TypeError:
        if WHISPER_MODEL:
            return transcribe(path, WHISPER_MODEL)
        raise


def process_mic_audio(audio_bytes):
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.write(audio_bytes)
    tmp.close()

    try:
        result = safe_transcribe(tmp.name)
    finally:
        try:
            os.remove(tmp.name)
        except Exception:
            pass

    return result


# ─────────────────────────────────────────────
# SESSION STATE INIT (UNCHANGED)
# ─────────────────────────────────────────────

def init_state():
    defaults = {
        "screen": "welcome",
        "language": None,
        "current_q": 0,
        "answers": {},
        "translated_questions": {},
        "user_data": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─────────────────────────────────────────────
# WELCOME SCREEN (UNCHANGED DESIGN)
# ─────────────────────────────────────────────

def show_welcome():
    st.markdown("<h1 class='fv-title'>First<span>Voice</span></h1>", unsafe_allow_html=True)
    st.markdown("<p class='fv-tagline'>If you can speak, you exist.</p>", unsafe_allow_html=True)

    if st.button("Begin Your Story →", use_container_width=True):
        st.session_state.screen = "language"
        st.rerun()


# ─────────────────────────────────────────────
# LANGUAGE SCREEN (SAFE GROQ)
# ─────────────────────────────────────────────

def show_language():
    st.title("Speak Your Language")

    audio = mic_recorder(
        start_prompt="🎙️ Press and Speak",
        stop_prompt="⏹ Stop",
        just_once=True
    )

    if audio and audio.get("bytes"):
        try:
            result = process_mic_audio(audio["bytes"])
            detected = result.get("language_name", "English")
            st.session_state.language = detected
            st.success(f"Detected: {detected}")
        except Exception as e:
            st.error(f"Language detection failed: {e}")

    if st.button("Continue"):
        st.session_state.screen = "interview"
        st.rerun()


# ─────────────────────────────────────────────
# INTERVIEW (UNCHANGED FLOW)
# ─────────────────────────────────────────────

def show_interview():
    idx = st.session_state.current_q
    questions = INTERVIEW_QUESTIONS
    total = len(questions)

    q = questions[idx]
    st.subheader(f"Question {idx+1} of {total}")
    st.markdown(f"<div class='q-card'>{q['english']}</div>", unsafe_allow_html=True)

    audio = mic_recorder(
        start_prompt="🎙️ Speak",
        stop_prompt="⏹ Stop",
        just_once=True,
        key=f"mic_{idx}"
    )

    if audio and audio.get("bytes"):
        try:
            result = process_mic_audio(audio["bytes"])
            text = result.get("text", "")
            if text:
                st.session_state.answers[q["id"]] = text
                st.success(text)
                st.rerun()
        except Exception as e:
            st.error(f"Transcription error: {e}")

    answer = st.text_area("Your Answer", value=st.session_state.answers.get(q["id"], ""))

    if st.button("Next →", disabled=not answer.strip()):
        st.session_state.answers[q["id"]] = answer
        if idx < total - 1:
            st.session_state.current_q += 1
        else:
            st.session_state.screen = "processing"
        st.rerun()


# ─────────────────────────────────────────────
# PROCESSING (SAFE AI CALL)
# ─────────────────────────────────────────────

def show_processing():
    st.title("Building Your Dossier...")
    st.progress(0.5)

    try:
        user_data = conduct_interview(
            st.session_state.answers,
            st.session_state.language or "English"
        )
        user_data["legal_summary"] = generate_legal_summary(user_data)
        user_data["next_steps"] = get_next_steps(user_data)
        st.session_state.user_data = user_data
    except Exception:
        st.session_state.user_data = {
            "name": "Identity Subject",
            "overall_confidence": 50,
            "legal_summary": "AI summary unavailable.",
            "next_steps": ["Submit to local authority"],
        }

    st.session_state.screen = "dossier"
    st.rerun()


# ─────────────────────────────────────────────
# DOSSIER (SAFE PDF)
# ─────────────────────────────────────────────

def show_dossier():
    ud = st.session_state.user_data

    st.title("Legal Identity Dossier")
    st.write(ud.get("legal_summary", ""))

    if st.button("Download PDF"):
        try:
            pdf_path = generate_dossier_pdf(ud)
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            st.download_button(
                "⬇️ Click to Download",
                pdf_bytes,
                file_name="firstvoice_dossier.pdf",
                mime="application/pdf"
            )

            try:
                os.remove(pdf_path)
            except Exception:
                pass

        except Exception as e:
            st.error(f"PDF error: {e}")

    if st.button("Start New Interview"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# ─────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────

screen = st.session_state.screen

if screen == "welcome":
    show_welcome()
elif screen == "language":
    show_language()
elif screen == "interview":
    show_interview()
elif screen == "processing":
    show_processing()
elif screen == "dossier":
    show_dossier()
