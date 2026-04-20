"""Entry point for MedFlow AI backend."""

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from src.backend.database import models
from src.backend.database.db_connection import engine
from src.backend.routes import (
    admin_routes,
    auth,
    doctor_routes,
    patient_routes,
    chat_ws,
)

# This command tells SQLAlchemy:
# "Check the DB. If these tables don't exist, create them now."
models.Base.metadata.create_all(bind=engine)


app = FastAPI(title="MedFlow AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # In development, you can allow all origins or specifically ["http://localhost:8080", "http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods like GET, POST, OPTIONS
    allow_headers=["*"],  # Allows all headers
)

api_v1 = APIRouter(prefix="/api/v1")

api_v1.include_router(patient_routes.router)
api_v1.include_router(admin_routes.router)
api_v1.include_router(doctor_routes.router)
api_v1.include_router(auth.router)

# Web Sockets
api_v1.include_router(chat_ws.router)

app.include_router(api_v1)


@app.get("/")
def root():
    return {"message": "MedFlow AI is running"}
