"""
FirstVoice - Premium Version
Full UI + Interview Flow
"""

import streamlit as st
from datetime import datetime
from streamlit_mic_recorder import mic_recorder

from voice_input import (
    transcribe,
    get_whisper_model
)

from conversation import (
    INTERVIEW_QUESTIONS,
    generate_legal_summary,
    get_next_steps
)

from pdf_gen import generate_dossier_pdf


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="FirstVoice",
    page_icon="🎙️",
    layout="centered"
)


# --------------------------------------------------
# CUSTOM STYLING
# --------------------------------------------------

st.markdown("""
<style>
.big-title {
    font-size: 42px;
    font-weight: 700;
    text-align: center;
}
.subtitle {
    text-align: center;
    font-size: 18px;
    opacity: 0.8;
}
.center-btn {
    display: flex;
    justify-content: center;
    margin-top: 30px;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "screen" not in st.session_state:
    st.session_state.screen = "welcome"

if "step" not in st.session_state:
    st.session_state.step = 0

if "responses" not in st.session_state:
    st.session_state.responses = []


# --------------------------------------------------
# LOAD MODEL
# --------------------------------------------------

@st.cache_resource
def load_model():
    return get_whisper_model()

model = load_model()


# ==================================================
# SCREEN 1 — WELCOME
# ==================================================

def show_welcome():
    st.markdown('<div class="big-title">🎙️ FirstVoice</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Social AI · Identity For All</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Speak your truth. We document it safely.</div>', unsafe_allow_html=True)

    st.markdown("<div class='center-btn'>", unsafe_allow_html=True)
    if st.button("Begin Your Story"):
        st.session_state.screen = "language"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ==================================================
# SCREEN 2 — LANGUAGE SELECT
# ==================================================

def show_language():
    st.title("Choose Your Language")

    language = st.selectbox(
        "Select language for interview:",
        ["English", "Tamil"]
    )

    if st.button("Continue"):
        st.session_state.language = language
        st.session_state.screen = "interview"
        st.rerun()


# ==================================================
# SCREEN 3 — INTERVIEW
# ==================================================

def show_interview():
    st.title("Interview Session")

    if st.session_state.step >= len(INTERVIEW_QUESTIONS):
        st.session_state.screen = "processing"
        st.rerun()

    question = INTERVIEW_QUESTIONS[st.session_state.step]

    st.subheader(f"Question {st.session_state.step + 1}")
    st.write(question["english"])

    audio = mic_recorder(
        start_prompt="🎙️ Start Recording",
        stop_prompt="⏹️ Stop Recording",
        key=f"mic_{st.session_state.step}"
    )

    if audio:
        with st.spinner("Transcribing..."):
            text = transcribe(audio["bytes"], model)

        if text:
            st.success("Recorded:")
            st.write(text)

            st.session_state.responses.append(text)
            st.session_state.step += 1
            st.rerun()


# ==================================================
# SCREEN 4 — PROCESSING
# ==================================================

def show_processing():
    st.title("Processing Your Story...")
    st.info("Please wait while we prepare your legal summary.")

    with st.spinner("Generating summary..."):
        summary = generate_legal_summary(st.session_state.responses)
        next_steps = get_next_steps(st.session_state.responses)

    st.session_state.summary = summary
    st.session_state.next_steps = next_steps
    st.session_state.screen = "dossier"
    st.rerun()


# ==================================================
# SCREEN 5 — DOSSIER
# ==================================================

def show_dossier():
    st.title("📄 Your Legal Dossier")

    st.subheader("Summary")
    st.write(st.session_state.summary)

    st.subheader("Recommended Next Steps")
    st.write(st.session_state.next_steps)

    pdf_file = generate_dossier_pdf(
        responses=st.session_state.responses,
        summary=st.session_state.summary,
        next_steps=st.session_state.next_steps,
        timestamp=datetime.now()
    )

    st.download_button(
        label="⬇️ Download PDF",
        data=pdf_file,
        file_name="FirstVoice_Dossier.pdf",
        mime="application/pdf"
    )

    if st.button("Start New Interview"):
        st.session_state.screen = "welcome"
        st.session_state.step = 0
        st.session_state.responses = []
        st.rerun()


# --------------------------------------------------
# ROUTER
# --------------------------------------------------

if st.session_state.screen == "welcome":
    show_welcome()

elif st.session_state.screen == "language":
    show_language()

elif st.session_state.screen == "interview":
    show_interview()

elif st.session_state.screen == "processing":
    show_processing()

elif st.session_state.screen == "dossier":
    show_dossier()
