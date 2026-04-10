from fastapi import APIRouter
from app.workflows.patient_flow import run_patient_flow

router = APIRouter()

@router.post("/consult")
def consult(data: dict):
    return run_patient_flow(data)
