sessions = {}
session_counter = 1

def create_session(patient_info, user_id=None):
    """
    Create a new session (visit)

    user_id → for future DB integration
    """
    global session_counter

    session_id = session_counter

    sessions[session_id] = {
        "session_id": session_id,
        "user_id": user_id,  
        "patient_info": patient_info,
        "conversation": [],
        "appointment": {
            "doctor": None,
            "speciality": None,
            "day": None,
            "time_slot": None,
            "status": None
        }
    }

    session_counter += 1
    return session_id

def add_conversation(session_id, symptoms, insight, response, timestamp):

    session = sessions.get(session_id)
    if isinstance(insight, dict):
        specialist = (
            insight.get("recommended_specialist")
            or insight.get("specialist")
            or insight.get("diagnosis", {}).get("specialist")
            or "General Physician"
        )

        insight_text = f"Patient may need to consult a {specialist}"

    else:
        specialist = "General Physician"
        insight_text = "Basic consultation recommended"
    session["conversation"].append({
        "symptoms": symptoms,
        "insight": insight_text,
        "specialist": specialist,
        "timestamp": timestamp
    })

def update_appointment(session_id, appointment_data):
    """
    Update appointment details inside session
    """

    session = sessions.get(session_id)
    if not session:
        return

    session["appointment"].update(appointment_data)

def get_session(session_id):
    return sessions.get(session_id)