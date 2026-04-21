from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.backend.core.enums import Step
from src.ai.services.input_service import process_patient_input
from datetime import datetime
from src.ai.services.insight_service import generate_insights, generate_patient_response
from src.ai.services.rag_service import get_relevant_context
from src.ai.utils.session_store import create_session, add_conversation, get_session
from src.ai.db_services.booking_service import (
    parse_insight,
    normalize_speciality,
    get_next_date_for_day,
)
from src.ai.db_services import booking_service as db_booking
from src.ai.services.general_chat_service import (
    get_next_7_days,
    general_chat,
    INTRO_MESSAGE,
)
from src.ai.db_services.appointment_db_service import create_appointment
from src.ai.db_services.consultation_db_service import save_consultation_record
from src.ai.services.intent_service import detect_intent
from src.ai.db_services.med_history_service import get_medical_history
import src.ai.db_services.db_services as db_service

router = APIRouter()

# This will hold active sessions
active_sessions = {}


@router.websocket("/ws/patient/chat")
async def chat_endpoint(websocket: WebSocket, id: int):
    """
    WebSocket endpoint for patient chat
    Expects query parameter: ?id=<patient_id>
    """
    await websocket.accept()

    # Generate unique session ID for this WebSocket connection
    ws_session_id = hash(websocket)

    print(f"[WebSocket] New connection attempt for patient ID: {id}")

    # =====================================================
    # 🔍 FETCH PATIENT INFO FROM DATABASE
    # =====================================================
    try:
        patient_info = db_service.get_patient_by_id(id)

        if not patient_info:
            print(f"[WebSocket] Patient ID {id} not found in database")
            await websocket.send_json(
                {
                    "step": "error",
                    "message": "❌ Patient not found. Please register first.",
                }
            )
            await websocket.close()
            return

        print(f"[WebSocket] Patient loaded: {patient_info.get('name', 'Unknown')}")

    except Exception as e:
        print(f"[WebSocket] Error loading patient: {str(e)}")
        await websocket.send_json(
            {"step": "error", "message": f"❌ Error loading patient info: {str(e)}"}
        )
        await websocket.close()
        return

    # =====================================================
    # 🏥 FETCH MEDICAL HISTORY
    # =====================================================
    try:
        medical_history = get_medical_history(id)
        print(f"[WebSocket] Medical history loaded for patient {id}")
    except Exception as e:
        print(f"[WebSocket] No medical history found: {str(e)}")
        medical_history = None

    # =====================================================
    # 📝 CREATE SESSION STORE
    # =====================================================
    try:
        store_session_id = create_session(patient_info)
        print(f"[WebSocket] Session created: {store_session_id}")
    except Exception as e:
        print(f"[WebSocket] Error creating session: {str(e)}")
        await websocket.send_json(
            {"step": "error", "message": f"❌ Error creating session: {str(e)}"}
        )
        await websocket.close()
        return

    # Initialize session state
    active_sessions[ws_session_id] = {
        "step": Step.GENERAL_CHAT,
        "patient_id": id,
        "patient_info": patient_info,
        "medical_history": medical_history,
        "store_session_id": store_session_id,
        "mode": "idle",
        "stage": None,
    }

    print(f"[WebSocket] Active session initialized for patient {id}")

    # =====================================================
    # 👋 WELCOME MESSAGE
    # =====================================================
    await websocket.send_json(
        {
            "step": Step.GENERAL_CHAT,
            "intent": "general",
            "message": f"Welcome back, {patient_info['name']}! " + INTRO_MESSAGE,
        }
    )

    try:
        while True:
            data = await websocket.receive_text()
            session = active_sessions[ws_session_id]
            step = session["step"]

            print(f"[WebSocket] Received: {data[:50]}... | Step: {step}")

            # =====================================================
            # GENERAL CHAT WITH INTENT DETECTION
            # =====================================================
            if step == Step.GENERAL_CHAT:

                # Get fresh chat history from session store
                store_session = get_session(session["store_session_id"])
                chat_history = store_session.get("conversations", [])

                mode = session.get("mode", "idle")

                # =====================================================
                # 🟢 IDLE MODE (GENERAL CHAT)
                # =====================================================
                if mode == "idle":

                    try:
                        intent = detect_intent(data)
                        print(f"[WebSocket] Detected intent: {intent}")
                    except Exception as e:
                        print(f"[WebSocket] Intent detection failed: {str(e)}")
                        intent = "general"

                    if intent == "medical":
                        # Switch to medical mode
                        session["mode"] = "medical"
                        session["stage"] = "symptom"
                        session["step"] = Step.AWAITING_SYMPTOMS

                        await websocket.send_json(
                            {
                                "step": Step.AWAITING_SYMPTOMS,
                                "message": "🤒 Describe your symptoms:",
                            }
                        )
                        continue

                    # General chat response
                    try:
                        ai_response = general_chat(
                            data, session["patient_info"], chat_history=chat_history
                        )

                        # Save to conversation history
                        add_conversation(
                            session_id=session["store_session_id"],
                            symptoms=data,
                            insight="general",
                            response=ai_response,
                            timestamp=str(datetime.now()),
                        )

                        await websocket.send_json(
                            {"step": Step.GENERAL_CHAT, "message": ai_response}
                        )
                    except Exception as e:
                        print(f"[WebSocket] General chat error: {str(e)}")
                        await websocket.send_json(
                            {
                                "step": Step.GENERAL_CHAT,
                                "message": f"❌ Error: {str(e)}",
                            }
                        )

            # =====================================================
            # SYMPTOMS ANALYSIS
            # =====================================================
            elif step == Step.AWAITING_SYMPTOMS:
                try:
                    raw_data = {**session["patient_info"], "symptoms": data}
                    patient = process_patient_input(raw_data)

                    context = get_relevant_context(patient)

                    insight_json = generate_insights(
                        patient,
                        context.get("context", ""),
                        medical_history=session.get("medical_history"),
                    )

                    response = generate_patient_response(patient, insight_json)

                    session["last_insight"] = insight_json
                    session["last_response"] = response

                    add_conversation(
                        session_id=session["store_session_id"],
                        symptoms=data,
                        insight=insight_json,
                        response=response,
                        timestamp=str(datetime.now()),
                    )

                    print(f"[WebSocket] Insight generated successfully")

                    await websocket.send_json(
                        {
                            "step": Step.AWAITING_FOLLOWUP,
                            "insight_json": insight_json,
                            "message": response
                            + "\n\n❓ Do you have more symptoms? (yes/no)",
                        }
                    )

                    session["step"] = Step.AWAITING_FOLLOWUP
                    session["stage"] = "await_followup"

                except Exception as e:
                    print(f"[WebSocket] Symptom analysis error: {str(e)}")
                    await websocket.send_json(
                        {
                            "step": Step.AWAITING_SYMPTOMS,
                            "message": f"❌ Error analyzing symptoms: {str(e)}. Try again.",
                        }
                    )

            # =====================================================
            # FOLLOW-UP
            # =====================================================
            elif step == Step.AWAITING_FOLLOWUP:
                if data.lower() in ["yes", "y"]:
                    session["step"] = Step.AWAITING_SYMPTOMS
                    session["stage"] = "symptom"

                    await websocket.send_json(
                        {
                            "step": Step.AWAITING_SYMPTOMS,
                            "message": "🤒 Tell me your additional symptoms.",
                        }
                    )
                elif data.lower() in ["no", "n"]:
                    session["step"] = Step.AWAITING_BOOKING
                    session["stage"] = "booking"

                    await websocket.send_json(
                        {
                            "step": Step.AWAITING_BOOKING,
                            "message": "🏥 Would you like to book an appointment? (yes/no)",
                        }
                    )
                else:
                    await websocket.send_json(
                        {
                            "step": Step.AWAITING_FOLLOWUP,
                            "message": "❌ Please answer yes or no.",
                        }
                    )

            # =====================================================
            # BOOKING DECISION
            # =====================================================
            elif step == Step.AWAITING_BOOKING:
                if data.lower() in ["yes", "y"]:

                    insight = parse_insight(session.get("last_insight", ""))
                    speciality = normalize_speciality(
                        insight.get("primary_specialist")
                        or insight.get("recommended_specialist")
                        or "General Physician"
                    )

                    slot_list = db_booking.build_slots(speciality, doctors)

                    if not slot_list:
                        await websocket.send_json(
                            {
                                "step": Step.GENERAL_CHAT,
                                "message": f"❌ No slots available for {speciality}",
                            }
                        )
                        session["step"] = Step.GENERAL_CHAT
                        session["mode"] = "idle"
                        continue

                    session["available_slots"] = slot_list

                    slots_text = f"🩺 Specialist: {speciality}\n📅 Available Slots:\n\n"
                    for s in slot_list:
                        slots_text += (
                            f"{s['slot_number']}. "
                            f"{s['day']} ({s['date']}) - {s['time_slot']} ({s['doctor']})\n"
                        )

                    slots_text += "\n👉 Enter slot number:"

                    session["step"] = Step.AWAITING_SLOT_SELECTION

                    await websocket.send_json(
                        {
                            "step": Step.AWAITING_SLOT_SELECTION,
                            "message": slots_text,
                            "slots": slot_list,
                        }
                    )

                else:
                    session["step"] = Step.GENERAL_CHAT
                    session["mode"] = "idle"

                    await websocket.send_json(
                        {
                            "step": Step.GENERAL_CHAT,
                            "message": "👍 Okay, continue chatting",
                        }
                    )

            # =====================================================
            # SLOT SELECTION
            # =====================================================
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
                    await websocket.send_json(
                        {"step": Step.AWAITING_BOOKING_CONFIRM, "message": confirm_text}
                    )
                else:
                    await websocket.send_json(
                        {
                            "step": Step.AWAITING_SLOT_SELECTION,
                            "message": f"❌ Invalid choice. Enter 1-{len(slot_list)}.",
                        }
                    )

            # =====================================================
            # BOOKING CONFIRMATION
            # =====================================================
            elif step == Step.AWAITING_BOOKING_CONFIRM:
                if data.lower() in ["yes", "y"]:
                    chosen = session["chosen_slot"]

                    try:
                        appointment_id = create_appointment(
                            patient_id=session["patient_id"],
                            doctor_id=chosen["doctor_id"],
                            slot_id=chosen["slot_id"],
                            target_date=chosen["date"],
                        )

                        record_id = save_consultation_record(
                            appointment_id,
                            session.get("last_insight", ""),
                            session.get("last_response", ""),
                        )

                        session["mode"] = "idle"
                        session["stage"] = None
                        session["last_insight"] = None
                        session["step"] = Step.GENERAL_CHAT

                        await websocket.send_json(
                            {
                                "step": Step.GENERAL_CHAT,
                                "message": (
                                    f"✅ Appointment Confirmed!\n"
                                    f"👨‍⚕️ Doctor: {chosen['doctor']}\n"
                                    f"🩺 Specialist: {chosen['speciality']}\n"
                                    f"📅 {chosen['day']} ({chosen['date']})\n"
                                    f"⏰ Time: {chosen['time_slot']}\n"
                                    f"📄 Consultation ID: {record_id}\n\n"
                                    f"💬 You can continue chatting!"
                                ),
                            }
                        )

                        print(f"[WebSocket] Appointment booked: {appointment_id}")

                    except Exception as e:
                        print(f"[WebSocket] Appointment booking failed: {str(e)}")
                        session["mode"] = "idle"
                        session["stage"] = None
                        session["step"] = Step.GENERAL_CHAT

                        await websocket.send_json(
                            {
                                "step": Step.GENERAL_CHAT,
                                "message": f"❌ Booking Error: {str(e)}\n💬 Continue chatting!",
                            }
                        )
                else:
                    session["mode"] = "idle"
                    session["stage"] = None
                    session["step"] = Step.GENERAL_CHAT

                    await websocket.send_json(
                        {
                            "step": Step.GENERAL_CHAT,
                            "message": "❌ Appointment cancelled. 💬 Continue chatting!",
                        }
                    )

    except WebSocketDisconnect:
        print(f"[WebSocket] Client disconnected: patient {id}")
        active_sessions.pop(ws_session_id, None)
    except Exception as e:
        print(f"[WebSocket] Unexpected error: {str(e)}")
        try:
            await websocket.send_json(
                {"step": "error", "message": f"❌ Server error: {str(e)}"}
            )
        except:
            pass
        active_sessions.pop(ws_session_id, None)
