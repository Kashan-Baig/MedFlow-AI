from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.backend.database.db_connection import get_db
from src.backend.database import models
from src.backend.core.middleware import get_current_admin

router = APIRouter()

@router.get("/all_users")
def get_all_users(db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)):
    result = db.execute(text("""
        SELECT 
            id, 
            email, 
            role 
        FROM users
    """)).fetchall()

    users = [dict(row._mapping) for row in result]

    return {
        "status": "success",
        "count": len(users),
        "data": users
    }