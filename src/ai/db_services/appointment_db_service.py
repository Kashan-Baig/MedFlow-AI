from datetime import datetime, timedelta, date as DateType

from sqlalchemy import text
from src.backend.database.db_connection import get_db
from src.backend.database.models import (
    Appointment,
    Slot,
    SlotBooking,
    SlotException,
    AppointmentStatus,
    CaseType,
)


# =========================
# UTIL: CALCULATE EXPECTED TIME
# =========================
def calculate_queue_and_time(slot: Slot, queue_number: int, target_date):
    """
    Given a slot and a 1-based queue_number, return the expected time.

    Example: slot 09:00–11:00, max=10 → 12 min/patient.
             Queue #6 → 09:00 + (5 × 12 min) = 10:00 AM
    """
    dummy_date = datetime(2000, 1, 1)  # date doesn't matter, only time arithmetic
    slot_start = datetime.combine(dummy_date, slot.start_time)
    slot_end = datetime.combine(dummy_date, slot.end_time)

    slot_duration_minutes = (slot_end - slot_start).seconds // 60
    time_per_patient = slot_duration_minutes / slot.max_appointments

    offset = timedelta(minutes=(queue_number - 1) * time_per_patient)
    expected_time = (slot_start + offset).time()
    return expected_time


# =========================
# CHECK: CAN BOOK (legacy helper kept for reference)
# =========================
def can_book_appointment(db, slot_id, target_date):
    slot = db.query(Slot).filter(Slot.slot_id == slot_id).first()
    booked_count = (
        db.query(Appointment)
        .filter(
            Appointment.slot_id == slot_id,
            Appointment.appointment_date == target_date,
            Appointment.status != AppointmentStatus.CANCELLED,
        )
        .count()
    )
    return booked_count < slot.max_appointments


# =========================
# MAIN: CREATE APPOINTMENT  (new 6-step flow)
# =========================
def create_appointment(patient_id, doctor_id, slot_id, target_date):
    db = get_db()
    try:
        exception = (
            # ── Step 1: Block if doctor has a SlotException on this date ──────────
            db.query(SlotException)
            .filter(
                SlotException.slot_id == slot_id,
                SlotException.exception_date == target_date,
            )
            .first()
        )
        if exception:
            return f"Doctor is on leave on {target_date} ({exception.reason.value})"
        # ── Step 2: Get or create the SlotBooking for (slot, date) ───────────
        slot_booking = (
            db.query(SlotBooking)
            .filter(
                SlotBooking.slot_id == slot_id,
                SlotBooking.booking_date == target_date,
            )
            .first()
        )
        if not slot_booking:
            slot_booking = SlotBooking(
                slot_id=slot_id,
                booking_date=target_date,
                booked_count=0,
            )
            db.add(slot_booking)
            db.flush()  # get booking_id without a full commit

        # ── Step 3: Check capacity ─────────────────────────────────────────────
        slot = db.query(Slot).filter(Slot.slot_id == slot_id).first()
        if not slot:
            return "Slot not found"

        if slot_booking.booked_count >= slot.max_appointments:
            return "Slot is already full"

        # ── Step 4: Calculate queue number & expected time ─────────────────────
        queue_number = slot_booking.booked_count + 1
        expected_time = calculate_queue_and_time(slot, queue_number, target_date)

        # ── Step 5: Insert the Appointment ────────────────────────────────────
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            slot_id=slot_id,
            slot_booking_id=slot_booking.booking_id,
            appointment_date=target_date,
            queue_number=queue_number,
            expected_time=expected_time,
            status=AppointmentStatus.CONFIRMED,
            case_type=CaseType.CONSULTATION,
        )
        db.add(appointment)
        db.flush()  # get appointment_id

        # ── Step 6: Increment booked_count ────────────────────────────────────
        slot_booking.booked_count += 1

        db.commit()
        db.refresh(appointment)

        return {
            "appointment_id": appointment.appointment_id,
            "queue_number": queue_number,
            "expected_time": str(expected_time),
        }

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


# =========================
# GET: APPOINTMENTS BY PATIENT
# =========================
def get_appointments_by_patient_id(patient_id):
    db = get_db()
    try:
        query = text(
            """
            SELECT
                a.appointment_id,
                a.status,
                a.case_type,
                a.appointment_date,
                a.queue_number,
                a.expected_time,
                s.start_time           AS start_time,
                s.end_time             AS end_time,
                sb.booked_count        AS total_booked_for_day,
                d.full_name            AS doctor_name,
                d.specialization       AS doctor_specialization,
                p.full_name            AS patient_name
            FROM appointments a
            JOIN doctors  d  ON a.doctor_id      = d.doctor_id
            JOIN patients p  ON a.patient_id     = p.patient_id
            JOIN slots    s  ON a.slot_id         = s.slot_id
            LEFT JOIN slot_bookings sb
                          ON a.slot_booking_id   = sb.booking_id
            WHERE a.patient_id = :patient_id
            ORDER BY a.appointment_id DESC;
        """
        )
        result = db.execute(query, {"patient_id": patient_id}).fetchall()
        return [dict(row._mapping) for row in result]
    finally:
        db.close()


# =========================
# GET: AVAILABLE SLOTS RANGE
# =========================
def get_available_slots_range(
    start_date: DateType = None, end_date: DateType = None, doctor_id: int = None
):
    db = get_db()
    try:
        if not start_date:
            start_date = DateType.today()
        if not end_date:
            end_date = start_date + timedelta(days=30)

        if start_date > end_date:
            return {
                "status": "error",
                "message": "start_date cannot be greater than end_date",
            }

        result = db.execute(
            text(
                """
            WITH date_series AS (
                SELECT generate_series(:start_date, :end_date, INTERVAL '1 day')::date AS slot_date
            )

            SELECT
                ds.slot_date,
                s.slot_id,
                s.start_time,
                s.end_time,
                s.max_appointments,

                COALESCE(sb.booked_count, 0) AS booked_count,
                (s.max_appointments - COALESCE(sb.booked_count, 0)) AS remaining_slots,

                d.doctor_id,
                d.full_name AS doctor_name,
                d.specialization

            FROM date_series ds

            JOIN slots s
                ON TO_CHAR(ds.slot_date, 'FMDay') = ANY (s.available_days::TEXT[])

            JOIN doctors d
                ON s.doctor_id = d.doctor_id

            LEFT JOIN slot_bookings sb
                ON s.slot_id = sb.slot_id
                AND sb.booking_date = ds.slot_date

            WHERE NOT EXISTS (
                SELECT 1
                FROM slot_exceptions se
                WHERE se.slot_id = s.slot_id
                  AND se.exception_date = ds.slot_date
            )

            AND (s.max_appointments - COALESCE(sb.booked_count, 0)) > 0

            -- ✅ optional doctor filter
            AND (:doctor_id IS NULL OR s.doctor_id = :doctor_id)

            ORDER BY ds.slot_date, s.start_time
            """
            ),
            {
                "start_date": start_date,
                "end_date": end_date,
                "doctor_id": doctor_id,  # ✅ pass param
            },
        ).fetchall()

        slots = []
        for row in result:
            r = dict(row._mapping)
            # Ensure date and time are strings for consistent frontend matching
            slots.append(
                {
                    **r,
                    "slot_date": (
                        r["slot_date"].strftime("%Y-%m-%d")
                        if hasattr(r["slot_date"], "strftime")
                        else str(r["slot_date"])
                    ),
                    "start_time": (
                        r["start_time"].strftime("%H:%M")
                        if hasattr(r["start_time"], "strftime")
                        else str(r["start_time"])[:5]
                    ),
                    "end_time": (
                        r["end_time"].strftime("%H:%M")
                        if hasattr(r["end_time"], "strftime")
                        else str(r["end_time"])[:5]
                    ),
                }
            )

        return slots
    finally:
        db.close()
