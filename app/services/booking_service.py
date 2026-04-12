from app.utils.session_store import get_session, update_appointment
from app.utils.doctor_store import doctors
from datetime import datetime, timedelta
import json, re


# =========================
# UTIL: GET DATE FOR DAY
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
# UTIL: NEXT 7 DAYS
# =========================
def get_next_7_days():
    today = datetime.now()
    return [(today + timedelta(days=i)).strftime("%A") for i in range(7)]


# =========================
# PARSE INSIGHT SAFELY
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
# MAIN BOOKING FUNCTION
# =========================
def book_appointment(session_id, insight):

    session = get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    insight = parse_insight(insight)

    # =========================
    # EXTRACT SPECIALIST (FIXED)
    # =========================
    speciality = (
        insight.get("primary_specialist")
        or insight.get("recommended_specialist")
        or insight.get("specialist")
        or "General Physician"
    )

    print(f"\n🩺 Recommended Specialist: {speciality}")

    # =========================
    # NEXT 7 DAYS
    # =========================
    next_days = get_next_7_days()

    slot_map = []
    print("\n📅 Available Slots (Next 7 Days):\n")

    count = 1

    for day in next_days:
        for doc in doctors:

            if any(s.lower() == speciality.lower() for s in doc["speciality"]):

                if day in doc["available_days"]:

                    date = get_next_date_for_day(day)

                    for time_slot in doc["time_slots"]:
                        slot_map.append((doc, day, date, time_slot))

                        print(
                            f"{count}. {day} ({date}) - {time_slot} ({doc['name']})"
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

    doctor, day, date, time_slot = slot_map[int(choice) - 1]

    # =========================
    # CONFIRMATION
    # =========================
    print("\n👨‍⚕️ Appointment Details:")
    print(f"Doctor: {doctor['name']}")
    print(f"Speciality: {speciality}")
    print(f"Day: {day}")
    print(f"Date: {date}")
    print(f"Time: {time_slot}")

    confirm = input("\n✅ Confirm appointment? (yes/no): ").lower()

    if confirm not in ["yes", "y"]:
        return {"error": "Appointment cancelled"}

    # =========================
    # SAVE APPOINTMENT
    # =========================
    appointment_data = {
        "doctor": doctor["name"],
        "speciality": speciality,
        "day": day,
        "date": str(date),
        "time_slot": time_slot,
        "status": "confirmed"
    }

    update_appointment(session_id, appointment_data)

    return appointment_data