"""Entry point for MedFlow AI backend."""
from fastapi import FastAPI
from app.api import patient_routes, admin_routes, doctor_routes

app = FastAPI(title="MedFlow AI")

app.include_router(patient_routes.router, prefix="/patient")
app.include_router(admin_routes.router, prefix="/admin")
app.include_router(doctor_routes.router, prefix="/doctor")

@app.get("/")
def root():
    return {"message": "MedFlow AI is running"}
