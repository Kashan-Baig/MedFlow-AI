from fastapi import APIRouter
# from workflows.admin_flow import run_admin_flow

router = APIRouter()

@router.post("/intake")
def intake(data: dict):
    return {}
