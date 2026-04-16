from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

def detect_intent(user_input: str) -> str:
    prompt = f"""
Classify the user's intent into ONE of these:

1. medical → ONLY when user is describing symptoms, illness, pain, or not feeling well
   Examples:
   - I have fever
   - I feel headache
   - I am sick
   - chest pain

2. general → EVERYTHING else:
   - asking about doctors
   - asking about system
   - booking questions
   - greetings
   - chit chat

IMPORTANT RULE:
If user is asking about doctors, hospital, system, or information → ALWAYS return "general"

User Input:
{user_input}

Return ONLY:
medical
or
general
"""

    response = llm.invoke(prompt)
    return response.content.strip().lower()