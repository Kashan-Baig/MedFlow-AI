import os
import json
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from app.ai.services.input_service import PatientInput

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)


# =========================
# STRUCTURED INSIGHT (FINAL FIX)
# =========================
def generate_insights(patient, context):

    # ensure context is string
    if isinstance(context, dict):
        context = context.get("context", "")

    prompt = f"""
You are a medical AI system.

STRICT RULES:
- Return ONLY valid JSON
- Max 3 diseases
- ONLY ONE primary_specialist (no slashes, no multiple values)
- Keep response clean (no notes, no explanation)
- Use ONLY information from the provided CONTEXT below
- If context lacks information, set primary_specialist to "General Physician"
- For infants (age < 2), ALWAYS set primary_specialist to "Pediatrician"
- Do NOT answer anything unrelated to symptoms.
- Do NOT engage in conversation outside symptom analysis.
- Always redirect the user back to providing symptoms.

PATIENT:
Name: {patient.name}
Age: {patient.age}
Gender: {patient.gender}
Symptoms: {patient.symptoms}

CONTEXT (USE ONLY THIS INFORMATION):
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


# =========================
# HUMAN RESPONSE (CHATBOT)
# =========================
# =========================
# HUMAN RESPONSE (CHATBOT)
# =========================
def generate_patient_response(patient: PatientInput, insight_json: str):

    prompt = f"""
You are a friendly medical assistant.

RULES:
- Be brief and concise (2-3 sentences max)
- Be calm, supportive, and professional
- Do NOT mention disease names or possible conditions
- Do NOT say "you may have X" or "it's possible you have Y"
- Focus ONLY on: acknowledging symptoms + specialist referral + urgency level
- Suggest next step clearly
- Use ONLY information from the AI insight provided
- If symptoms are not covered in available data, respond: "Your symptoms are outside our current coverage area. I recommend consulting a General Physician for a comprehensive evaluation."
- For infants (age < 2), always direct to Pediatrician
- If the user says anything OTHER than symptoms (e.g., greetings, random questions, personal info, jokes, or unrelated text), respond strictly with:
"I can only help with symptom-based medical queries. Please describe your symptoms."

Do NOT answer anything unrelated to symptoms.
Do NOT engage in conversation outside symptom analysis.
Always redirect the user back to providing symptoms.

PATIENT SYMPTOMS:
{patient.symptoms}

AI INSIGHT:
{insight_json}

GOOD EXAMPLE:
"I understand you're experiencing concerning symptoms. I recommend seeing an Infectious Disease Specialist as soon as possible for proper evaluation."

BAD EXAMPLE (DO NOT DO THIS):
"Based on your symptoms, it's possible you may have Dengue Fever or Influenza..."

Respond briefly and naturally (2-3 sentences):
"""

    response = llm.invoke(prompt)
    return response.content.strip()


# =========================
# SAFE JSON PARSE (IMPORTANT)
# =========================
def parse_insight(json_str: str):
    try:
        import re
        match = re.search(r"```(?:json)?\n?(.*?)```", json_str, re.DOTALL)
        raw = match.group(1) if match else json_str
        return json.loads(raw)
    except:
        return {
            "error": "invalid_json",
            "raw": json_str
        }