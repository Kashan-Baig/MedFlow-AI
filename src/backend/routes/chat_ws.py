from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.backend.core.enums import Step
from src.ai.services.input_service import (
    process_patient_input,
    validate_age,
    validate_name,
    validate_gender,
    validate_email,
    validate_phone

)
from datetime import datetime
from src.ai.services.insight_service import (
    generate_insights,
    generate_patient_response
)
from src.ai.services.rag_service import get_relevant_context
from src.ai.utils.session_store import create_session, add_conversation, get_session
from src.ai.utils.doctor_store import doctors
from src.ai.db_services.booking_service import (
    parse_insight, normalize_speciality, get_next_7_days, get_next_date_for_day
)
from src.ai.db_services.appointment_db_service import create_appointment
from src.ai.db_services.consultation_db_service import save_consultation_record
router = APIRouter()
# This will hold active sessions: {session_id: {state, patient_info, ...}}
active_sessions = {}
@router.websocket("/ws/patient/chat")
async def chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Generate a simple session ID
    session_id = id(websocket)
    # Initialize session state
    active_sessions[session_id] = {
        "step": Step.AWAITING_NAME,
        "patient_info": {}
    }
    # Send welcome message
    await websocket.send_json({
        "step": Step.AWAITING_NAME,
        "message": "🏥 Welcome to MedFlow AI Medical Assistant! What's your full name?"
    })
    try:
        while True:
            data = await websocket.receive_text()
            session = active_sessions[session_id]
            step = session["step"]

            # ---- STEP 1: NAME ----
            if step == Step.AWAITING_NAME:
                if validate_name(data):
                    session["patient_info"]["name"] = data
                    session["step"] = Step.AWAITING_EMAIL
                    await websocket.send_json({
                        "step": Step.AWAITING_EMAIL,
                        "message": "Got it! What's your email?"
                    })
                else:
                    await websocket.send_json({
                        "step": Step.AWAITING_NAME,
                        "message": "Invalid name. Please enter at least 2 characters."
                    })

            # ---- STEP 2: EMAIL ----
            elif step == Step.AWAITING_EMAIL:
                if validate_email(data):
                    session["patient_info"]["email"] = data
                    session["step"] = Step.AWAITING_AGE
                    await websocket.send_json({
                        "step": Step.AWAITING_AGE,
                        "message": "What's your age?"
                    })
                else:
                    await websocket.send_json({
                        "step": Step.AWAITING_EMAIL,
                        "message": "❌ Invalid email. Try again."
                    })

            # ---- STEP 3: AGE ----
            elif step == Step.AWAITING_AGE:
                if validate_age(data):
                    session["patient_info"]["age"] = data
                    session["step"] = Step.AWAITING_GENDER
                    await websocket.send_json({
                        "step": Step.AWAITING_GENDER,
                        "message": "What's your gender? (male/female)"
                    })
                else:
                    await websocket.send_json({
                        "step": Step.AWAITING_AGE,
                        "message": "Age must be between 1-120."
                    })

            # ---- STEP 4: GENDER ----
            elif step == Step.AWAITING_GENDER:
                if validate_gender(data.lower()):
                    session["patient_info"]["gender"] = data.lower()
                    session["step"] = Step.AWAITING_PHONE
                    await websocket.send_json({
                        "step": Step.AWAITING_PHONE,
                        "message": "📱 What's your phone number?"
                    })
                else:
                    await websocket.send_json({
                        "step": Step.AWAITING_GENDER,
                        "message": "❌ Only 'male' or 'female' allowed."
                    })

            # ---- STEP 5: PHONE ----
            elif step == Step.AWAITING_PHONE:
                if validate_phone(data):
                    session["patient_info"]["phone"] = data
                    # Save to session store (links local active_session to session store)
                    store_session_id = create_session(session["patient_info"])
                    session["store_session_id"] = store_session_id
                    session["step"] = Step.AWAITING_SYMPTOMS
                    await websocket.send_json({
                        "step": Step.AWAITING_SYMPTOMS,
                        "message": "✅ All set! Now describe your symptoms."
                    })
                else:
                    await websocket.send_json({
                        "step": Step.AWAITING_PHONE,
                        "message": "❌ Invalid phone number."
                    }) 
            # ---- STEP 6: SYMPTOMS (THE AI PART) ----
            elif step == Step.AWAITING_SYMPTOMS:
                try:
                    # Build the patient object from stored info + new symptoms
                    raw_data = {**session["patient_info"], "symptoms": data}
                    patient = process_patient_input(raw_data)
                    # Get RAG context
                    context = get_relevant_context(patient)
                    # Generate AI insight (structured JSON)
                    insight_json = generate_insights(patient, context.get("context", ""))
                    # Generate friendly response for patient
                    response = generate_patient_response(patient, insight_json)
                    # Store in session for later (booking will need this)
                    session["last_insight"] = insight_json
                    session["last_response"] = response
                    
                    # Saving conversation to session store
                    add_conversation(
                        session_id=session["store_session_id"],
                        symptoms=data,
                        insight=insight_json,
                        response=response,
                        timestamp=str(datetime.now())
                    )
                    print("our insight_json to either store in the db or send to the FE " , insight_json)
                    # Send AI response + follow-up question
                    await websocket.send_json({
                        "step": Step.AWAITING_FOLLOWUP,
                        "message": response + "\n\n❓ Do you have more symptoms? (yes/no)",
                        # "insight": insight_json,
                    })
                    session["step"] = Step.AWAITING_FOLLOWUP

                except Exception as e:
                    await websocket.send_json({
                        "step": Step.AWAITING_SYMPTOMS,
                        "message": f"❌ Error analyzing symptoms: {str(e)}. Try again."
                    })

            # ---- STEP 7: FOLLOW-UP ----
            elif step == Step.AWAITING_FOLLOWUP:
                if data.lower() in ["yes", "y"]:
                    session["step"] = Step.AWAITING_SYMPTOMS
                    await websocket.send_json({
                        "step": Step.AWAITING_SYMPTOMS,
                        "message": "🤒 Tell me your additional symptoms."
                    })
                else:
                    session["step"] = Step.AWAITING_BOOKING
                    await websocket.send_json({
                        "step": Step.AWAITING_BOOKING,
                        "message": "🏥 Would you like to book an appointment? (yes/no)"
                    })

            # ---- STEP 8: BOOKING DECISION ----
            elif step == Step.AWAITING_BOOKING:
                if data.lower() in ["yes", "y"]:
                    # Build available slots from insight
                    insight = parse_insight(session.get("last_insight", ""))
                    speciality = normalize_speciality(
                        insight.get("primary_specialist")
                        or insight.get("recommended_specialist")
                        or "General Physician"
                    )

                    next_days = get_next_7_days()
                    slot_list = []
                    count = 1
                    for day in next_days:
                        for doc in doctors:
                            if any(s.lower() == speciality.lower() for s in doc["speciality"]):
                                if day in doc["available_days"]:
                                    date = get_next_date_for_day(day)
                                    for time_slot in doc["time_slots"]:
                                        slot_list.append({
                                            "slot_number": count,
                                            "doctor": doc["name"],
                                            "doctor_id": doc["id"],
                                            "speciality": speciality,
                                            "day": day,
                                            "date": str(date),
                                            "time_slot": time_slot
                                        })
                                        count += 1

                    if not slot_list:
                        await websocket.send_json({
                            "step": Step.DONE,
                            "message": f"❌ No slots available for {speciality}. Session ended. 👋"
                        })
                        break

                    # Store slots so we can look up the choice later
                    session["available_slots"] = slot_list

                    # Build a readable list for the user
                    slots_text = f"🩺 Specialist: {speciality}\n📅 Available Slots:\n\n"
                    for s in slot_list:
                        slots_text += f"{s['slot_number']}. {s['day']} ({s['date']}) - {s['time_slot']} ({s['doctor']})\n"
                    slots_text += "\n👉 Enter the slot number to book:"

                    session["step"] = Step.AWAITING_SLOT_SELECTION
                    await websocket.send_json({
                        "step": Step.AWAITING_SLOT_SELECTION,
                        "message": slots_text,
                        "slots": slot_list
                    })
                else:
                    await websocket.send_json({
                        "step": Step.DONE,
                        "message": "👍 Take care! Session ended. 👋"
                    })
                    break

            # ---- STEP 9: SLOT SELECTION ----
            elif step == Step.AWAITING_SLOT_SELECTION:
                slot_list = session.get("available_slots", [])
                if data.isdigit() and 1 <= int(data) <= len(slot_list):
                    chosen = slot_list[int(data) - 1]
                    session["chosen_slot"] = chosen

                    confirm_text = (
                        f"👨‍⚕️ Appointment Details:\n"
                        f"Doctor: {chosen['doctor']}\n"
                        f"Speciality: {chosen['speciality']}\n"
                        f"Day: {chosen['day']} ({chosen['date']})\n"
                        f"Time: {chosen['time_slot']}\n\n"
                        f"✅ Confirm appointment? (yes/no)"
                    )
                    session["step"] = Step.AWAITING_BOOKING_CONFIRM
                    await websocket.send_json({
                        "step": Step.AWAITING_BOOKING_CONFIRM,
                        "message": confirm_text
                    })
                else:
                    await websocket.send_json({
                        "step": Step.AWAITING_SLOT_SELECTION,
                        "message": f"❌ Invalid choice. Enter a number between 1 and {len(slot_list)}."
                    })

            # ---- STEP 10: BOOKING CONFIRMATION ----
            elif step == Step.AWAITING_BOOKING_CONFIRM:
                if data.lower() in ["yes", "y"]:
                    chosen = session["chosen_slot"]
                    try:
                        appointment_id = create_appointment(
                            patient_id=session["store_session_id"],
                            doctor_id=chosen["doctor_id"],
                            slot_id=1
                        )

                        # Save consultation record
                        record_id = save_consultation_record(
                            appointment_id,
                            session.get("last_insight", ""),
                            session.get("last_response", "")
                        )

                        await websocket.send_json({
                            "step": Step.DONE,
                            "message": (
                                f"✅ Appointment Confirmed!\n"
                                f"👨‍⚕️ Doctor: {chosen['doctor']}\n"
                                f"🩺 Specialist: {chosen['speciality']}\n"
                                f"📅 {chosen['day']} ({chosen['date']})\n"
                                f"⏰ Time: {chosen['time_slot']}\n"
                                f"📄 Consultation ID: {record_id}\n\n"
                                f"👋 Take care!"
                            )
                        })
                    except Exception as e:
                        await websocket.send_json({
                            "step": Step.DONE,
                            "message": f"❌ Booking Error: {str(e)}\n👋 Session ended."
                        })
                    break
                else:
                    await websocket.send_json({
                        "step": Step.DONE,
                        "message": "❌ Appointment cancelled. 👋 Take care!"
                    })
                    break

    except WebSocketDisconnect:
        # Cleanup when user disconnects
        active_sessions.pop(session_id, None)
