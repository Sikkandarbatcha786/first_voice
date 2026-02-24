"""
FirstVoice - Main App
Streamlit Cloud Safe Version
"""

import streamlit as st
from datetime import datetime
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
    generate_legal_summary,
    get_next_steps
)

from pdf_gen import generate_dossier_pdf


# ---------------------------
# PAGE CONFIG
# ---------------------------

st.set_page_config(
    page_title="FirstVoice",
    page_icon="🎙️",
    layout="centered"
)

st.title("🎙️ FirstVoice")
st.markdown("Speak your truth. We document it safely.")


# ---------------------------
# SESSION STATE
# ---------------------------

if "step" not in st.session_state:
    st.session_state.step = 0

if "responses" not in st.session_state:
    st.session_state.responses = []

if "completed" not in st.session_state:
    st.session_state.completed = False


# ---------------------------
# LOAD WHISPER MODEL
# ---------------------------

model = get_whisper_model()


# ---------------------------
# INTERVIEW FLOW
# ---------------------------

if not st.session_state.completed:

    question = INTERVIEW_QUESTIONS[st.session_state.step]

    st.subheader(f"Question {st.session_state.step + 1}")
    st.write(question)

    # 🎤 MIC RECORDING
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

            if st.session_state.step >= len(INTERVIEW_QUESTIONS):
                st.session_state.completed = True

            st.rerun()

else:
    # ---------------------------
    # FINAL SUMMARY
    # ---------------------------

    st.success("Interview Completed")

    with st.spinner("Generating legal summary..."):
        summary = generate_legal_summary(st.session_state.responses)
        next_steps = get_next_steps(st.session_state.responses)

    st.subheader("📄 Legal Summary")
    st.write(summary)

    st.subheader("🧭 Recommended Next Steps")
    st.write(next_steps)

    # ---------------------------
    # GENERATE PDF
    # ---------------------------

    pdf_file = generate_dossier_pdf(
        responses=st.session_state.responses,
        summary=summary,
        next_steps=next_steps,
        timestamp=datetime.now()
    )

    st.download_button(
        label="⬇️ Download Legal Dossier PDF",
        data=pdf_file,
        file_name="FirstVoice_Dossier.pdf",
        mime="application/pdf"
    )

    if st.button("🔁 Start Over"):
        st.session_state.step = 0
        st.session_state.responses = []
        st.session_state.completed = False
        st.rerun()
