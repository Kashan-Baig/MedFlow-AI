"""Database models."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    Date,
    Time,
    DateTime,
    Enum,
    Text,
    ARRAY,
    Numeric,
)
from sqlalchemy.orm import relationship
import enum
from .db_connection import Base

# ENUMS :


class AppointmentStatus(str, enum.Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"


class CaseType(str, enum.Enum):
    CONSULTATION = "Consultation"
    FOLLOW_UP = "Follow-up"
    EMERGENCY = "Emergency"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"


class BloodGroup(str, enum.Enum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"


class Gender(str, enum.Enum):
    Male = "Male"
    Female = "Female"


class DayOfWeek(enum.Enum):
    Monday = "Monday"
    Tuesday = "Tuesday"
    Wednesday = "Wednesday"
    Thursday = "Thursday"
    Friday = "Friday"
    Saturday = "Saturday"
    Sunday = "Sunday"


# MODELS :


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String, default=UserRole.PATIENT)
    patient = relationship("Patient", back_populates="user", uselist=False)
    doctor = relationship("Doctor", back_populates="user", uselist=False)
    admin = relationship("Admin", back_populates="user", uselist=False)


class Admin(Base):
    __tablename__ = "admins"
    admin_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    user = relationship("User", back_populates="admin")


class Doctor(Base):
    __tablename__ = "doctors"
    doctor_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    contact_number = Column(String(20))
    gender = Column(Enum(Gender))
    specialization = Column(String(50), nullable=False)
    workload_count = Column(Integer, default=0)
    on_duty_status = Column(Boolean, default=True)

    user = relationship("User", back_populates="doctor")
    slots = relationship("ScheduleSlot", back_populates="doctor")


class Patient(Base):
    __tablename__ = "patients"
    patient_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    contact_number = Column(String(20))
    age = Column(Integer, nullable=False)
    gender = Column(Enum(Gender))
    address = Column(Text)

    user = relationship("User", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient")
    history = relationship("MedicalHistory", back_populates="patient", uselist=False)


# TODO : update this model according to neon db


class ScheduleSlot(Base):
    __tablename__ = "schedule_slots"
    slot_id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.doctor_id"))
    available_days = Column(
        ARRAY(Enum(DayOfWeek, name="day_of_week", create_type=False)), nullable=False
    )
    max_appointments = Column(Integer, default=1, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_locked = Column(Boolean, default=False)
    doctor = relationship("Doctor", back_populates="slots")


class Appointment(Base):
    __tablename__ = "appointments"
    appointment_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id"))
    doctor_id = Column(Integer, ForeignKey("doctors.doctor_id"))
    appointment_date = Column(Date, nullable=False)
    slot_id = Column(Integer, ForeignKey("schedule_slots.slot_id"))
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.PENDING)
    case_type = Column(Enum(CaseType))
    patient = relationship("Patient", back_populates="appointments")
    record = relationship(
        "ConsultationRecord", back_populates="appointment", uselist=False
    )
    precheck = relationship(
        "MedicalPrecheck", back_populates="appointment", uselist=False
    )


class ConsultationRecord(Base):
    __tablename__ = "consultation_records"
    record_id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.appointment_id"))
    observations = Column(Text)
    diagnosis = Column(Text)
    prescribed_actions = Column(Text)

    appointment = relationship("Appointment", back_populates="record")


class MedicalHistory(Base):
    __tablename__ = "medical_history"
    history_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id"), unique=True)
    allergies = Column(ARRAY(String))
    blood_group = Column(Enum(BloodGroup))
    chronic_conditions = Column(ARRAY(String))
    current_medications = Column(ARRAY(String))
    last_updated = Column(Date)
    patient = relationship("Patient", back_populates="history")


class MedicalPrecheck(Base):
    __tablename__ = "medical_prechecks"
    check_id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(
        Integer, ForeignKey("appointments.appointment_id"), nullable=False
    )
    # Vitals
    blood_pressure = Column(String(20))
    temperature = Column(Numeric(precision=4, scale=1))
    pulse_rate = Column(Integer)
    spo2 = Column(Numeric(precision=4, scale=1))
    weight = Column(Numeric(precision=5, scale=2))
    patient_symptoms = Column(ARRAY(String))
    ai_predicted_condition = Column(String(100))
    appointment = relationship("Appointment", back_populates="precheck")
