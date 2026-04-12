import os
import json
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from app.ai.services.rag_service import get_relevant_context
from app.ai.services.input_service import PatientInput

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)


# =========================
# STRUCTURED INSIGHT (DB READY)
# =========================
def generate_insights(patient):

    context = get_relevant_context(patient)

    prompt = f"""
You are a medical AI system.
Return ONLY ONE primary_specialist
(no slashes, no multiple values)

Return ONLY valid JSON (top 3 diseases max).

PATIENT:
Name: {patient.name}
Age: {patient.age}
Gender: {patient.gender}
Symptoms: {patient.symptoms}

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
    return response.content


# =========================
# HUMAN RESPONSE (CHATBOT)
# =========================
def generate_patient_response(patient: PatientInput, insight_json: str):

    prompt = f"""
You are a friendly medical assistant.

Explain the situation to the patient in simple human language.

RULES:
- No JSON
- Be calm and supportive
- Suggest next step
- Do NOT confirm final diagnosis

PATIENT:
{patient.symptoms}

AI INSIGHT:
{insight_json}

Now respond naturally:
"""

    response = llm.invoke(prompt)
    return response.content.strip()


# =========================
# OPTIONAL: SAFE JSON PARSE
# =========================
def parse_insight(json_str: str):
    try:
        return json.loads(json_str)
    except:
        return {
            "error": "invalid_json",
            "raw": json_str
        }