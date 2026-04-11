"""Entry point for MedFlow AI backend."""
from fastapi import FastAPI
from api.routes import patient_routes, admin_routes, doctor_routes, auth
from database.db_connection import engine
from database import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MedFlow AI")

app.include_router(patient_routes.router, prefix="/patient")
app.include_router(admin_routes.router, prefix="/admin")
app.include_router(doctor_routes.router, prefix="/doctor")
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "MedFlow AI is running"}
