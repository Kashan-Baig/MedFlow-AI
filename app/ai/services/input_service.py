import re
from dataclasses import dataclass
from typing import Optional, Dict


# =========================
# DATA MODEL
# =========================
@dataclass
class PatientInput:
    name: str
    email: Optional[str]
    phone: str
    age: Optional[int]
    gender: Optional[str]
    symptoms: str


# =========================
# VALIDATION HELPERS
# =========================
def validate_email(email: str) -> bool:
    if not email:
        return True
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    # basic Pakistan + international support
    pattern = r"^[0-9+\-\s]{10,15}$"
    return re.match(pattern, phone) is not None


# =========================
# CLEANING FUNCTION
# =========================
def clean_text(text: str) -> str:
    if not text:
        return ""
    return text.strip().lower()


# =========================
# MAIN SERVICE FUNCTION
# =========================
def process_patient_input(data: Dict) -> PatientInput:
    """
    Takes raw frontend input and converts it into structured format
    """

    name = clean_text(data.get("name", "Unknown"))
    email = data.get("email")
    phone = data.get("phone", "")
    age = data.get("age")
    gender = clean_text(data.get("gender", "unknown"))
    symptoms = data.get("symptoms", "")

    # -------------------------
    # VALIDATION CHECKS
    # -------------------------
    if not name:
        raise ValueError("Name is required")

    if not validate_phone(phone):
        raise ValueError("Invalid phone number format")

    if email and not validate_email(email):
        raise ValueError("Invalid email format")

    if not symptoms:
        raise ValueError("Symptoms cannot be empty")

    # -------------------------
    # RETURN STRUCTURED OBJECT
    # -------------------------
    return PatientInput(
        name=name,
        email=email,
        phone=phone,
        age=age,
        gender=gender,
        symptoms=symptoms
    )


# =========================
# OPTIONAL: DICT OUTPUT (FOR API)
# =========================
def to_dict(patient: PatientInput) -> Dict:
    return {
        "name": patient.name,
        "email": patient.email,
        "phone": patient.phone,
        "age": patient.age,
        "gender": patient.gender,
        "symptoms": patient.symptoms
    }