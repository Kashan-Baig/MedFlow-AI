import json
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import src.ai.db_services.db_services as db_service
from src.ai.utils.session_store import (
    create_session,
    add_conversation,
    get_session
)

from src.ai.services.input_service import (
    process_patient_input,
    validate_age,
    validate_name,
    validate_gender,
    validate_email,
    validate_phone
)

from src.ai.services.rag_service import get_relevant_context
from src.ai.services.insight_service import (
    generate_insights,
    generate_patient_response
)

from src.ai.services.intent_service import detect_intent
from src.ai.services.general_chat_service import general_chat, INTRO_MESSAGE

from src.ai.db_services.med_history_service import get_medical_history


# =========================
# SAFE INPUT
# =========================
def safe_input(prompt):
    value = input(prompt).strip()
    if value.lower() in ["exit", "quit"]:
        print("\n👋 Session ended.")
        sys.exit(0)
    return value


# =========================
# MAIN WORKFLOW
# =========================
def chat_workflow(patient_id: str):

    session_id = create_session({})
    session = get_session(session_id)

    session["patient_id"] = patient_id

    # Fetch patient info
    patient_info = db_service.get_patient_by_id(patient_id)
    session["patient_info"] = patient_info or {}

    # Fetch medical history
    medical_history = get_medical_history(patient_id)
    session["medical_history"] = medical_history

    print(f"\nWelcome back, {patient_info['name']}! " + INTRO_MESSAGE)

    # =========================
    # STATE INIT
    # =========================
    session["mode"] = "idle"
    session["stage"] = None

    # =====================================================
    # LOOP
    # =====================================================
    while True:

        user_input = safe_input("\nYou: ")
        session = get_session(session_id)

        chat_history = session.get("conversations", [])


        mode = session.get("mode", "idle")
        stage = session.get("stage")

        # =====================================================
        # 🟢 IDLE MODE (GENERAL CHAT)
        # =====================================================
        if mode == "idle":

            try:
                intent = detect_intent(user_input)
            except:
                intent = "general"

            if intent == "medical":
                session["mode"] = "medical"
                session["stage"] = "symptom"
                print("\n🤒 Describe your symptoms:")
                continue

            print("\n🤖 Assistant:")
            ai_response = general_chat(user_input, session["patient_info"],chat_history=chat_history)
            print(ai_response)

            add_conversation(
                session_id=session_id,
                symptoms=user_input,      # reuse field
                insight="general",        # mark type
                response=ai_response,
                timestamp=str(datetime.now())
            )

            continue

        # =====================================================
        # 🔴 MEDICAL MODE
        # =====================================================

        # =====================================================
        # 🧠 SYMPTOM ANALYSIS
        # =====================================================
        if stage == "symptom":

            raw_data = {
                **session.get("patient_info", {}),
                "symptoms": user_input
            }

            try:
                patient = process_patient_input(raw_data)

                # RAG context
                context = get_relevant_context(patient)

                # Insight with medical history
                insight_json = generate_insights(
                    patient,
                    context,
                    medical_history=session.get("medical_history")
                )

                # Human-readable response
                response = generate_patient_response(patient, insight_json)

                session["last_insight"] = insight_json

            except Exception as e:
                print(f"❌ Medical error: {str(e)}")
                continue

            print("\n🤖 MedFlow AI Doctor:")
            print(response)

            add_conversation(
                session_id=session_id,
                symptoms=user_input,
                insight=insight_json,
                response=response,
                timestamp=str(datetime.now())
            )

            print("\n❓ Do you have more symptoms? (yes/no)")
            session["stage"] = "await_followup"
            continue

        # =====================================================
        # ⏳ FOLLOW-UP
        # =====================================================
        if stage == "await_followup":

            answer = user_input.lower()

            if answer in ["yes", "y"]:
                session["stage"] = "symptom"
                print("➡️ Tell me more symptoms.")
                continue

            elif answer in ["no", "n"]:
                session["stage"] = "booking"
                stage = "booking"
            else:
                print("❌ Please answer yes or no.")
                continue

        # =====================================================
        # 📅 BOOKING
        # =====================================================
        if stage == "booking":

            print("\n📅 Finding appointment...\n")

            try:
                appointment = db_service.book_appointment(
                    session_id,
                    session.get("last_insight")
                )

                if "error" in appointment:
                    print(f"❌ {appointment['error']}")
                else:
                    print("\n✅ Appointment Confirmed!")
                    print(f"👨‍⚕️ Doctor: {appointment['doctor']}")
                    print(f"🩺 Speciality: {appointment['speciality']}")
                    print(f"📅 Day: {appointment['day']}")
                    print(f"⏰ Time: {appointment['time_slot']}")

            except Exception as e:
                print(f"❌ Booking error: {str(e)}")

            # Reset only necessary fields
            session["mode"] = "idle"
            session["stage"] = None
            session["last_insight"] = None

            print("\n💬 You can continue chatting.")
            continue


# =========================
# RUN
# =========================
if __name__ == "__main__":
    chat_workflow(65)