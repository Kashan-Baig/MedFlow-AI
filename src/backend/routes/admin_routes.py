from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.backend.database.db_connection import get_db
from src.backend.database import models
from src.backend.core.middleware import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin"])
