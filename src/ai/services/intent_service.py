from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

def detect_intent(user_input):
    """
    Classify user intent into medical or general
    """
    
    prompt = f"""
Classify the user's intent into ONE of these:

1. medical → When user:
   - Is describing symptoms, illness, pain, or not feeling well
   - Wants to book/schedule an appointment
   - Mentions needing a doctor or medical help
   
   Examples:
   - "I have fever"
   - "I feel headache"
   - "I am sick"
   - "chest pain"
   - "book an appointment"
   - "I want to see a doctor"
   - "schedule appointment"
   - "need medical help"

2. general → EVERYTHING else:
   - General questions about the system
   - Asking how things work
   - Greetings
   - Chit chat
   - Questions about doctors (but not booking)
   
   Examples:
   - "Hello"
   - "How does this work?"
   - "What doctors do you have?"
   - "Tell me about your services"

IMPORTANT RULES:
- If user wants to BOOK or SCHEDULE → return "medical"
- If user is just ASKING about doctors/services → return "general"

User Input:
{user_input}

Return ONLY one word:
medical
or
general
"""

    response = llm.invoke(prompt)
    return response.content.strip().lower()