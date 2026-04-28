from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import src.backend.core.middleware as security
from src.backend.database.db_connection import get_db
from src.backend.core.middleware import get_current_user
from src.backend.core.middleware import get_current_admin


router = APIRouter(prefix="/user", tags=["user"])


@router.get("/user_data")
def get_single_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):

    result = db.execute(
        text(
            """
        SELECT 
            id,
            email,
            password_hash,
            role
        FROM users
        WHERE id = :id
    """
        ),
        {"id": id},
    ).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = dict(result._mapping)

    return {"status": "success", "data": user_data}


@router.get("/all_users")
def get_all_users(
    db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)
):
    result = db.execute(
        text(
            """
        SELECT 
            id, 
            email, 
            role 
        FROM users
    """
        )
    ).fetchall()

    users = [dict(row._mapping) for row in result]

    return {"status": "success", "count": len(users), "data": users}

