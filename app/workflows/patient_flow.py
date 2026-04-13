import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from app.services.patient_db_service import create_patient_if_not_exists
from app.services.booking_service import book_appointment
from app.services.consultation_db_service import save_consultation_record
from app.utils.session_store import create_session, add_conversation, get_session
from app.ai.services.input_service import (
    process_patient_input,
    validate_age,
    validate_name,
    validate_gender,
    validate_email,
    validate_phone
)
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
    # STEP 1 PATIENT INFO (SMART VALIDATION)
    # =========================

    # NAME
    while True:
        name = safe_input("👤 Enter your full name: ")
        if validate_name(name):
            break
        print("❌ Invalid name. Try again.")

    # EMAIL
    while True:
        email = safe_input("📧 Enter your email: ")
        if validate_email(email):
            break
        print("❌ Invalid email format.")

    # AGE
    while True:
        age = safe_input("🎂 Enter your age: ")
        if validate_age(age):
            break
        print("❌ Age must be between 1–120.")

    # GENDER
    while True:
        gender = safe_input("⚧ Enter your gender (male/female): ").lower()
        if validate_gender(gender):
            break
        print("❌ Only 'male' or 'female' allowed.")

    # PHONE
    while True:
        phone = safe_input("📱 Enter your phone number: ")
        if validate_phone(phone):
            break
        print("❌ Invalid phone number.")

    patient_info = {
        "name": name,
        "age": age,
        "gender": gender,
        "email": email,
        "phone": phone
    }

    session_id = create_session(patient_info)

    # =========================
    # CREATE PATIENT IN DB
    # =========================
    try:
        patient_obj = process_patient_input({
            **patient_info,
            "symptoms": "initial"
        })

        patient_id = create_patient_if_not_exists(patient_obj)

        session = get_session(session_id)
        session["patient_id"] = patient_id   

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
            insight_json = generate_insights(patient, context)
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

                    # =========================
                    # SAVE CONSULTATION
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
            print("\n👍 Okay. Take care and stay healthy!")

        print("\n👋 Session ended.")
        save_session(session_id)
        break


# =========================
# RUN
# =========================
if __name__ == "__main__":
    chat_workflow()