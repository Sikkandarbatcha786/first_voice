"""
FirstVoice - AI Brain (conversation.py)
----------------------------------------
Handles:
  - Guided 8-question identity interview
  - Sending answers to Groq LLM
  - Extracting legally useful information
  - Building the user_data profile (always in English)
  - Translating questions to user's language
Free: Uses Groq API (free tier - 14,400 requests/day)
"""

import os
import streamlit as st
from groq import Groq

# ─────────────────────────────────────────────
# SETUP GROQ CLIENT (Cloud & Local safe)
# ─────────────────────────────────────────────

def get_groq_client():
    api_key = None

    # 1️⃣ Streamlit Cloud first
    try:
        if "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass

    # 2️⃣ Fallback to local .env
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "❌ GROQ_API_KEY not found in Streamlit secrets or environment."
        )

    return Groq(api_key=api_key)


# ─────────────────────────────────────────────
# THE 8 INTERVIEW QUESTIONS
# ─────────────────────────────────────────────

INTERVIEW_QUESTIONS = [
    {"id": 1, "english": "What is your name, and what do people in your village or community call you?",
     "purpose": "Extract full name, nicknames, community name", "evidence_type": "name_identity", "icon": "👤"},
    {"id": 2, "english": "Can you describe the village or place where you were born or grew up? Tell me about any rivers, temples, mountains, or landmarks you remember.",
     "purpose": "Extract location, geographic markers, region", "evidence_type": "location_history", "icon": "🏡"},
    {"id": 3, "english": "Who are the elders or respected people in your community who have known you since you were a child? What are their names?",
     "purpose": "Extract community witnesses, elder names", "evidence_type": "community_ties", "icon": "👴"},
    {"id": 4, "english": "Do you remember any festivals, seasons, or important events from your childhood? What did your family do during these times?",
     "purpose": "Extract cultural markers, seasonal references, traditions", "evidence_type": "cultural_proof", "icon": "🎋"},
    {"id": 5, "english": "What is your mother's name and your father's name? What work did your family do to earn a living?",
     "purpose": "Extract family record, parental names, occupation", "evidence_type": "family_record", "icon": "🌾"},
    {"id": 6, "english": "Have you ever gone to school, a clinic, a temple, or a government office? Do you remember anyone there who knew you by name?",
     "purpose": "Extract institutional interactions, named witnesses", "evidence_type": "institutional_contact", "icon": "🏫"},
    {"id": 7, "english": "Do you have any physical marks, scars, or features that people in your community would recognize you by? Or any objects — a photograph, letter, or item — that connects you to your family or village?",
     "purpose": "Extract physical identifiers, tangible evidence", "evidence_type": "physical_evidence", "icon": "🔍"},
    {"id": 8, "english": "Is there anything else important about who you are, where you come from, or your family that you would like to tell us?",
     "purpose": "Catch additional evidence, closing statement", "evidence_type": "additional_evidence", "icon": "📜"},
]

# ─────────────────────────────────────────────
# HARDCODED NATURAL TRANSLATIONS
# ─────────────────────────────────────────────

HARDCODED_TRANSLATIONS = {
    "Tamil": {1: "உங்கள் பெயர் என்ன? உங்கள் கிராமத்தில் உங்களை எப்படி அழைக்கிறார்கள்?", 2: "நீங்கள் எந்த ஊரில் பிறந்தீர்கள் அல்லது வளர்ந்தீர்கள்? அங்கே ஆறு, கோயில், மலை அல்லது நினைவில் இருக்கும் ஏதாவது இடம் இருக்கா?", 3: "உங்கள் கிராமத்தில் உங்களை சிறுவயதிலிருந்தே அறிந்த பெரியவர்கள் யார்? அவர்கள் பெயர் என்ன?", 4: "சிறுவயதில் கொண்டாடிய திருவிழாக்கள் அல்லது முக்கியமான நிகழ்வுகள் என்னென்ன? அந்த நேரத்தில் உங்கள் குடும்பம் என்ன செய்யும்?", 5: "உங்கள் அம்மா பெயர் என்ன? அப்பா பெயர் என்ன? உங்கள் குடும்பம் என்ன தொழில் செய்தது?", 6: "நீங்கள் பள்ளி, மருத்துவமனை, கோயில் அல்லது அரசு அலுவலகம் போனது இருக்கா? அங்கே உங்களை பெயர் சொல்லி அழைத்தவர்கள் யாராவது இருக்கார்களா?", 7: "உங்கள் உடம்பில் ஏதாவது வடு, தழும்பு அல்லது அடையாளம் இருக்கா? அல்லது புகைப்படம், கடிதம் போன்று குடும்பத்தோடு தொடர்புடைய ஏதாவது பொருள் இருக்கா?", 8: "உங்களைப் பற்றியோ உங்கள் குடும்பத்தைப் பற்றியோ உங்கள் ஊரைப் பற்றியோ வேறு ஏதாவது சொல்ல விரும்புகிறீர்களா?"},
    "Hindi": {1: "आपका नाम क्या है? आपके गाँव में लोग आपको किस नाम से बुलाते हैं?", 2: "आप किस गाँव में पैदा हुए या पले-बढ़े? वहाँ कोई नदी, मंदिर, पहाड़ या कोई खास जगह है जो आपको याद हो?", 3: "आपके गाँव में कौन से बुजुर्ग हैं जो आपको बचपन से जानते हैं? उनका नाम क्या है?", 4: "बचपन में कौन से त्योहार मनाते थे? उस वक्त आपका परिवार क्या करता था?", 5: "आपकी माँ का नाम क्या है? पिताजी का नाम क्या है? घर में क्या काम करते थे?", 6: "क्या आप कभी स्कूल, अस्पताल, मंदिर या सरकारी दफ्तर गए? वहाँ कोई था जो आपको नाम से जानता था?", 7: "क्या आपके शरीर पर कोई निशान या दाग है? या कोई फोटो, चिट्ठी जो आपके परिवार या गाँव से जुड़ी हो?", 8: "अपने बारे में, अपने परिवार के बारे में या अपने गाँव के बारे में कुछ और बताना चाहते हैं?"}
    # Add other languages as before...
}

# ─────────────────────────────────────────────
# TRANSLATE QUESTION TO USER'S LANGUAGE
# ─────────────────────────────────────────────

def translate_question(question_english, target_language, client=None):
    if target_language.lower() == "english":
        return question_english

    # Find question id
    q_id = next((q["id"] for q in INTERVIEW_QUESTIONS if q["english"] == question_english), None)

    # Hardcoded translation first
    if q_id and target_language in HARDCODED_TRANSLATIONS:
        translation = HARDCODED_TRANSLATIONS[target_language].get(q_id)
        if translation:
            return translation
        else:
            print(f"⚠️ Warning: Hardcoded translation for Q{q_id} missing in {target_language}")

    # Fallback to Groq LLM
    if client is None:
        client = get_groq_client()

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": f"You are a native {target_language} speaker. Translate naturally and warmly. Return only the translated question."},
                {"role": "user", "content": question_english}
            ],
            max_tokens=200,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Translation error for {target_language}: {e}")
        return question_english

# ─────────────────────────────────────────────
# EXTRACT FROM ANSWER
# ─────────────────────────────────────────────

def extract_from_answer(question, answer, evidence_type, client=None):
    if not answer or not answer.strip():
        return {"facts": [], "confidence": 0, "raw": ""}

    if client is None:
        client = get_groq_client()

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Extract legal facts from answer in ENGLISH only."},
                {"role": "user", "content": f"Question: {question}\nAnswer: {answer}\nEvidence type: {evidence_type}"}
            ],
            max_tokens=300,
            temperature=0.2,
        )
        raw_response = response.choices[0].message.content.strip()
        return _parse_extraction(raw_response, answer)
    except Exception as e:
        print(f"⚠️ Extraction failed for evidence type '{evidence_type}': {e}")
        return {"facts": [answer], "confidence": 30, "raw": answer}

def _parse_extraction(raw_response, original_answer):
    facts = []
    confidence = 30
    summary = ""
    for line in raw_response.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            facts.append(line[2:])
        elif line.startswith("CONFIDENCE:"):
            try:
                confidence = int(line.replace("CONFIDENCE:", "").strip())
            except:
                confidence = 40
        elif line.startswith("SUMMARY:"):
            summary = line.replace("SUMMARY:", "").strip()
    return {"facts": facts if facts else [original_answer], "confidence": min(max(confidence, 0), 100), "summary": summary, "raw": original_answer}

# ─────────────────────────────────────────────
# FULL INTERVIEW CONDUCTOR
# ─────────────────────────────────────────────

def conduct_interview(answers_dict, language="English"):
    client = get_groq_client()
    user_data = {"language": language, "answers": {}, "extracted": {}, "evidence_scores": {}, "overall_confidence": 0, "name": "Unknown", "location": "Unknown", "community": "Unknown", "family": "Unknown"}

    total_confidence = 0
    answered_count = 0

    for q in INTERVIEW_QUESTIONS:
        q_id = q["id"]
        answer = answers_dict.get(q_id, "").strip()
        if not answer:
            user_data["evidence_scores"][q["evidence_type"]] = 0
            continue
        extraction = extract_from_answer(q["english"], answer, q["evidence_type"], client)
        user_data["answers"][q_id] = answer
        user_data["extracted"][q["evidence_type"]] = extraction
        user_data["evidence_scores"][q["evidence_type"]] = extraction["confidence"]
        total_confidence += extraction["confidence"]
        answered_count += 1

    if answered_count > 0:
        user_data["overall_confidence"] = int(total_confidence / answered_count)

    user_data = _extract_key_fields(user_data, answers_dict, client)
    return user_data

def _extract_key_fields(user_data, answers_dict, client):
    all_answers = "\n".join([f"Q{qid}: {ans}" for qid, ans in answers_dict.items() if ans.strip()])
    if not all_answers:
        return user_data
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Extract key identity info in ENGLISH only: NAME, LOCATION, COMMUNITY, FAMILY."},
                {"role": "user", "content": all_answers}
            ],
            max_tokens=200,
            temperature=0.1,
        )
        raw = response.choices[0].message.content.strip()
        for line in raw.split("\n"):
            if line.startswith("NAME:"): user_data["name"] = line.replace("NAME:","").strip()
            elif line.startswith("LOCATION:"): user_data["location"] = line.replace("LOCATION:","").strip()
            elif line.startswith("COMMUNITY:"): user_data["community"] = line.replace("COMMUNITY:","").strip()
            elif line.startswith("FAMILY:"): user_data["family"] = line.replace("FAMILY:","").strip()
    except Exception as e:
        print(f"⚠️ Key field extraction failed: {e}")
    return user_data

# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\nFirstVoice — AI Brain Test\n")
    client = get_groq_client()
    for q in INTERVIEW_QUESTIONS:
        translated = translate_question(q["english"], "Tamil", client)
        print(f"Q{q['id']}: {translated}")
