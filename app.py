"""
FirstVoice - Main App (app.py)
-------------------------------
Full Streamlit UI connecting voice engine,
AI brain, and PDF generator.

Run with: streamlit run app.py
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
    AudioRecorder, transcribe, speak,
    transcribe_uploaded_file, get_whisper_model
)
from conversation import (
    INTERVIEW_QUESTIONS, translate_question,
    conduct_interview, generate_legal_summary, get_next_steps
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
# CUSTOM CSS
# ─────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=Inter:wght@300;400;500&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background: #0a0a0f; }
    .block-container { padding-top: 2rem; max-width: 720px; }
    .fv-title { text-align:center; font-family:'Lora',serif; font-size:3.5rem; color:#f0e8d8; margin-bottom:0; }
    .fv-title span { color:#c9a96e; }
    .fv-tagline { text-align:center; color:#806050; font-size:1.1rem; font-style:italic; margin-bottom:2rem; }
    .fv-card { background:rgba(255,255,255,0.03); border:1px solid rgba(201,169,110,0.2); border-radius:12px; padding:1.5rem; margin-bottom:1rem; }
    .score-high { background:linear-gradient(135deg,#1a3a2a,#2d7a4f); border-radius:12px; padding:1.5rem; text-align:center; }
    .score-mid  { background:linear-gradient(135deg,#3a2a0a,#c47c2b); border-radius:12px; padding:1.5rem; text-align:center; }
    .score-low  { background:linear-gradient(135deg,#3a0a0a,#a83232); border-radius:12px; padding:1.5rem; text-align:center; }
    .q-card { background:rgba(201,169,110,0.05); border-left:3px solid #c9a96e; border-radius:0 8px 8px 0; padding:1rem 1.2rem; margin-bottom:1rem; font-size:1.1rem; color:#f0e8d8; }
    .mic-box { background:rgba(201,169,110,0.05); border:2px dashed rgba(201,169,110,0.3); border-radius:16px; padding:1.5rem; text-align:center; margin-bottom:1rem; }
    .speaking-badge { display:inline-block; background:rgba(74,222,128,0.15); border:1px solid #4ade80; border-radius:20px; padding:4px 14px; font-size:0.75rem; color:#4ade80; letter-spacing:1px; margin-bottom:0.5rem; }
    .stButton > button { background:linear-gradient(135deg,#c9a96e,#a07840) !important; color:#0a0a0f !important; border:none !important; border-radius:50px !important; font-weight:bold !important; padding:0.6rem 2rem !important; font-size:1rem !important; transition:all 0.3s !important; }
    .stButton > button:hover { transform:translateY(-2px) !important; box-shadow:0 6px 20px rgba(201,169,110,0.4) !important; }
    .stProgress > div > div { background:linear-gradient(90deg,#c9a96e,#4ade80) !important; }
    .stTextArea textarea { background:rgba(255,255,255,0.03) !important; border:1px solid rgba(201,169,110,0.3) !important; color:#e8e0d0 !important; border-radius:10px !important; font-family:'Lora',serif !important; }
    .stSelectbox > div > div { background:rgba(255,255,255,0.03) !important; border:1px solid rgba(201,169,110,0.3) !important; color:#e8e0d0 !important; }
    .fv-label { font-size:0.75rem; letter-spacing:2px; color:#c9a96e; text-transform:uppercase; margin-bottom:0.3rem; }
    #MainMenu{visibility:hidden;} footer{visibility:hidden;} header{visibility:hidden;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# LANGUAGES
# ─────────────────────────────────────────────

LANGUAGES = [
    # Major Indian
    "Tamil", "Hindi", "Telugu", "Kannada", "Bengali",
    "Marathi", "Malayalam", "Punjabi", "Odia", "Gujarati",
    "Urdu", "Assamese", "Maithili", "Konkani", "Sindhi",
    # Tribal
    "Gondi", "Bhili", "Santali", "Mundari", "Kurukh",
    "Tulu", "Kodava", "Dogri", "Bodo", "Manipuri",
    "Khasi", "Mizo", "Nagamese",
    # Rural / Regional
    "Chhattisgarhi", "Bundeli", "Rajasthani", "Haryanvi",
    "Magahi", "Angika", "Bajjika", "Awadhi", "Bhojpuri",
    # International
    "English",
]

# gTTS language codes
LANG_TTS = {
    "Tamil": "ta", "Hindi": "hi", "Telugu": "te", "Kannada": "kn",
    "Bengali": "bn", "Marathi": "mr", "Malayalam": "ml", "Punjabi": "pa",
    "Odia": "or", "Gujarati": "gu", "Urdu": "ur", "Assamese": "as",
    "Maithili": "hi", "Konkani": "hi", "Sindhi": "hi",
    "Gondi": "hi", "Bhili": "hi", "Santali": "hi", "Mundari": "hi",
    "Kurukh": "hi", "Tulu": "kn", "Kodava": "kn", "Dogri": "hi",
    "Bodo": "hi", "Manipuri": "bn", "Khasi": "en", "Mizo": "en",
    "Nagamese": "en", "Chhattisgarhi": "hi", "Bundeli": "hi",
    "Rajasthani": "hi", "Haryanvi": "hi", "Magahi": "hi",
    "Angika": "hi", "Bajjika": "hi", "Awadhi": "hi", "Bhojpuri": "hi",
    "English": "en",
}

GREETINGS = {
    "Tamil":    "வணக்கம். நான் FirstVoice. உங்கள் கதையை சொல்லுங்கள். நான் உதவுவேன்.",
    "Hindi":    "नमस्ते। मैं FirstVoice हूँ। आपकी कहानी बताइए। मैं आपकी मदद करूँगा।",
    "Telugu":   "నమస్కారం. నేను FirstVoice. మీ కథ చెప్పండి. నేను సహాయం చేస్తాను.",
    "Kannada":  "ನಮಸ್ಕಾರ. ನಾನು FirstVoice. ನಿಮ್ಮ ಕಥೆ ಹೇಳಿ. ನಾನು ಸಹಾಯ ಮಾಡುತ್ತೇನೆ.",
    "Bengali":  "নমস্কার। আমি FirstVoice। আপনার গল্প বলুন। আমি সাহায্য করব।",
    "Marathi":  "नमस्कार. मी FirstVoice आहे. तुमची कहाणी सांगा. मी मदत करेन.",
    "Malayalam":"നമസ്കാരം. ഞാൻ FirstVoice ആണ്. നിങ്ങളുടെ കഥ പറയൂ. ഞാൻ സഹായിക്കാം.",
    "Punjabi":  "ਸਤ ਸ੍ਰੀ ਅਕਾਲ। ਮੈਂ FirstVoice ਹਾਂ। ਆਪਣੀ ਕਹਾਣੀ ਦੱਸੋ।",
    "Gujarati": "નમસ્તે. હું FirstVoice છું. તમારી વાર્તા કહો.",
    "English":  "Hello. I am FirstVoice. I will help you prove who you are. Let us begin.",
}

CONFIRMATIONS = {
    "Tamil":    "நன்றி. அடுத்த கேள்விக்கு தயாரா?",
    "Hindi":    "धन्यवाद। अगले सवाल के लिए तैयार हैं?",
    "Telugu":   "ధన్యవాదాలు. తర్వాత ప్రశ్నకు సిద్ధంగా ఉన్నారా?",
    "Kannada":  "ಧನ್ಯವಾದ. ಮುಂದಿನ ಪ್ರಶ್ನೆಗೆ ತಯಾರಿದ್ದೀರಾ?",
    "Bengali":  "ধন্যবাদ। পরের প্রশ্নের জন্য প্রস্তুত?",
    "Marathi":  "धन्यवाद. पुढच्या प्रश्नासाठी तयार आहात का?",
    "Malayalam":"നന്ദി. അടുത്ത ചോദ്യത്തിന് തയ്യാറാണോ?",
    "Punjabi":  "ਧੰਨਵਾਦ। ਅਗਲੇ ਸਵਾਲ ਲਈ ਤਿਆਰ ਹੋ?",
    "Gujarati": "આભાર. આગળના સવાલ માટે તૈયાર છો?",
    "English":  "Thank you. Ready for the next question?",
}

FINAL_MSG = {
    "Tamil":    "நன்றி. உங்கள் அடையாள ஆவணம் தயாராகிறது.",
    "Hindi":    "धन्यवाद। आपका पहचान दस्तावेज़ तैयार हो रहा है।",
    "Telugu":   "ధన్యవాదాలు. మీ గుర్తింపు పత్రం తయారవుతోంది.",
    "Kannada":  "ಧನ್ಯವಾದ. ನಿಮ್ಮ ಗುರುತಿನ ದಾಖಲೆ ತಯಾರಾಗುತ್ತಿದೆ.",
    "Bengali":  "ধন্যবাদ। আপনার পরিচয় নথি তৈরি হচ্ছে।",
    "Marathi":  "धन्यवाद. तुमचे ओळखपत्र तयार होत आहे.",
    "Malayalam":"നന്ദി. നിങ്ങളുടെ തിരിച്ചറിയൽ രേഖ തയ്യാറാകുന്നു.",
    "Punjabi":  "ਧੰਨਵਾਦ। ਤੁਹਾਡਾ ਪਛਾਣ ਦਸਤਾਵੇਜ਼ ਤਿਆਰ ਹੋ ਰਿਹਾ ਹੈ।",
    "Gujarati": "આભાર. તમારો ઓળખ દસ્તાવેજ તૈયાર થઈ રહ્યો છે.",
    "English":  "Thank you. Your identity document is being prepared now.",
}


# ─────────────────────────────────────────────
# TTS HELPER
# ─────────────────────────────────────────────

def make_audio(text, language="English"):
    lang_code = LANG_TTS.get(language, "en")
    try:
        tts = gTTS(text=text, lang=lang_code, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except Exception as e:
        print(f"TTS error: {e}")
        return None

def play_voice(text, language="English"):
    audio_bytes = make_audio(text, language)
    if audio_bytes:
        st.markdown(
            f"<div class='speaking-badge'>🔊 SPEAKING · {language.upper()}</div>",
            unsafe_allow_html=True
        )
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)


# ─────────────────────────────────────────────
# MIC HELPER
# ─────────────────────────────────────────────

def process_mic_audio(audio_bytes):
    tmp = tempfile.NamedTemporaryFile(
        suffix=".wav", delete=False, dir=tempfile.gettempdir()
    )
    tmp.write(audio_bytes)
    tmp.close()
    result = transcribe(tmp.name)
    try:
        os.remove(tmp.name)
    except Exception:
        pass
    return result


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

def init_state():
    defaults = {
        "screen":               "welcome",
        "language":             None,
        "current_q":            0,
        "answers":              {},
        "translated_questions": {},
        "user_data":            {},
        "current_transcript":   "",
        "q_spoken":             set(),
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_state()


# ─────────────────────────────────────────────
# SCORE HELPERS
# ─────────────────────────────────────────────

def score_color_hex(score):
    if score >= 75: return "#4ade80"
    if score >= 50: return "#fbbf24"
    return "#f87171"

def score_class(score):
    if score >= 75: return "score-high"
    if score >= 50: return "score-mid"
    return "score-low"

def score_label(score):
    if score >= 75: return "STRONG EVIDENCE"
    if score >= 50: return "MODERATE EVIDENCE"
    return "PRELIMINARY EVIDENCE"


# ─────────────────────────────────────────────
# SCREEN: WELCOME
# ─────────────────────────────────────────────

def show_welcome():
    st.markdown("""
        <div style='text-align:center; padding:2rem 0 1rem;'>
            <div style='font-size:4rem; margin-bottom:1rem;'>🌿</div>
            <div style='font-size:0.75rem; letter-spacing:6px; color:#c9a96e; margin-bottom:0.5rem;'>
                SOCIAL AI · IDENTITY FOR ALL
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<h1 class='fv-title'>First<span>Voice</span></h1>", unsafe_allow_html=True)
    st.markdown("<p class='fv-tagline'>If you can speak, you exist.</p>", unsafe_allow_html=True)

    st.markdown("""
    <div class='fv-card' style='text-align:center;'>
        <p style='color:#a09080; font-size:1rem; line-height:1.8; margin:0;'>
            400 million people worldwide have no birth certificate, no ID, no legal existence.<br>
            They cannot access hospitals, open bank accounts, vote, or prove who they are.<br><br>
            <strong style='color:#c9a96e;'>FirstVoice changes that — using only their voice.</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div style='text-align:center; color:#504030;'>🎙️<br><small>Voice First</small></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='text-align:center; color:#504030;'>🌐<br><small>35+ Languages</small></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div style='text-align:center; color:#504030;'>⚖️<br><small>Legal Grade</small></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn = st.columns([1, 2, 1])[1]
    with col_btn:
        if st.button("Begin Your Story →", use_container_width=True):
            st.session_state.screen = "language"
            st.rerun()


# ─────────────────────────────────────────────
# SCREEN: LANGUAGE DETECTION
# ─────────────────────────────────────────────

def show_language():
    st.markdown("<div style='text-align:center; color:#c9a96e; font-size:0.75rem; letter-spacing:4px; margin-bottom:0.5rem;'>STEP 1 OF 3</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; font-weight:normal; color:#f0e8d8;'>Speak Your Language</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#706050; margin-bottom:1.5rem;'>Press the button and speak 2-3 sentences — say your name and where you are from. We will detect your language and respond in it.</p>", unsafe_allow_html=True)

    st.markdown("""
    <div class='mic-box'>
        <div style='font-size:3rem; margin-bottom:0.5rem;'>🎙️</div>
        <p style='color:#c9a96e; margin:0 0 0.3rem;'>Press the button and speak</p>
        <p style='color:#504030; font-size:0.85rem; margin:0;'>Speak 2-3 sentences for accurate language detection</p>
    </div>
    """, unsafe_allow_html=True)

    audio = mic_recorder(
        start_prompt="🎙️  Press Here and Speak",
        stop_prompt="⏹  Stop Recording",
        just_once=True,
        use_container_width=True,
        key="lang_mic"
    )

    if audio and audio.get("bytes"):
        with st.spinner("🔍 Detecting your language..."):
            try:
                result = process_mic_audio(audio["bytes"])
                detected = result["language_name"]
                text = result["text"]
                st.session_state.language = detected

                quote_html = f'<div style="font-size:0.85rem; color:#806050; font-style:italic; margin-top:0.3rem;">&ldquo;{text}&rdquo;</div>' if text else ""

                st.markdown(f"""
                <div style='text-align:center; background:rgba(74,222,128,0.08);
                    border:1px solid #4ade80; border-radius:12px; padding:1.5rem; margin:1rem 0;'>
                    <div style='font-size:0.7rem; letter-spacing:3px; color:#4ade80; margin-bottom:0.5rem;'>
                        ✅ LANGUAGE DETECTED
                    </div>
                    <div style='font-size:2.2rem; color:#f0e8d8; margin:0.3rem 0;'>
                        {detected}
                    </div>
                    {quote_html}
                </div>
                """, unsafe_allow_html=True)

                # App speaks back in detected language
                greeting = GREETINGS.get(
                    detected,
                    f"Hello. I am FirstVoice. I detected {detected}. Let us continue."
                )
                play_voice(greeting, detected)

            except Exception as e:
                st.error(f"Could not detect language: {e}")

    # Manual fallback
    st.markdown("<div style='text-align:center; color:#403020; margin:1.2rem 0 0.8rem; font-size:0.85rem;'>— or select your language manually —</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        manual = st.selectbox(
            "Select language",
            LANGUAGES,
            label_visibility="collapsed",
            key="manual_lang_select"
        )
        if st.button("Use this language", use_container_width=True):
            st.session_state.language = manual
            play_voice(GREETINGS.get(manual, "Hello. I am FirstVoice. Let us continue."), manual)
            st.rerun()

    # Continue button
    current_lang = st.session_state.get("language")
    if current_lang:
        st.markdown(f"""
        <div style='text-align:center; color:#4ade80; font-size:0.9rem; margin:1rem 0 0.5rem;'>
            ✅ Ready in <strong>{current_lang}</strong>
        </div>
        """, unsafe_allow_html=True)

        col_btn = st.columns([1, 2, 1])[1]
        with col_btn:
            if st.button(f"Continue in {current_lang} →", use_container_width=True):
                with st.spinner("Preparing your interview..."):
                    try:
                        from conversation import get_groq_client
                        client = get_groq_client()
                        for q in INTERVIEW_QUESTIONS:
                            translated = translate_question(q["english"], current_lang, client)
                            st.session_state.translated_questions[q["id"]] = translated
                    except Exception:
                        for q in INTERVIEW_QUESTIONS:
                            st.session_state.translated_questions[q["id"]] = q["english"]
                st.session_state.screen = "interview"
                st.rerun()


# ─────────────────────────────────────────────
# SCREEN: INTERVIEW
# ─────────────────────────────────────────────

def show_interview():
    current_q_idx = st.session_state.current_q
    q = INTERVIEW_QUESTIONS[current_q_idx]
    total = len(INTERVIEW_QUESTIONS)
    lang = st.session_state.language or "English"

    # Progress
    st.markdown(f"<div style='text-align:center; color:#c9a96e; font-size:0.75rem; letter-spacing:4px; margin-bottom:0.5rem;'>STEP 2 OF 3 · QUESTION {current_q_idx + 1} OF {total}</div>", unsafe_allow_html=True)
    st.progress((current_q_idx + 1) / total)
    st.markdown("<br>", unsafe_allow_html=True)

    # Question
    translated_q = st.session_state.translated_questions.get(q["id"], q["english"])

    # App speaks question once
    spoken_key = f"spoken_q_{q['id']}"
    if spoken_key not in st.session_state.get("q_spoken", set()):
        play_voice(translated_q, lang)
        if "q_spoken" not in st.session_state:
            st.session_state.q_spoken = set()
        st.session_state.q_spoken.add(spoken_key)

    st.markdown(f"""
    <div class='q-card'>
        <span style='font-size:1.5rem;'>{q['icon']}</span><br><br>
        {translated_q}
    </div>
    """, unsafe_allow_html=True)

    # Get existing answer (from session state — already saved answer takes priority)
    existing_answer = st.session_state.answers.get(q["id"], "")

    # Real-time mic
    st.markdown("<div class='fv-label'>🎙️ Speak Your Answer</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='mic-box' style='padding:1.2rem;'>
        <p style='color:#806050; font-size:0.85rem; margin:0 0 0.8rem;'>
            Press the button and speak in your language
        </p>
    """, unsafe_allow_html=True)

    audio = mic_recorder(
        start_prompt="🎙️  Press to Speak",
        stop_prompt="⏹  Stop",
        just_once=True,
        use_container_width=True,
        key=f"mic_q_{q['id']}"
    )

    st.markdown("</div>", unsafe_allow_html=True)

    if audio and audio.get("bytes"):
        with st.spinner("🔍 Transcribing..."):
            try:
                result = process_mic_audio(audio["bytes"])
                spoken_text = result["text"]
                if spoken_text.strip():
                    # ── KEY FIX: save answer to session state immediately ──
                    st.session_state.answers[q["id"]] = spoken_text
                    st.session_state.current_transcript = spoken_text
                    existing_answer = spoken_text
                    st.success(f"✅ Heard: {spoken_text}")

                    # App confirms in user's language
                    confirmation = CONFIRMATIONS.get(lang, "Thank you. Ready for the next question?")
                    play_voice(confirmation, lang)

                    # Rerun so text area and Next button update immediately
                    st.rerun()

            except Exception as e:
                st.error(f"Transcription error: {e}")

    # Text fallback — shows transcribed text or lets user type
    st.markdown("<div class='fv-label' style='margin-top:1rem;'>Or Type Your Answer</div>", unsafe_allow_html=True)
    answer = st.text_area(
        "Answer",
        value=existing_answer,
        placeholder="Your spoken answer will appear here, or type directly...",
        height=110,
        label_visibility="collapsed",
        key=f"answer_text_{q['id']}"
    )

    # If user types something, save it too
    if answer and answer != existing_answer:
        st.session_state.answers[q["id"]] = answer

    # Navigation
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    # Use session state answer for button enable check (not text area value)
    saved_answer = st.session_state.answers.get(q["id"], "")

    with col1:
        if current_q_idx > 0:
            if st.button("← Back", use_container_width=True):
                st.session_state.current_transcript = ""
                st.session_state.current_q -= 1
                st.rerun()

    with col2:
        btn_label = "Next Question →" if current_q_idx < total - 1 else "Build My Dossier →"
        if st.button(btn_label, use_container_width=True, disabled=not saved_answer.strip()):
            st.session_state.current_transcript = ""
            if current_q_idx < total - 1:
                st.session_state.current_q += 1
                st.rerun()
            else:
                # App says final message
                final_msg = FINAL_MSG.get(lang, "Thank you. Your identity document is being prepared.")
                play_voice(final_msg, lang)
                time.sleep(1)
                st.session_state.screen = "processing"
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Skip this question"):
        st.session_state.current_transcript = ""
        st.session_state.current_q = min(current_q_idx + 1, total - 1)
        st.rerun()


# ─────────────────────────────────────────────
# SCREEN: PROCESSING
# ─────────────────────────────────────────────

def show_processing():
    st.markdown("<div style='font-size:3rem; text-align:center; margin-top:3rem;'>⚖️</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; font-weight:normal; color:#f0e8d8;'>Building Your Identity Dossier</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#706050;'>AI is analyzing your testimony and scoring your evidence</p>", unsafe_allow_html=True)

    steps = [
        "Analyzing voice testimony...",
        "Extracting location evidence...",
        "Scoring community ties...",
        "Building identity framework...",
        "Writing legal summary...",
        "Generating dossier...",
    ]

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, step in enumerate(steps):
        status_text.markdown(f"<p style='text-align:center; color:#c9a96e;'>⏳ {step}</p>", unsafe_allow_html=True)
        progress_bar.progress((i + 1) / len(steps))
        time.sleep(0.5)

    with st.spinner("Running AI analysis..."):
        try:
            user_data = conduct_interview(
                st.session_state.answers,
                st.session_state.language or "English"
            )
            user_data["legal_summary"] = generate_legal_summary(user_data)
            user_data["next_steps"] = get_next_steps(user_data)
            st.session_state.user_data = user_data
        except Exception as e:
            st.error(f"Processing error: {e}")
            st.session_state.user_data = {
                "name": "Identity Subject",
                "location": "Unknown", "community": "Unknown", "family": "Unknown",
                "language": st.session_state.language or "English",
                "overall_confidence": 50, "evidence_scores": {},
                "answers": st.session_state.answers,
                "legal_summary": "Identity evidence gathered through structured interview.",
                "next_steps": ["Submit to local legal aid authority"],
            }

    status_text.markdown("<p style='text-align:center; color:#4ade80;'>✅ Dossier complete!</p>", unsafe_allow_html=True)
    time.sleep(0.8)
    st.session_state.screen = "dossier"
    st.rerun()


# ─────────────────────────────────────────────
# SCREEN: DOSSIER
# ─────────────────────────────────────────────

def show_dossier():
    ud = st.session_state.user_data
    score = ud.get("overall_confidence", 0)
    lang = st.session_state.language or "English"

    st.markdown("<div style='text-align:center; color:#c9a96e; font-size:0.75rem; letter-spacing:4px; margin-bottom:0.5rem;'>STEP 3 OF 3 · COMPLETE</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; font-weight:normal; color:#f0e8d8;'>Legal Identity Dossier</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:#706050; font-size:0.85rem;'>Generated: {datetime.now().strftime('%d %B %Y')}</p>", unsafe_allow_html=True)

    sl = score_label(score)
    st.markdown(f"""
    <div class='{score_class(score)}' style='margin:1.5rem 0;'>
        <div style='font-size:0.7rem; letter-spacing:3px; color:rgba(255,255,255,0.7); margin-bottom:0.5rem;'>IDENTITY CONFIDENCE SCORE</div>
        <div style='font-size:3.5rem; font-weight:bold; color:white; line-height:1;'>{score}%</div>
        <div style='font-size:0.9rem; color:rgba(255,255,255,0.8); margin-top:0.5rem;'>{sl}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='fv-label' style='margin-top:1.5rem;'>Subject Profile</div>", unsafe_allow_html=True)
    fields = [
        ("Identified Name",    ud.get("name",      "Unknown")),
        ("Location / Region",  ud.get("location",  "Unknown")),
        ("Community Ties",     ud.get("community", "Unknown")),
        ("Family Record",      ud.get("family",    "Unknown")),
        ("Interview Language", ud.get("language",  "Unknown")),
    ]
    st.markdown("<div class='fv-card'>", unsafe_allow_html=True)
    for label, value in fields:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(f"<div class='fv-label'>{label}</div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div style='color:#e8e0d0; font-size:1rem; margin-bottom:0.5rem;'>{value}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='fv-label' style='margin-top:1rem;'>Evidence Breakdown</div>", unsafe_allow_html=True)
    evidence_labels = {
        "name_identity":         ("👤", "Name & Identity"),
        "location_history":      ("📍", "Location History"),
        "community_ties":        ("🤝", "Community Ties"),
        "cultural_proof":        ("🎋", "Cultural Proof"),
        "family_record":         ("🌾", "Family Record"),
        "institutional_contact": ("🏫", "Institutional Contact"),
        "physical_evidence":     ("🔍", "Physical Evidence"),
        "additional_evidence":   ("📜", "Additional Evidence"),
    }
    ev_scores = ud.get("evidence_scores", {})
    st.markdown("<div class='fv-card'>", unsafe_allow_html=True)
    for key, (icon, label) in evidence_labels.items():
        s = ev_scores.get(key, 0)
        c1, c2, c3 = st.columns([3, 1, 4])
        with c1:
            st.markdown(f"<div style='color:#d0c8b8; font-size:0.9rem; padding-top:2px;'>{icon} {label}</div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div style='color:{score_color_hex(s)}; font-weight:bold;'>{s}%</div>", unsafe_allow_html=True)
        with c3:
            st.progress(s / 100)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='fv-label' style='margin-top:1rem;'>⚖️ Legal Assessment</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='fv-card' style='border-color:rgba(201,169,110,0.3);'>
        <p style='color:#d0c8b8; font-style:italic; line-height:1.8; margin:0;'>{ud.get('legal_summary', '')}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='fv-label' style='margin-top:1rem;'>Recommended Next Steps</div>", unsafe_allow_html=True)
    st.markdown("<div class='fv-card'>", unsafe_allow_html=True)
    for i, step in enumerate(ud.get("next_steps", []), 1):
        st.markdown(f"""
        <div style='display:flex; gap:12px; align-items:flex-start; margin-bottom:10px;'>
            <div style='width:24px; height:24px; border-radius:50%; background:linear-gradient(135deg,#c9a96e,#a07840);
                display:flex; align-items:center; justify-content:center;
                font-size:12px; color:#0a0a0f; font-weight:bold; flex-shrink:0;'>{i}</div>
            <div style='color:#d0c8b8; font-size:0.9rem; line-height:1.6; padding-top:2px;'>{step}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📄 Download Legal Dossier", use_container_width=True):
            with st.spinner("Generating PDF..."):
                try:
                    pdf_path = generate_dossier_pdf(ud)
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    st.download_button(
                        label="⬇️ Click to Download PDF",
                        data=pdf_bytes,
                        file_name=f"firstvoice_{ud.get('name','dossier').replace(' ','_')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    os.remove(pdf_path)
                except Exception as e:
                    st.error(f"PDF error: {e}")

    with col2:
        if st.button("🔄 Start New Interview", use_container_width=True):
            for key in ["screen", "language", "current_q", "answers",
                        "translated_questions", "user_data",
                        "current_transcript", "q_spoken"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

def show_sidebar():
    with st.sidebar:
        st.markdown("### 🤝 NGO Dashboard")
        st.markdown("---")
        st.markdown("**Active Cases:** 0")
        st.markdown("**Completed:** 0")
        st.markdown("**Pending Review:** 0")
        st.markdown("---")
        st.markdown("**Supported Languages**")
        for lang in LANGUAGES:
            st.markdown(f"• {lang}")
        st.markdown("---")
        st.markdown("<small style='color:#504030;'>FirstVoice v1.0 · Built for the voiceless</small>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────

show_sidebar()

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