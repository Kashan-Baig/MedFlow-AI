from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db_connection import get_db
from app.database import models
from app.schemas import all_schema as schemas
from app.api.core import middleware as security
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=schemas.GenericResponse[schemas.UserOut])
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    # 2. Hash and Save
    hashed_pwd = security.hash_password(user_data.password)
    new_user = models.User(
        email=user_data.email,
        password_hash=hashed_pwd,
        role=user_data.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "status_code": 201,
        "message": "User registered successfully",
        "data": new_user
    }

@router.post("/login", response_model=schemas.GenericResponse[schemas.LoginResponse])
def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == login_data.email).first()
    if not user or not security.verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if(user.role != login_data.role):
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"this email is not registered as {login_data.role.value}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # 3. Generate Token
    access_token = security.create_access_token(
        data={"sub": user.email, "role": user.role}
    )
    
    return {
        "status_code": 200,
        "message": "User logged in successfully",
        "data": {
            "user" : user,
            "access_token": access_token,}
    }


