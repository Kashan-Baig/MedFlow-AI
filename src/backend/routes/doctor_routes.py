from fastapi import APIRouter, Depends, HTTPException
import src.ai.db_services.db_services as db_service
import src.backend.core.middleware as security

router = APIRouter(prefix="/doctor", tags=["Doctor"])


# @router.get("/appointments")
# def get_appointments_by_id(doctor_id: int):
#     return {
#         "status_code": 200,
#         "message": "Appointments fetched successfully",
#         "data": db_service.get_appointments_by_doctor_id(doctor_id)
#     }


@router.get("/doctors_by_speciality")
def get_doctors_by_speciality(speciality: str):
    return {
        "status_code": 200,
        "message": "Doctors fetched successfully",
        "data": db_service.get_doctors_by_speciality(
            speciality, from_doctor_router=True
        ),
    }


@router.get("/get_my_patients")
def get_patients_by_doctor_id(
    current_doctor: dict = Depends(security.get_current_doctor),
):
    doctor_id = current_doctor.get("role_id")
    return {
        "status_code": 200,
        "message": "Patients fetched successfully",
        "data": db_service.get_patients_by_doctor_id(doctor_id),
    }
