"""
FirstVoice - AI Brain (conversation.py)
----------------------------------------
Handles:
  - The guided 8-question identity interview
  - Sending answers to Groq LLM
  - Extracting legally useful information
  - Building the user_data profile (always in English)
  - Translating questions to user's language

Free: Uses Groq API (free tier - 14,400 requests/day)
"""

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


# ─────────────────────────────────────────────
# SETUP GROQ CLIENT
# ─────────────────────────────────────────────

def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "❌ GROQ_API_KEY not found!\n"
            "Please create a .env file in your project folder with:\n"
            "GROQ_API_KEY=your_key_here\n"
            "Get your free key at: https://console.groq.com"
        )
    return Groq(api_key=api_key)


# ─────────────────────────────────────────────
# THE 8 INTERVIEW QUESTIONS
# ─────────────────────────────────────────────

INTERVIEW_QUESTIONS = [
    {
        "id": 1,
        "english": "What is your name, and what do people in your village or community call you?",
        "purpose": "Extract full name, nicknames, community name",
        "evidence_type": "name_identity",
        "icon": "👤"
    },
    {
        "id": 2,
        "english": "Can you describe the village or place where you were born or grew up? Tell me about any rivers, temples, mountains, or landmarks you remember.",
        "purpose": "Extract location, geographic markers, region",
        "evidence_type": "location_history",
        "icon": "🏡"
    },
    {
        "id": 3,
        "english": "Who are the elders or respected people in your community who have known you since you were a child? What are their names?",
        "purpose": "Extract community witnesses, elder names",
        "evidence_type": "community_ties",
        "icon": "👴"
    },
    {
        "id": 4,
        "english": "Do you remember any festivals, seasons, or important events from your childhood? What did your family do during these times?",
        "purpose": "Extract cultural markers, seasonal references, traditions",
        "evidence_type": "cultural_proof",
        "icon": "🎋"
    },
    {
        "id": 5,
        "english": "What is your mother's name and your father's name? What work did your family do to earn a living?",
        "purpose": "Extract family record, parental names, occupation",
        "evidence_type": "family_record",
        "icon": "🌾"
    },
    {
        "id": 6,
        "english": "Have you ever gone to school, a clinic, a temple, or a government office? Do you remember anyone there who knew you by name?",
        "purpose": "Extract institutional interactions, named witnesses",
        "evidence_type": "institutional_contact",
        "icon": "🏫"
    },
    {
        "id": 7,
        "english": "Do you have any physical marks, scars, or features that people in your community would recognize you by? Or any objects — a photograph, letter, or item — that connects you to your family or village?",
        "purpose": "Extract physical identifiers, tangible evidence",
        "evidence_type": "physical_evidence",
        "icon": "🔍"
    },
    {
        "id": 8,
        "english": "Is there anything else important about who you are, where you come from, or your family that you would like to tell us?",
        "purpose": "Catch additional evidence, closing statement",
        "evidence_type": "additional_evidence",
        "icon": "📜"
    },
]


# ─────────────────────────────────────────────
# HARDCODED NATURAL TRANSLATIONS
# Written by hand — not AI generated
# Natural spoken language, not textbook
# ─────────────────────────────────────────────

HARDCODED_TRANSLATIONS = {
    "Tamil": {
        1: "உங்கள் பெயர் என்ன? உங்கள் கிராமத்தில் உங்களை எப்படி அழைக்கிறார்கள்?",
        2: "நீங்கள் எந்த ஊரில் பிறந்தீர்கள் அல்லது வளர்ந்தீர்கள்? அங்கே ஆறு, கோயில், மலை அல்லது நினைவில் இருக்கும் ஏதாவது இடம் இருக்கா?",
        3: "உங்கள் கிராமத்தில் உங்களை சிறுவயதிலிருந்தே அறிந்த பெரியவர்கள் யார்? அவர்கள் பெயர் என்ன?",
        4: "சிறுவயதில் கொண்டாடிய திருவிழாக்கள் அல்லது முக்கியமான நிகழ்வுகள் என்னென்ன? அந்த நேரத்தில் உங்கள் குடும்பம் என்ன செய்யும்?",
        5: "உங்கள் அம்மா பெயர் என்ன? அப்பா பெயர் என்ன? உங்கள் குடும்பம் என்ன தொழில் செய்தது?",
        6: "நீங்கள் பள்ளி, மருத்துவமனை, கோயில் அல்லது அரசு அலுவலகம் போனது இருக்கா? அங்கே உங்களை பெயர் சொல்லி அழைத்தவர்கள் யாராவது இருக்கார்களா?",
        7: "உங்கள் உடம்பில் ஏதாவது வடு, தழும்பு அல்லது அடையாளம் இருக்கா? அல்லது புகைப்படம், கடிதம் போன்று குடும்பத்தோடு தொடர்புடைய ஏதாவது பொருள் இருக்கா?",
        8: "உங்களைப் பற்றியோ உங்கள் குடும்பத்தைப் பற்றியோ உங்கள் ஊரைப் பற்றியோ வேறு ஏதாவது சொல்ல விரும்புகிறீர்களா?",
    },
    "Hindi": {
        1: "आपका नाम क्या है? आपके गाँव में लोग आपको किस नाम से बुलाते हैं?",
        2: "आप किस गाँव में पैदा हुए या पले-बढ़े? वहाँ कोई नदी, मंदिर, पहाड़ या कोई खास जगह है जो आपको याद हो?",
        3: "आपके गाँव में कौन से बुजुर्ग हैं जो आपको बचपन से जानते हैं? उनका नाम क्या है?",
        4: "बचपन में कौन से त्योहार मनाते थे? उस वक्त आपका परिवार क्या करता था?",
        5: "आपकी माँ का नाम क्या है? पिताजी का नाम क्या है? घर में क्या काम करते थे?",
        6: "क्या आप कभी स्कूल, अस्पताल, मंदिर या सरकारी दफ्तर गए? वहाँ कोई था जो आपको नाम से जानता था?",
        7: "क्या आपके शरीर पर कोई निशान या दाग है? या कोई फोटो, चिट्ठी जो आपके परिवार या गाँव से जुड़ी हो?",
        8: "अपने बारे में, अपने परिवार के बारे में या अपने गाँव के बारे में कुछ और बताना चाहते हैं?",
    },
    "Telugu": {
        1: "మీ పేరు ఏమిటి? మీ గ్రామంలో మిమ్మల్ని అందరూ ఏమని పిలుస్తారు?",
        2: "మీరు పుట్టి పెరిగిన ఊరు ఏది? అక్కడ నది, గుడి, కొండ లేదా గుర్తుండే ఏదైనా చోటు ఉందా?",
        3: "మీ గ్రామంలో చిన్నప్పటి నుండి మిమ్మల్ని తెలిసిన పెద్దలు ఎవరు? వారి పేర్లు చెప్పగలరా?",
        4: "చిన్నప్పుడు మీరు జరుపుకున్న పండుగలు ఏవైనా గుర్తున్నాయా? ఆ సమయంలో మీ కుటుంబం ఏం చేసేది?",
        5: "మీ అమ్మ పేరు ఏమిటి? నాన్న పేరు ఏమిటి? మీ కుటుంబం ఏం పని చేసేది?",
        6: "మీరు ఎప్పుడైనా స్కూలు, ఆసుపత్రి, గుడి లేదా సర్కారు కార్యాలయానికి వెళ్ళారా? అక్కడ మిమ్మల్ని పేరుతో తెలిసిన వాళ్ళు ఎవరైనా ఉన్నారా?",
        7: "మీ శరీరంపై ఏదైనా గుర్తు లేదా మచ్చ ఉందా? లేదా కుటుంబానికి సంబంధించిన ఫోటో, ఉత్తరం వంటివి ఏదైనా ఉన్నాయా?",
        8: "మీరు, మీ కుటుంబం లేదా మీ ఊరి గురించి ఇంకేదైనా చెప్పాలనుకుంటున్నారా?",
    },
    "Kannada": {
        1: "ನಿಮ್ಮ ಹೆಸರು ಏನು? ನಿಮ್ಮ ಊರಿನಲ್ಲಿ ನಿಮ್ಮನ್ನು ಎಲ್ಲರೂ ಹೇಗೆ ಕರೆಯುತ್ತಾರೆ?",
        2: "ನೀವು ಹುಟ್ಟಿ ಬೆಳೆದ ಊರು ಯಾವುದು? ಅಲ್ಲಿ ನದಿ, ದೇವಸ್ಥಾನ, ಬೆಟ್ಟ ಅಥವಾ ನೆನಪಿನಲ್ಲಿರುವ ಯಾವುದಾದರೂ ಜಾಗ ಇದೆಯಾ?",
        3: "ನಿಮ್ಮ ಊರಿನಲ್ಲಿ ನಿಮ್ಮನ್ನು ಚಿಕ್ಕಂದಿನಿಂದ ತಿಳಿದಿರುವ ಹಿರಿಯರು ಯಾರು? ಅವರ ಹೆಸರು ಏನು?",
        4: "ಚಿಕ್ಕಂದಿನಲ್ಲಿ ಆಚರಿಸುತ್ತಿದ್ದ ಹಬ್ಬಗಳು ಅಥವಾ ಮುಖ್ಯ ಸಮಯಗಳು ನೆನಪಿದೆಯಾ? ಆ ಸಮಯದಲ್ಲಿ ನಿಮ್ಮ ಕುಟುಂಬ ಏನು ಮಾಡುತ್ತಿತ್ತು?",
        5: "ನಿಮ್ಮ ಅಮ್ಮನ ಹೆಸರು ಏನು? ಅಪ್ಪನ ಹೆಸರು ಏನು? ನಿಮ್ಮ ಕುಟುಂಬ ಏನು ಕೆಲಸ ಮಾಡುತ್ತಿತ್ತು?",
        6: "ನೀವು ಎಂದಾದರೂ ಶಾಲೆ, ಆಸ್ಪತ್ರೆ, ದೇವಸ್ಥಾನ ಅಥವಾ ಸರ್ಕಾರಿ ಕಚೇರಿಗೆ ಹೋಗಿದ್ದೀರಾ? ಅಲ್ಲಿ ನಿಮ್ಮನ್ನು ಹೆಸರಿನಿಂದ ತಿಳಿದಿರುವ ಯಾರಾದರೂ ಇದ್ದಾರಾ?",
        7: "ನಿಮ್ಮ ದೇಹದ ಮೇಲೆ ಯಾವುದಾದರೂ ಗುರುತು ಅಥವಾ ಕಲೆ ಇದೆಯಾ? ಅಥವಾ ಕುಟುಂಬಕ್ಕೆ ಸಂಬಂಧಿಸಿದ ಫೋಟೋ, ಪತ್ರ ಇದೆಯಾ?",
        8: "ನಿಮ್ಮ ಬಗ್ಗೆ, ನಿಮ್ಮ ಕುಟುಂಬದ ಬಗ್ಗೆ ಅಥವಾ ನಿಮ್ಮ ಊರಿನ ಬಗ್ಗೆ ಇನ್ನೂ ಏನಾದರೂ ಹೇಳಲು ಬಯಸುತ್ತೀರಾ?",
    },
    "Malayalam": {
        1: "നിങ്ങളുടെ പേര് എന്താണ്? ഗ്രാമത്തിൽ എല്ലാവരും നിങ്ങളെ എന്ന് വിളിക്കും?",
        2: "നിങ്ങൾ ജനിച്ചു വളർന്ന ഊര് ഏതാണ്? അവിടെ നദി, ക്ഷേത്രം, മല അല്ലെങ്കിൽ ഓർമ്മയിലുള്ള എന്തെങ്കിലും ഇടം ഉണ്ടോ?",
        3: "നിങ്ങളെ ചെറുപ്പം മുതൽ അറിയുന്ന ഗ്രാമത്തിലെ മുതിർന്നവർ ആരാണ്? അവരുടെ പേര് പറയാമോ?",
        4: "ചെറുപ്പത്തിൽ ആഘോഷിച്ചിരുന്ന ഉത്സവങ്ങൾ ഓർമ്മയുണ്ടോ? ആ സമയത്ത് കുടുംബം എന്ത് ചെയ്യും?",
        5: "അമ്മയുടെ പേര് എന്താണ്? അച്ഛന്റെ പേര് എന്താണ്? കുടുംബം എന്ത് ജോലി ചെയ്തിരുന്നു?",
        6: "സ്കൂൾ, ആശുപത്രി, ക്ഷേത്രം അല്ലെങ്കിൽ സർക്കാർ ഓഫീസ് പോയിട്ടുണ്ടോ? അവിടെ നിങ്ങളെ പേരെടുത്ത് അറിയുന്ന ആരെങ്കിലും ഉണ്ടോ?",
        7: "ശരീരത്തിൽ എന്തെങ്കിലും അടയാളം ഉണ്ടോ? കുടുംബവുമായി ബന്ധപ്പെട്ട ഫോട്ടോ, കത്ത് എന്തെങ്കിലും ഉണ്ടോ?",
        8: "നിങ്ങളെക്കുറിച്ചോ കുടുംബത്തെക്കുറിച്ചോ ഊരിനെക്കുറിച്ചോ വേറെ എന്തെങ്കിലും പറയാനുണ്ടോ?",
    },
    "Bengali": {
        1: "আপনার নাম কী? আপনার গ্রামে সবাই আপনাকে কীভাবে ডাকে?",
        2: "আপনি কোন গ্রামে জন্মেছেন বা বড় হয়েছেন? সেখানে কোনো নদী, মন্দির, পাহাড় বা মনে রাখার মতো জায়গা আছে?",
        3: "আপনার গ্রামে কারা আছেন যারা আপনাকে ছোটবেলা থেকে চেনেন? তাদের নাম কী?",
        4: "ছোটবেলায় কোন উৎসব পালন করতেন? সেই সময় পরিবার কী করত?",
        5: "আপনার মায়ের নাম কী? বাবার নাম কী? পরিবার কী কাজ করত?",
        6: "আপনি কি কখনো স্কুল, হাসপাতাল, মন্দির বা সরকারি অফিসে গেছেন? সেখানে কেউ আপনাকে নাম ধরে চিনত?",
        7: "আপনার শরীরে কোনো দাগ বা চিহ্ন আছে? অথবা পরিবারের সাথে সম্পর্কিত কোনো ছবি বা চিঠি আছে?",
        8: "আপনার সম্পর্কে, পরিবার বা গ্রাম সম্পর্কে আর কিছু বলতে চান?",
    },
    "Marathi": {
        1: "तुमचं नाव काय आहे? गावात तुम्हाला कसं बोलावतात?",
        2: "तुम्ही कुठल्या गावात जन्मलात किंवा वाढलात? तिथे नदी, मंदिर, डोंगर किंवा आठवणीतील एखादी जागा आहे का?",
        3: "तुमच्या गावात कोण असे वडीलधारे आहेत जे तुम्हाला लहानपणापासून ओळखतात? त्यांची नावे काय आहेत?",
        4: "लहानपणी कोणते सण साजरे करत होता? त्या वेळी कुटुंब काय करायचं?",
        5: "तुमच्या आईचं नाव काय? बाबांचं नाव काय? कुटुंब काय काम करत होतं?",
        6: "तुम्ही कधी शाळा, दवाखाना, मंदिर किंवा सरकारी कार्यालयात गेलात का? तिथे कोणी तुम्हाला नावाने ओळखत होतं का?",
        7: "तुमच्या शरीरावर एखादी खूण किंवा व्रण आहे का? किंवा कुटुंबाशी संबंधित फोटो, पत्र असं काही आहे का?",
        8: "तुमच्याबद्दल, कुटुंबाबद्दल किंवा गावाबद्दल आणखी काही सांगायचं आहे का?",
    },
    "Punjabi": {
        1: "ਤੁਹਾਡਾ ਨਾਮ ਕੀ ਹੈ? ਪਿੰਡ ਵਿੱਚ ਸਾਰੇ ਤੁਹਾਨੂੰ ਕਿਵੇਂ ਬੁਲਾਉਂਦੇ ਹਨ?",
        2: "ਤੁਸੀਂ ਕਿਸ ਪਿੰਡ ਵਿੱਚ ਜੰਮੇ ਜਾਂ ਵੱਡੇ ਹੋਏ? ਉੱਥੇ ਕੋਈ ਦਰਿਆ, ਮੰਦਰ, ਪਹਾੜ ਜਾਂ ਯਾਦਗਾਰੀ ਜਗ੍ਹਾ ਹੈ?",
        3: "ਤੁਹਾਡੇ ਪਿੰਡ ਵਿੱਚ ਕੋਣ ਬਜ਼ੁਰਗ ਹਨ ਜੋ ਤੁਹਾਨੂੰ ਬਚਪਨ ਤੋਂ ਜਾਣਦੇ ਹਨ? ਉਨ੍ਹਾਂ ਦਾ ਨਾਮ ਕੀ ਹੈ?",
        4: "ਬਚਪਨ ਵਿੱਚ ਕਿਹੜੇ ਤਿਉਹਾਰ ਮਨਾਉਂਦੇ ਸੀ? ਉਸ ਵੇਲੇ ਪਰਿਵਾਰ ਕੀ ਕਰਦਾ ਸੀ?",
        5: "ਤੁਹਾਡੀ ਮਾਂ ਦਾ ਨਾਮ ਕੀ ਹੈ? ਪਿਤਾ ਜੀ ਦਾ ਨਾਮ ਕੀ ਹੈ? ਘਰ ਵਿੱਚ ਕੀ ਕੰਮ ਕਰਦੇ ਸੀ?",
        6: "ਕੀ ਤੁਸੀਂ ਕਦੇ ਸਕੂਲ, ਹਸਪਤਾਲ, ਮੰਦਰ ਜਾਂ ਸਰਕਾਰੀ ਦਫ਼ਤਰ ਗਏ? ਉੱਥੇ ਕੋਈ ਸੀ ਜੋ ਤੁਹਾਨੂੰ ਨਾਮ ਤੋਂ ਜਾਣਦਾ ਸੀ?",
        7: "ਕੀ ਤੁਹਾਡੇ ਸਰੀਰ ਉੱਤੇ ਕੋਈ ਨਿਸ਼ਾਨ ਹੈ? ਜਾਂ ਕੋਈ ਫੋਟੋ, ਚਿੱਠੀ ਜੋ ਪਰਿਵਾਰ ਨਾਲ ਜੁੜੀ ਹੋਵੇ?",
        8: "ਆਪਣੇ ਬਾਰੇ, ਪਰਿਵਾਰ ਬਾਰੇ ਜਾਂ ਪਿੰਡ ਬਾਰੇ ਹੋਰ ਕੁਝ ਦੱਸਣਾ ਚਾਹੁੰਦੇ ਹੋ?",
    },
    "Gujarati": {
        1: "તમારું નામ શું છે? ગામમાં સૌ તમને કેવી રીતે બોલાવે છે?",
        2: "તમે ક્યા ગામમાં જન્મ્યા અથવા મોટા થયા? ત્યાં કોઈ નદી, મંદિર, પહાડ અથવા યાદગાર જગ્યા છે?",
        3: "તમારા ગામમાં કોણ વડીલ છે જે તમને બાળપણથી ઓળખે છે? એમના નામ શું છે?",
        4: "બાળપણમાં કયા તહેવારો ઉજવતા? એ સમયે કુટુંબ શું કરતું?",
        5: "તમારી માનું નામ શું છે? બાપુનું નામ શું છે? કુટુંબ શું કામ કરતું?",
        6: "તમે ક્યારેય શાળા, દવાખાનું, મંદિર અથવા સરકારી ઓફિસ ગયા? ત્યાં કોઈ તમને નામથી ઓળખતું?",
        7: "તમારા શરીર પર કોઈ નિશાન છે? અથવા કુટુંબ સાથે જોડાયેલ ફોટો, પત્ર છે?",
        8: "તમારા વિશે, કુટુંબ વિશે અથવા ગામ વિશે બીજું કંઈ કહેવું છે?",
    },
    "Urdu": {
        1: "آپ کا نام کیا ہے؟ گاؤں میں سب آپ کو کس نام سے بلاتے ہیں؟",
        2: "آپ کس گاؤں میں پیدا ہوئے یا پلے بڑھے؟ وہاں کوئی دریا، مندر، پہاڑ یا یادگار جگہ ہے؟",
        3: "آپ کے گاؤں میں کون بزرگ ہیں جو آپ کو بچپن سے جانتے ہیں؟ ان کا نام کیا ہے؟",
        4: "بچپن میں کون سے تہوار مناتے تھے؟ اس وقت گھر والے کیا کرتے تھے؟",
        5: "آپ کی ماں کا نام کیا ہے؟ ابا کا نام کیا ہے؟ گھر میں کیا کام ہوتا تھا؟",
        6: "کیا آپ کبھی اسکول، اسپتال، مندر یا سرکاری دفتر گئے؟ وہاں کوئی تھا جو آپ کو نام سے جانتا ہو؟",
        7: "کیا آپ کے جسم پر کوئی نشان یا زخم کا داغ ہے؟ یا کوئی تصویر، خط جو آپ کے خاندان سے جڑا ہو؟",
        8: "اپنے بارے میں، خاندان کے بارے میں یا گاؤں کے بارے میں اور کچھ بتانا چاہتے ہیں؟",
    },
}


# ─────────────────────────────────────────────
# TRANSLATE QUESTION TO USER'S LANGUAGE
# ─────────────────────────────────────────────

def translate_question(question_english, target_language, client=None):
    if target_language.lower() == "english":
        return question_english

    # Find question id by matching english text
    q_id = None
    for q in INTERVIEW_QUESTIONS:
        if q["english"] == question_english:
            q_id = q["id"]
            break

    # Use hardcoded natural translation if available
    if q_id and target_language in HARDCODED_TRANSLATIONS:
        hardcoded = HARDCODED_TRANSLATIONS[target_language].get(q_id)
        if hardcoded:
            return hardcoded

    # Fall back to Groq for tribal / other languages
    if client is None:
        client = get_groq_client()
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a native {target_language} speaker from a rural village in India. "
                        f"Translate this question into natural spoken {target_language} — "
                        f"simple, warm, the way a kind community worker would ask face to face. "
                        f"Use everyday words, not formal or textbook language. "
                        f"Return ONLY the translated question, nothing else."
                    )
                },
                {"role": "user", "content": question_english}
            ],
            max_tokens=200,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Translation error: {e}")
        return question_english


# ─────────────────────────────────────────────
# EXTRACT INFORMATION FROM AN ANSWER
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
                {
                    "role": "system",
                    "content": (
                        "You are a legal identity expert helping undocumented people "
                        "establish their identity. The person's answer may be in any "
                        "language — Tamil, Hindi, Urdu, Telugu, or any other. "
                        "You MUST always respond in ENGLISH only. "
                        "Translate all names, places, and details into English. "
                        "Extract specific, verifiable facts from their answers "
                        "that could be used as legal evidence.\n\n"
                        "Respond in this exact format:\n"
                        "FACTS: [list each specific fact in English on a new line starting with -]\n"
                        "CONFIDENCE: [number 0-100 based on how specific and verifiable the answer is]\n"
                        "SUMMARY: [one sentence summary in English of what was established]"
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Question asked: {question}\n"
                        f"Person's answer (may be in any language): {answer}\n"
                        f"Evidence category: {evidence_type}"
                    )
                }
            ],
            max_tokens=300,
            temperature=0.2,
        )

        raw_response = response.choices[0].message.content.strip()
        return _parse_extraction(raw_response, answer)

    except Exception as e:
        print(f"⚠️ Extraction error: {e}")
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
            except ValueError:
                confidence = 40
        elif line.startswith("SUMMARY:"):
            summary = line.replace("SUMMARY:", "").strip()

    return {
        "facts": facts if facts else [original_answer],
        "confidence": min(max(confidence, 0), 100),
        "summary": summary,
        "raw": original_answer,
    }


# ─────────────────────────────────────────────
# FULL INTERVIEW CONDUCTOR
# ─────────────────────────────────────────────

def conduct_interview(answers_dict, language="English"):
    client = get_groq_client()

    user_data = {
        "language": language,
        "answers": {},
        "extracted": {},
        "evidence_scores": {},
        "overall_confidence": 0,
        "name": "Unknown",
        "location": "Unknown",
        "community": "Unknown",
        "family": "Unknown",
    }

    total_confidence = 0
    answered_count = 0

    print("\n🔍 Analyzing all answers...")

    for q in INTERVIEW_QUESTIONS:
        q_id = q["id"]
        answer = answers_dict.get(q_id, "").strip()

        if not answer:
            user_data["evidence_scores"][q["evidence_type"]] = 0
            continue

        extraction = extract_from_answer(
            question=q["english"],
            answer=answer,
            evidence_type=q["evidence_type"],
            client=client
        )

        user_data["answers"][q_id] = answer
        user_data["extracted"][q["evidence_type"]] = extraction
        user_data["evidence_scores"][q["evidence_type"]] = extraction["confidence"]

        total_confidence += extraction["confidence"]
        answered_count += 1

        print(f"  ✅ Q{q_id} processed — confidence: {extraction['confidence']}%")

    if answered_count > 0:
        user_data["overall_confidence"] = int(total_confidence / answered_count)

    user_data = _extract_key_fields(user_data, answers_dict, client)

    return user_data


def _extract_key_fields(user_data, answers_dict, client):
    """Extract name, location, community from all answers — always output in English."""

    all_answers = "\n".join([
        f"Q{qid}: {ans}"
        for qid, ans in answers_dict.items()
        if ans.strip()
    ])

    if not all_answers:
        return user_data

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract key identity information from these interview answers. "
                        "The answers may be in any language — Tamil, Hindi, Urdu, Telugu, "
                        "or any other Indian or tribal language. "
                        "You MUST always respond in ENGLISH only. "
                        "Translate all names, places, and details into English. "
                        "Respond in exactly this format:\n"
                        "NAME: [full name in English or 'Unknown']\n"
                        "LOCATION: [village/region in English or 'Unknown']\n"
                        "COMMUNITY: [community/family ties in English or 'Unknown']\n"
                        "FAMILY: [parent names and occupation in English or 'Unknown']\n"
                        "Keep each field to one line only."
                    )
                },
                {
                    "role": "user",
                    "content": all_answers
                }
            ],
            max_tokens=200,
            temperature=0.1,
        )

        raw = response.choices[0].message.content.strip()
        for line in raw.split("\n"):
            if line.startswith("NAME:"):
                user_data["name"] = line.replace("NAME:", "").strip()
            elif line.startswith("LOCATION:"):
                user_data["location"] = line.replace("LOCATION:", "").strip()
            elif line.startswith("COMMUNITY:"):
                user_data["community"] = line.replace("COMMUNITY:", "").strip()
            elif line.startswith("FAMILY:"):
                user_data["family"] = line.replace("FAMILY:", "").strip()

    except Exception as e:
        print(f"⚠️ Key field extraction error: {e}")

    return user_data


# ─────────────────────────────────────────────
# GENERATE LEGAL SUMMARY
# ─────────────────────────────────────────────

def generate_legal_summary(user_data):
    client = get_groq_client()

    profile_text = f"""
    Name: {user_data.get('name', 'Unknown')}
    Location: {user_data.get('location', 'Unknown')}
    Community: {user_data.get('community', 'Unknown')}
    Family: {user_data.get('family', 'Unknown')}
    Overall Confidence: {user_data.get('overall_confidence', 0)}%
    Evidence collected: {list(user_data.get('extracted', {}).keys())}
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a legal aid expert writing formal identity verification "
                        "documents for undocumented individuals. "
                        "Always write in ENGLISH only — never use any other language. "
                        "Write a 3-sentence formal legal summary suitable for submission "
                        "to a court or government authority. Be specific about what "
                        "evidence was gathered and what it establishes. "
                        "Use formal legal language."
                    )
                },
                {
                    "role": "user",
                    "content": f"Write a legal summary in English for this identity profile:\n{profile_text}"
                }
            ],
            max_tokens=300,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"⚠️ Legal summary error: {e}")
        return (
            f"Based on oral testimony and community evidence gathered through "
            f"structured interview, the subject presents credible claims of identity "
            f"with an overall evidence confidence score of "
            f"{user_data.get('overall_confidence', 0)}%. "
            f"The evidence collected includes testimony regarding location history, "
            f"community ties, and family records, which together form a basis for "
            f"identity verification proceedings."
        )


# ─────────────────────────────────────────────
# RECOMMENDED NEXT STEPS
# ─────────────────────────────────────────────

def get_next_steps(user_data):
    score = user_data.get("overall_confidence", 0)

    if score >= 75:
        return [
            "Submit dossier to nearest District Legal Services Authority (DLSA)",
            "Apply for Aadhaar enrollment at a special camp with this dossier",
            "Contact local NGO partner to arrange elder testimony recording",
            "File application for birth certificate with Municipal Corporation",
        ]
    elif score >= 50:
        return [
            "Arrange formal testimony from community elders mentioned in interview",
            "Collect any available physical documents (ration card fragments, photos)",
            "Re-interview with additional questions to strengthen location evidence",
            "Contact nearest legal aid clinic with this preliminary dossier",
        ]
    else:
        return [
            "Conduct follow-up interview with more specific location details",
            "Bring a community elder to provide corroborating testimony",
            "Search for any institutional records (school, clinic, temple registers)",
            "Contact local gram panchayat for community verification",
        ]


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  FirstVoice — AI Brain Test")
    print("=" * 50)

    client = get_groq_client()

    print("\n[TEST] Hardcoded Tamil Questions")
    for q in INTERVIEW_QUESTIONS:
        tamil = translate_question(q["english"], "Tamil", client)
        print(f"  Q{q['id']}: {tamil}")

    print("\n✅ Done!\n")