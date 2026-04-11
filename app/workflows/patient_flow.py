import json
import os
from datetime import datetime


from app.ai.services.input_service import process_patient_input, to_dict
from app.ai.services.rag_service import get_relevant_context
from app.ai.services.insight_service import (
    generate_insights,
    generate_patient_response
)

# =========================
# LOG FILE
# =========================
LOG_FILE = "ai_logs.json"


# =========================
# SAVE LOGS
# =========================
def save_log(patient, insight):
    log_entry = {
        "timestamp": str(datetime.now()),
        "patient": to_dict(patient),   # ✅ convert object → dict
        "insight": insight
    }

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(log_entry)

    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=4)


# =========================
# MAIN CHAT WORKFLOW
# =========================
def chat_workflow():

    print("\n🏥 Welcome to MedFlow AI Medical Assistant")
    print("Type 'exit' anytime to quit\n")

    # =========================
    # SAFE INPUT
    # =========================
    def safe_input(prompt):
        value = input(prompt).strip()
        if value.lower() in ["exit", "quit"]:
            print("\n👋 Session ended by user.")
            exit()
        return value

    # =========================
    # STEP 1: BASIC INFO
    # =========================
    name = safe_input("👤 Enter your full name: ")
    age = safe_input("🎂 Enter your age: ")
    gender = safe_input("⚧ Enter your gender: ")
    email = safe_input("📧 Enter your email: ")
    phone = safe_input("📱 Enter your phone number: ")

    print("\n✅ Thanks! Now tell me your symptoms.")

    # =========================
    # CHAT LOOP
    # =========================
    while True:

        symptoms = safe_input("\n🤒 Enter symptoms: ")

        # ✅ CREATE RAW DATA
        raw_data = {
            "name": name,
            "age": age,
            "gender": gender,
            "email": email,
            "phone": phone,
            "symptoms": symptoms
        }

        try:
            # ✅ CONVERT TO OBJECT (IMPORTANT FIX)
            patient = process_patient_input(raw_data)

        except Exception as e:
            print(f"\n❌ Input Error: {str(e)}")
            continue

        # =========================
        # AI PIPELINE
        # =========================
        print("\n🧠 Analyzing your symptoms...\n")

        try:
            context = get_relevant_context(patient)
            insight_json = generate_insights(patient)
            response = generate_patient_response(patient, insight_json)

        except Exception as e:
            print(f"\n❌ AI Error: {str(e)}")
            continue

        # =========================
        # OUTPUT
        # =========================
        print("\n🤖 AI DOCTOR RESPONSE:")
        print(response)

        print("\n🧠 INTERNAL INSIGHT:")
        print(insight_json)

        # =========================
        # SAVE LOG
        # =========================
        save_log(patient, insight_json)

        # =========================
        # FOLLOW-UP LOOP
        # =========================
        follow_up = safe_input(
            "\n❓ Do you have any more symptoms or questions? (yes/no): "
        ).lower()

        if follow_up in ["yes", "y"]:
            print("\n➡️ Okay, tell me more.")
            continue

        # =========================
        # APPOINTMENT FLOW
        # =========================
        book = safe_input(
            "\n🏥 Would you like to book an appointment with a doctor? (yes/no): "
        ).lower()

        if book in ["yes", "y"]:
            print("\n📅 Booking process started...")
            print("👉 (Here you will later connect SQL doctor scheduling system)")
            print("✅ Appointment request received!")
        else:
            print("\n👍 Okay. Take care and stay healthy!")

        print("\n👋 Session ended.")
        break


# =========================
# RUN
# =========================
if __name__ == "__main__":
    chat_workflow()