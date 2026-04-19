from enum import Enum

class Step(str, Enum):
    AWAITING_NAME = "awaiting_name"
    AWAITING_EMAIL = "awaiting_email"
    AWAITING_AGE = "awaiting_age"
    AWAITING_GENDER = "awaiting_gender"
    AWAITING_PHONE = "awaiting_phone"
    GENERAL_CHAT = "general_chat"
    AWAITING_SYMPTOMS = "awaiting_symptoms"
    AWAITING_FOLLOWUP = "awaiting_followup"
    AWAITING_BOOKING = "awaiting_booking"
    AWAITING_SLOT_SELECTION = "awaiting_slot_selection"
    AWAITING_BOOKING_CONFIRM = "awaiting_booking_confirm"
    DONE = "done"
