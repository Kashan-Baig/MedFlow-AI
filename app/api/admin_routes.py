from fastapi import APIRouter
from app.workflows.admin_flow import run_admin_flow

router = APIRouter()

@router.post("/intake")
def intake(data: dict):
    return run_admin_flow(data)
