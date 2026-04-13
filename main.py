"""Entry point for MedFlow AI backend."""
from fastapi import FastAPI

from src.backend.database import models
from src.backend.database.db_connection import engine
from src.backend.routes import admin_routes, auth, doctor_routes, patient_routes

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MedFlow AI")

app.include_router(patient_routes.router, prefix="/patient")
app.include_router(admin_routes.router, prefix="/admin")
app.include_router(doctor_routes.router, prefix="/doctor")
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "MedFlow AI is running"}
