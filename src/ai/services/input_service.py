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
def validate_name(name: str) -> bool:
    return bool(name) and len(name.strip()) >= 2


def validate_email(email: str) -> bool:
    if not email:
        return True
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    # Pakistan-friendly + international
    pattern = r"^[0-9+\-\s]{10,15}$"
    return re.match(pattern, phone) is not None


def validate_age(age) -> bool:
    try:
        age = int(age)
        return 0 < age < 120
    except:
        return False


def validate_gender(gender: str) -> bool:
    return gender.lower() in ["male", "female"]


# =========================
# CLEANING FUNCTION
# =========================
def clean_text(text: str) -> str:
    if not text:
        return ""
    return text.strip()


# =========================
# MAIN SERVICE FUNCTION
# =========================
def process_patient_input(data: Dict) -> PatientInput:
    """
    Takes raw frontend input and converts it into structured format
    """

    name = clean_text(data.get("name", ""))
    email = data.get("email")
    phone = clean_text(data.get("phone", ""))
    age = data.get("age")
    gender = clean_text(data.get("gender", "")).lower()
    symptoms = clean_text(data.get("symptoms", ""))

    # -------------------------
    # VALIDATION CHECKS
    # -------------------------
    if not validate_name(name):
        raise ValueError("Invalid name (min 2 characters required)")

    if not validate_phone(phone):
        raise ValueError("Invalid phone number format")

    if email and not validate_email(email):
        raise ValueError("Invalid email format")

    if not validate_age(age):
        raise ValueError("Age must be a number between 1 and 120")

    if not validate_gender(gender):
        raise ValueError("Gender must be 'male' or 'female'")

    if not symptoms:
        raise ValueError("Symptoms cannot be empty")

    # -------------------------
    # RETURN STRUCTURED OBJECT
    # -------------------------
    return PatientInput(
        name=name,
        email=email,
        phone=phone,
        age=int(age),
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