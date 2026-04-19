from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

from src.ai.db_services.doctor_service import get_doctors_by_speciality

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.5
)

# =========================
# INTRO MESSAGE
# =========================
INTRO_MESSAGE = """
👋 Hello! Welcome to MedFlow AI — your intelligent healthcare assistant.

We help you with:
1. AI-based symptom analysis  
2. Smart doctor recommendations  
3. Easy appointment booking  
4. Access to verified specialists  

Our system uses intelligent medical analysis to guide you to the right doctor at the right time.

💡 If you're not feeling well, just describe your symptoms and I’ll assist you step-by-step.

How may I help you today?
"""

# =========================
# HELPER: NEXT 7 DAYS
# =========================
def get_next_7_days():
    today = datetime.now()
    return [(today + timedelta(days=i)).strftime("%A") for i in range(7)]


# =========================
# HELPER: DETECT DOCTOR QUERY
# =========================
def is_doctor_query(user_input: str) -> bool:
    keywords = [
        "doctor", "doctors", "specialist",
        "cardiologist", "neurologist", "dermatologist",
        "physician", "orthopedic", "pediatrician",
        "show", "list", "available"
    ]
    return any(k in user_input.lower() for k in keywords)


# =========================
# HELPER: EXTRACT SPECIALITY
# =========================
def extract_speciality(user_input: str) -> str:
    specialities = [
        "cardiologist",
        "neurologist",
        "dermatologist",
        "general physician",
        "orthopedic",
        "pediatrician"
    ]

    for spec in specialities:
        if spec in user_input.lower():
            return spec.title()

    return None


# =========================
# DOCTOR FETCH FROM DB
# =========================
def fetch_doctors_by_speciality(speciality: str):

    all_doctors = {}
    days = get_next_7_days()
    daily_map = get_doctors_by_speciality(speciality)

    for day in days:
        doctors = daily_map.get(day, [])

        for doc in doctors:
            if doc["id"] not in all_doctors:
                all_doctors[doc["id"]] = doc

    return list(all_doctors.values())


# =========================
# MAIN GENERAL CHAT
# =========================
def general_chat(user_input: str , patient_info: dict = None, chat_history=None):

    history_text = ""

    if chat_history:
        history_text = "\n".join([
            f"User: {c['symptoms']}\nAssistant: {c['response']}"
            for c in chat_history[-5:]   # last 5 only
        ])

    patient_context = ""
    if patient_info:
        patient_context = f"\nYou are currently talking to: {patient_info['name']}, a {patient_info['age']} year old {patient_info['gender']}."
    # =========================
    # 1. HANDLE DOCTOR QUERIES (DB)
    # =========================
    if is_doctor_query(user_input):

        speciality = extract_speciality(user_input)

        # ❗ Edge case: no speciality mentioned
        if not speciality:
            return (
                "👨‍⚕️ Please specify a speciality (e.g., Cardiologist, Neurologist), "
                "so I can show available doctors."
            )

        doctors = fetch_doctors_by_speciality(speciality)

        # ❗ No doctors found
        if not doctors:
            return f"❌ No {speciality} available in the coming days."

        # ✅ Format response
        response = f"\n👨‍⚕️ Available {speciality}s:\n\n"

        for doc in doctors:
            response += f"• {doc['name']}\n"

        response += (
            "\n💡 To book an appointment, simply describe your symptoms "
            "and I’ll guide you to the best doctor."
        )

        return response



    # =========================
    # 2. GENERAL LLM CHAT
    # =========================
    prompt = f"""
You are MedFlow AI — a professional healthcare assistant.
{patient_context}
Your responsibilities:
- Answer general questions about the system
- Explain doctor availability and booking process
- Guide users toward AI-based symptom analysis

SYSTEM FEATURES:
- AI-powered symptom analysis
- Smart doctor recommendation
- Appointment booking system
- Verified specialists

IMPORTANT RULES:
- Use previous conversation for context if available
- Keep responses SHORT and clear
- Be professional and friendly
- If user asks about doctors → suggest checking availability
- If user asks for appointment → say symptoms are required first
- If user shows any illness → guide them to describe symptoms

GOAL:
Encourage users to use the AI symptom analysis for best results.

CHAT HISTORY:
{history_text}

User:
{user_input}

Response:
"""

    response = llm.invoke(prompt)
    return response.content.strip()