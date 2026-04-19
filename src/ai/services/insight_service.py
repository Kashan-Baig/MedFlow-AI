import os
import json
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from src.ai.services.input_service import PatientInput

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

# =========================================================
# 🧠 FORMAT MEDICAL HISTORY
# =========================================================
def format_medical_history(history: dict) -> str:
    if not history:
        return "No known medical history."

    return f"""
Allergies: {", ".join(history.get("allergies", [])) or "None"}
Blood Group: {history.get("blood_group", "Unknown")}
Chronic Conditions: {", ".join(history.get("chronic_conditions", [])) or "None"}
Current Medications: {", ".join(history.get("current_medications", [])) or "None"}
"""


# =========================================================
# 🧠 STRUCTURED INSIGHT (UPDATED)
# =========================================================
def generate_insights(patient, context, medical_history=None):

    if isinstance(context, dict):
        context = context.get("context", "")

    history_text = format_medical_history(medical_history)

    prompt = f"""
You are a medical AI system.

STRICT RULES:
- Return ONLY valid JSON
- Max 3 diseases
- ONLY ONE primary_specialist
- Use ONLY given CONTEXT
- Consider MEDICAL HISTORY carefully
- If insufficient info → "General Physician"
- If age < 2 → Pediatrician
- Do NOT hallucinate
- Do NOT answer unrelated content

PATIENT:
Name: {patient.name}
Age: {patient.age}
Gender: {patient.gender}
Symptoms: {patient.symptoms}

MEDICAL HISTORY:
{history_text}

CONTEXT:
{context}

JSON FORMAT:
{{
  "possible_diseases": [
    {{
      "name": "",
      "confidence": 0.0
    }}
  ],
  "primary_specialist": "",
  "alternative_specialists": [],
  "urgency": "low|medium|high|emergency",
  "severity_score": 1-10,
  "recommended_action": ""
}}
"""

    response = llm.invoke(prompt)
    return response.content.strip()


# =========================================================
# 💬 HUMAN RESPONSE
# =========================================================
def generate_patient_response(
    patient: PatientInput,
    insight_json: str
):

    prompt = f"""
You are a friendly medical assistant.

RULES:
- 2-3 sentences ONLY
- Calm, professional
- NO disease names
- Focus on symptoms + specialist + urgency
- Use insight strictly
- If non-medical input → redirect to symptoms

PATIENT SYMPTOMS:
{patient.symptoms}

AI INSIGHT:
{insight_json}

Respond naturally:
"""

    response = llm.invoke(prompt)
    return response.content.strip()


# =========================================================
# 🧾 SAFE JSON PARSER
# =========================================================
def parse_insight(json_str: str):
    try:
        import re

        match = re.search(r"```(?:json)?\n?(.*?)```", json_str, re.DOTALL)
        raw = match.group(1) if match else json_str

        return json.loads(raw)

    except Exception:
        return {
            "error": "invalid_json",
            "raw": json_str
        }