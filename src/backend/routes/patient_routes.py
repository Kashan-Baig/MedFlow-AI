from fastapi import APIRouter
# from workflows.patient_flow import run_patient_flow
import src.ai.db_services.db_services as db_service


router = APIRouter(prefix="/patient", tags=["Patient"])


@router.get("/appointments")
def get_appointments_by_id(patient_id: int):
    return {
        "status_code": 200,
        "message": "Appointments fetched successfully",
        "data": db_service.get_appointments_by_patient_id(patient_id)
    } 
