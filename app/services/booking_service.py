from app.utils.session_store import get_session, update_appointment
from app.utils.doctor_store import doctors


def normalize_day(day):
    return day.strip().capitalize()


def normalize_time(time_slot):
    return (
        time_slot.strip()
        .replace("AM", " AM")
        .replace("PM", " PM")
        .replace("  ", " ")
    )


def book_appointment(session_id, insight):

    session = get_session(session_id)

    if not session:
        return {"error": "Session not found"}

    # =========================
    # PARSE INSIGHT
    # =========================
    if isinstance(insight, str):
        import json, re
        try:
            match = re.search(r"```(?:json)?\n?(.*?)```", insight, flags=re.DOTALL)
            raw_json = match.group(1).strip() if match else insight.strip()
            insight = json.loads(raw_json)
        except Exception:
            pass

    if isinstance(insight, dict):
        speciality = (
            insight.get("recommended_specialist")
            or insight.get("specialist")
            or insight.get("diagnosis", {}).get("specialist")
            or "General Physician"
        )
    else:
        print("⚠️ Insight not structured → using General Physician")
        speciality = "General Physician"

    print(f"\n🩺 Recommended Specialist: {speciality}")

    # =========================
    # GET DAY
    # =========================
    day_input = input("📅 Enter preferred day (e.g., Monday): ")
    day = normalize_day(day_input)

    # =========================
    # GET AVAILABLE DOCTORS
    # =========================
    available_doctors = [
        d for d in doctors
        if any(s.lower() == speciality.lower() for s in d["speciality"])
        and any(dy.lower() == day.lower() for dy in d["available_days"])
        ]

    if not available_doctors:
        return {"error": f"No doctors available for {speciality} on {day}"}

    # =========================
    # SHOW TIME SLOTS
    # =========================
    print(f"\n⏰ Available time slots on {day}:")

    all_slots = set()
    for d in available_doctors:
        for slot in d["time_slots"]:
            all_slots.add(slot)

    all_slots = list(all_slots)

    for i, slot in enumerate(all_slots, 1):
        print(f"{i}. {slot}")

    # =========================
    # USER SELECT SLOT
    # =========================
    choice = input("\n👉 Select a slot number: ").strip()

    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(all_slots):
        return {"error": "Invalid slot selection"}

    time_slot = all_slots[int(choice) - 1]

    # =========================
    # FIND DOCTOR
    # =========================
    doctor = None
    for d in available_doctors:
        if time_slot in d["time_slots"]:
            doctor = d
            break

    if not doctor:
        return {
            "error": "No doctor available for selected day and time slot"
        }

    # =========================
    # CONFIRM
    # =========================
    print("\n👨‍⚕️ Doctor Available:")
    print(f"Name: {doctor['name']}")
    print(f"Speciality: {doctor['speciality']}")
    print(f"Day: {day}")
    print(f"Time: {time_slot}")

    confirm = input("\n✅ Do you want to confirm this appointment? (yes/no): ").strip().lower()

    if confirm not in ["yes", "y"]:
        return {
            "error": "Appointment not confirmed by user"
        }

    # =========================
    # SAVE APPOINTMENT
    # =========================
    appointment_data = {
        "doctor": doctor["name"],
        "speciality": doctor["speciality"],
        "day": day,
        "time_slot": time_slot,
        "status": "confirmed"
    }

    update_appointment(session_id, appointment_data)

    return appointment_data