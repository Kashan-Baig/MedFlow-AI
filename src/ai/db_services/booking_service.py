from src.ai.utils.session_store import get_session, update_appointment
from datetime import datetime, timedelta
import json, re

from src.ai.db_services.appointment_db_service import create_appointment
from src.ai.db_services.doctor_service import get_doctors_by_speciality


# =========================
# UTIL: DATE FROM DAY
# =========================
def get_next_date_for_day(day_name: str):
    days_map = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6
    }

    today = datetime.now()
    target_day = days_map[day_name]

    days_ahead = target_day - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7

    return (today + timedelta(days=days_ahead)).date()


# =========================
# UTIL: PARSE INSIGHT
# =========================
def parse_insight(insight):
    if isinstance(insight, str):
        try:
            match = re.search(r"```(?:json)?\n?(.*?)```", insight, re.DOTALL)
            raw = match.group(1) if match else insight
            return json.loads(raw)
        except:
            return {}
    return insight if isinstance(insight, dict) else {}


# =========================
# NORMALIZE SPECIALITY
# =========================
def normalize_speciality(text):
    if not text:
        return "General Physician"

    text = text.lower().replace("-", " ").strip()
    return text.split("/")[0].title()



# =========================
# MAIN BOOKING FUNCTION
# =========================
def book_appointment(session_id, insight):

    session = get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    insight = parse_insight(insight)

    speciality = normalize_speciality(
        insight.get("primary_specialist")
        or insight.get("recommended_specialist")
        or insight.get("specialist")
        or "General Physician"
    )

    print(f"\n🩺 Recommended Specialist: {speciality}")

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    slot_map = []
    print("\n📅 Available Slots:\n")

    count = 1 
    available_doctors_by_day = get_doctors_by_speciality(speciality)
    
    for day in days:
        available_doctors = available_doctors_by_day.get(day, [])

        for doc in available_doctors:
            # IMPORTANT FIX: use DB arrays directly (safe loop)
            for i in range(len(doc["time_slots"])):
                slot_id = doc["slot_ids"][i]
                time_slot = doc["time_slots"][i]
                slot_map.append({
                    "doctor": doc,
                    "day": day,
                    "time_slot": time_slot,
                    "slot_id": slot_id
                })
                print(
                    f"{count}. {day} - {time_slot} - {doc['name']}"
                )
                count += 1

    if not slot_map:
        return {"error": f"No slots available for {speciality}"}

    # =========================
    # USER SELECTION
    # =========================
    choice = input("\n👉 Select slot number: ").strip()

    if not choice.isdigit() or not (1 <= int(choice) <= len(slot_map)):
        return {"error": "Invalid slot selection"}

    selected = slot_map[int(choice) - 1]

    doctor = selected["doctor"]
    day = selected["day"]
    time_slot = selected["time_slot"]
    slot_id = selected["slot_id"]

    print("\n👨‍⚕️ Appointment Details:")
    print(f"Doctor: {doctor['name']}")
    print(f"Speciality: {speciality}")
    print(f"Day: {day}")
    print(f"Time: {time_slot}")
    print(f"Slot ID: {slot_id}")

    confirm = input("\n✅ Confirm appointment? (yes/no): ").lower()

    if confirm not in ["yes", "y"]:
        return {"error": "Appointment cancelled"}

    # =========================
    # FINAL VALIDATION
    # =========================
    patient_id = session.get("patient_id")

    if not patient_id:
        return {"error": "Patient ID not found in session"}

    # =========================
    # CREATE APPOINTMENT
    # =========================
    appointment_id = create_appointment(
        patient_id=patient_id,
        doctor_id=doctor["id"],
        slot_id=slot_id,
        target_date=get_next_date_for_day(day)
    )
    if appointment_id == "Slot is already full":
        return {
            "error": "Slot is already full",
        }

    appointment_data = {
        "appointment_id": appointment_id,
        "doctor": doctor["name"],
        "speciality": speciality,
        "day": day,
        "time_slot": time_slot,
        "status": "confirmed"
    }

    update_appointment(session_id, appointment_data)

    return appointment_data


def build_slots(speciality, doctors):
    days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    slot_list = []
    count = 1

    available_doctors_by_day = get_doctors_by_speciality(speciality)

    for day in days:
        available_doctors = available_doctors_by_day.get(day, [])

        for doc in available_doctors:
            for i in range(len(doc["time_slots"])):
                slot_list.append({
                    "slot_number": count,
                    "doctor": doc["name"],
                    "doctor_id": doc["id"],
                    "speciality": speciality, 
                    "slot_id": doc["slot_ids"][i],
                    "day": day,
                    "time_slot": doc["time_slots"][i],
                    "date": str(get_next_date_for_day(day)),
                })
                count += 1

    return slot_list