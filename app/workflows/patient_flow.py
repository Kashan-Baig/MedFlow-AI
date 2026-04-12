import json
import os
import sys
from datetime import datetime

# Fix sys.path for running the file directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from app.services.booking_service import book_appointment
from app.utils.session_store import create_session, add_conversation
from app.utils.session_store import get_session
from app.ai.services.input_service import process_patient_input, to_dict
from app.ai.services.rag_service import get_relevant_context
from app.ai.services.insight_service import (
    generate_insights,
    generate_patient_response
)

LOG_FILE = "C:\\Users\\amtul\\Desktop\\MedFlow-AI\\ai_logs.json"

def save_session(session_id):
    session = get_session(session_id)

    if not session:
        return

    log_entry = {
        "timestamp": str(datetime.now()),
        "session": session
    }

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(log_entry)

    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=4)
def safe_input(prompt):
    value = input(prompt).strip()
    if value.lower() in ["exit", "quit"]:
        print("\n👋 Session ended by user.")
        sys.exit(0)
    return value

# =========================
# MAIN CHAT WORKFLOW
# =========================
def chat_workflow():

    print("\n🏥 Welcome to MedFlow AI Medical Assistant")
    print("Type 'exit' anytime to quit\n")

    # =========================
    # STEP 1: BASIC INFO
    # =========================
    name = safe_input("👤 Enter your full name: ")
    age = safe_input("🎂 Enter your age: ")
    gender = safe_input("⚧ Enter your gender: ")
    email = safe_input("📧 Enter your email: ")
    phone = safe_input("📱 Enter your phone number: ")

    patient_info = {
        "name": name,
        "age": age,
        "gender": gender,
        "email": email,
        "phone": phone
    }

    session_id = create_session(patient_info)

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
        # ADD TO SESSION CONVERSATION
        # =========================
        add_conversation(
            session_id=session_id,
            symptoms=symptoms,
            insight=insight_json,
            response=response,
            timestamp=str(datetime.now())
        )

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

            try:
                # ✅ call booking service
                appointment = book_appointment(session_id, insight_json)

                # ✅ handle response
                if "error" in appointment:
                    print(f"❌ {appointment['error']}")
                else:
                    print("\n✅ Appointment Confirmed!")
                    print(f"👨‍⚕️ Doctor: {appointment['doctor']}")
                    print(f"🩺 Specialist: {appointment['speciality']}")
                    print(f"📅 Day: {appointment['day']}")
                    print(f"⏰ Time: {appointment['time_slot']}")
                    print(f"📌 Status: {appointment['status']}")

            except Exception as e:
                print(f"\n❌ Booking Error: {str(e)}")

        else:
            print("\n👍 Okay. Take care and stay healthy!")

        print("\n👋 Session ended.")
        save_session(session_id)
        break


# =========================
# RUN
# =========================
if __name__ == "__main__":
    chat_workflow()