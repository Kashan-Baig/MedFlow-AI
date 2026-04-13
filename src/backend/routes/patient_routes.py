from fastapi import APIRouter
# from workflows.patient_flow import run_patient_flow

router = APIRouter()

@router.post("/consult")
def consult(data: dict):
    return {}
