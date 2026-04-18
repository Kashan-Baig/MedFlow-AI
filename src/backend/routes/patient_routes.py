from fastapi import APIRouter, Depends

# from workflows.patient_flow import run_patient_flow
import src.ai.db_services.db_services as db_service
import src.backend.core.middleware as security

router = APIRouter(prefix="/patient", tags=["Patient"])


@router.get("/appointments")
def get_patient_appointments(
    current_patient: dict = Depends(security.get_current_patient),
):
    patient_id = current_patient.get("role_id")
    return {
        "status_code": 200,
        "message": "Appointments fetched successfully",
        "data": db_service.get_appointments_by_patient_id(patient_id),
    }
