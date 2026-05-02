import sys
from src.ai.db_services.booking_service import book_appointment
from src.ai.utils.session_store import create_session

session_id = create_session({"mode": "booking", "patient_id": 1, "last_insight": {"primary_specialist": "Pulmonologist"}})
# mock input to instantly exit
import builtins
builtins.input = lambda p: "exit"

try:
    book_appointment(session_id, {"primary_specialist": "Pulmonologist"})
except Exception as e:
    print(e)
