# app/ai/services/insight_service.py

import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

from app.ai.services.input_service import PatientInput
from app.ai.services.rag_service import get_relevant_context

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)


# ==================================================
# 1. STRUCTURED OUTPUT (FOR DATABASE)
# ==================================================
def generate_insights(patient: PatientInput):

    context = get_relevant_context(patient)

    prompt = f"""
You are a medical AI system.

Return ONLY valid JSON.

PATIENT:
Name: {patient.name}
Age: {patient.age}
Gender: {patient.gender}
Symptoms: {patient.symptoms}

CONTEXT:
{context}

JSON FORMAT:
{{
  "disease": "",
  "specialist": "",
  "urgency": "low|medium|high|emergency",
  "severity_score": 1-10,
  "recommended_action": ""
}}
"""

    response = llm.invoke(prompt)
    return response.content


# ==================================================
# 2. HUMAN RESPONSE (FOR CHATBOT / PATIENT TALK)
# ==================================================
def generate_patient_response(patient: PatientInput, structured_data: str):

    context = get_relevant_context(patient)

    prompt = f"""
You are a professional medical assistant in a hospital AI system.

You already analyzed the case.

Now respond to the patient in a clear, calm, human-like way.

IMPORTANT RULES:
- Do NOT output JSON
- Be empathetic
- Do NOT give final diagnosis as certainty
- Suggest specialist + urgency gently
- Offer appointment help

PATIENT:
Name: {patient.name}
Symptoms: {patient.symptoms}

AI ANALYSIS (JSON):
{structured_data}

MEDICAL CONTEXT:
{context}

Write a natural conversation response:
"""

    response = llm.invoke(prompt)
    return response.content.strip()