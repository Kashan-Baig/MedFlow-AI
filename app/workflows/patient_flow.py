import json
import os
import sys
from datetime import datetime

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from app.services.booking_service import book_appointment
from app.services.consultation_db_service import save_consultation_record
from app.utils.session_store import create_session, add_conversation, get_session
from app.ai.services.input_service import process_patient_input
from app.ai.services.rag_service import get_relevant_context
from app.ai.services.insight_service import (
    generate_insights,
    generate_patient_response
)
from app.services.patient_db_service import create_patient_if_not_exists

LOG_FILE = "ai_logs.json"


# =========================
# SAFE SESSION SAVE
# =========================
def save_session(session_id):
    session = get_session(session_id)
    if not session:
        return

    log_entry = {
        "timestamp": str(datetime.now()),
        "session": session
    }

    data = []

    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
        except json.JSONDecodeError:
            data = []

    data.append(log_entry)

    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=4)


# =========================
# SAFE INPUT
# =========================
def safe_input(prompt):
    value = input(prompt).strip()
    if value.lower() in ["exit", "quit"]:
        print("\n👋 Session ended by user.")
        sys.exit(0)
    return value


# =========================
# MAIN WORKFLOW
# =========================
def chat_workflow():

    print("\n🏥 Welcome to MedFlow AI Medical Assistant")
    print("Type 'exit' anytime to quit\n")

    # STEP 1 PATIENT INFO
    name = safe_input("👤 Enter your full name: ")
    email = safe_input("📧 Enter your email: ")
    age = safe_input("🎂 Enter your age: ")
    gender = safe_input("⚧ Enter your gender: ")
    phone = safe_input("📱 Enter your phone number: ")

    patient_info = {
        "name": name,
        "age": age,
        "gender": gender,
        "email": email,
        "phone": phone
    }

    session_id = create_session(patient_info)

    # CREATE PATIENT
    try:
        patient_obj = process_patient_input({
            **patient_info,
            "symptoms": "initial"
        })

        patient_id = create_patient_if_not_exists(patient_obj)
        print(f"\n✅ Patient registered with ID: {patient_id}")

    except Exception as e:
        print(f"\n❌ DB Error: {str(e)}")
        patient_id = None

    print("\n✅ Thanks! Now tell me your symptoms.")

    # =========================
    # CHAT LOOP
    # =========================
    while True:

        symptoms = safe_input("\n🤒 Enter symptoms: ")

        raw_data = {**patient_info, "symptoms": symptoms}

        try:
            patient = process_patient_input(raw_data)
        except Exception as e:
            print(f"\n❌ Input Error: {str(e)}")
            continue

        print("\n🧠 Analyzing your symptoms...\n")

        try:
            context = get_relevant_context(patient)

            insight_json = generate_insights(
                patient,
                context.get("context", "")
            )

            response = generate_patient_response(patient, insight_json)

        except Exception as e:
            print(f"\n❌ AI Error: {str(e)}")
            continue

        print("\n🤖 AI DOCTOR RESPONSE:")
        print(response)

        print("\n🧠 INTERNAL INSIGHT:")
        print(insight_json)

        add_conversation(
            session_id=session_id,
            symptoms=symptoms,
            insight=insight_json,
            response=response,
            timestamp=str(datetime.now())
        )

        follow_up = safe_input("\n❓ More symptoms? (yes/no): ").lower()

        if follow_up in ["yes", "y"]:
            continue

        # =========================
        # BOOKING FLOW
        # =========================
        book = safe_input("\n🏥 Book appointment? (yes/no): ").lower()

        if book in ["yes", "y"]:

            print("\n📅 Booking process started...\n")

            try:
                appointment = book_appointment(session_id, insight_json)

                if "error" in appointment:
                    print(f"❌ {appointment['error']}")
                else:
                    print("\n✅ Appointment Confirmed!")
                    print(f"👨‍⚕️ Doctor: {appointment['doctor']}")
                    print(f"🩺 Specialist: {appointment['speciality']}")
                    print(f"📅 Day: {appointment['day']}")
                    print(f"⏰ Time: {appointment['time_slot']}")
                    print(f"📌 Status: {appointment['status']}")

                    # =========================
                    # 🔥 SAVE CONSULTATION TO DB
                    # =========================
                    record_id = save_consultation_record(
                        appointment["appointment_id"],
                        insight_json,
                        response
                    )

                    print(f"\n📄 Consultation saved (ID: {record_id})")

            except Exception as e:
                print(f"\n❌ Booking Error: {str(e)}")

        else:
            print("\n👍 Okay. Take care!")

        print("\n👋 Session ended.")

        save_session(session_id)
        break


if __name__ == "__main__":
    chat_workflow()