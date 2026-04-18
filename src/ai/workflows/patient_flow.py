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
def chat_workflow(patient_id:str):

    session_id = create_session({})
    session = get_session(session_id)
    session["patient_id"] = patient_id
    patient_info = db_service.get_patient_by_id(patient_id)

    # storing the patient info for the session
    session["patient_info"] = patient_info or {}
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

        mode = session.get("mode", "idle")
        stage = session.get("stage")

        # =====================================================
        # 🟢 IDLE MODE (CHAT)
        # =====================================================
        if mode == "idle":

            try:
                intent = detect_intent(user_input)
            except:
                intent = "general"

            if intent == "medical":
                session["mode"] = "medical"
                session["stage"] = "symptom"
                print("\n Describe your symptoms:")
                continue

            print("\n🤖 Assistant:")
            print(general_chat(user_input , session["patient_info"]))
            continue

        # =====================================================
        # 🔴 MEDICAL MODE
        # =====================================================

        # -------------------------
        # NAME
        # -------------------------
        # if stage == "collect_name":
        #     if validate_name(user_input):
        #         session["patient_info"]["name"] = user_input
        #         session["stage"] = "collect_email"
        #         print("📧 Enter email:")
        #     else:
        #         print("❌ Invalid name")
        #     continue

        # # -------------------------
        # # EMAIL
        # # -------------------------
        # if stage == "collect_email":
        #     if validate_email(user_input):
        #         session["patient_info"]["email"] = user_input
        #         session["stage"] = "collect_age"
        #         print("🎂 Enter age:")
        #     else:
        #         print("❌ Invalid email")
        #     continue

        # # -------------------------
        # # AGE
        # # -------------------------
        # if stage == "collect_age":
        #     if validate_age(user_input):
        #         session["patient_info"]["age"] = user_input
        #         session["stage"] = "collect_gender"
        #         print("⚧ Gender:")
        #     else:
        #         print("❌ Invalid age")
        #     continue

        # # -------------------------
        # # GENDER
        # # -------------------------
        # if stage == "collect_gender":
        #     if validate_gender(user_input.lower()):
        #         session["patient_info"]["gender"] = user_input.lower()
        #         session["stage"] = "collect_phone"
        #         print("📱 Phone:")
        #     else:
        #         print("❌ Invalid gender")
        #     continue

        # # -------------------------
        # # PHONE
        # # -------------------------
        # if stage == "collect_phone":
        #     if validate_phone(user_input):

        #         session["patient_info"]["phone"] = user_input

        #         try:
        #             patient_obj = process_patient_input({
        #                 **session["patient_info"],
        #                 "symptoms": "initial"
        #             })

        #             patient_id = create_patient_if_not_exists(patient_obj)
        #             session["patient_id"] = patient_id

        #             print(f"\n✅ Registered (ID: {patient_id})")

        #         except Exception as e:
        #             print(f"⚠️ DB Warning: {str(e)}")

        #         session["stage"] = "symptom"
        #         print("\n🤒 Describe your symptoms:")
        #     else:
        #         print("❌ Invalid phone")
        #     continue

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
                context = get_relevant_context(patient)

                insight_json = generate_insights(patient, context)
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

            # ⭐ IMPORTANT FIX: ASK + MOVE TO AWAIT STATE
            print("\n❓ Do you have more symptoms? (yes/no)")
            session["stage"] = "await_followup"
            continue

        # =====================================================
        # ⏳ AWAIT FOLLOWUP (THIS FIXES YOUR ISSUE)
        # =====================================================
        if stage == "await_followup":

            answer = user_input.lower()

            if answer in ["yes", "y"]:
                session["stage"] = "symptom"
                print("➡️ Tell me more symptoms.")
                continue

            elif answer in ["no", "n"]:
                # DON'T just set stage and continue - fall through to booking
                session["stage"] = "booking"
                stage = "booking"
                # Remove continue here so it falls through to booking logic below

            else:
                print("❌ Please answer yes or no.")
                continue

        # =====================================================
        # 📅 BOOKING
        # =====================================================
        if stage == "booking":
            print("\n📅 Finding appointment...\n")

            try:
                appointment = db_service. book_appointment(
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

            # RESET CLEANLY
            session["mode"] = "idle"
            session["stage"] = None
            session["last_insight"] = None
            session["patient_info"] = {}

            print("\n💬 You can continue chatting.")
            continue


# =========================
# RUN
# =========================
if __name__ == "__main__":
    chat_workflow(61)