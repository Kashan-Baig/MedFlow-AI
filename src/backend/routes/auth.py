from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.backend.database import models
from src.backend.database.db_connection import get_db
from src.backend.database.models import UserRole
from src.backend.schemas import all_schema as schemas
from src.backend.core import middleware as security

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=schemas.GenericResponse[schemas.RegisterResponse]
)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    print(user_data)
    db_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pwd = security.hash_password(user_data.password)
    new_user = models.User(
        email=user_data.email, password_hash=hashed_pwd, role=user_data.role
    )
    db.add(new_user)
    db.flush()

    if user_data.role == UserRole.PATIENT:
        if not user_data.age:
            raise HTTPException(status_code=400, detail="Age is required for Patients")
        new_role = models.Patient(
            user_id=new_user.id,
            email=user_data.email,
            full_name=user_data.fullName,
            contact_number=user_data.contact_number,
            gender=user_data.gender,
            age=user_data.age,
        )
    elif user_data.role == UserRole.DOCTOR:
        if not user_data.specialization:
            raise HTTPException(
                status_code=400, detail="Specialization is required for doctors"
            )
        new_role = models.Doctor(
            user_id=new_user.id,
            email=user_data.email,
            full_name=user_data.fullName,
            specialization=user_data.specialization,
            contact_number=user_data.contact_number,
            gender=user_data.gender,
        )
    else:
        new_role = models.Admin(
            user_id=new_user.id,
            email=user_data.email,
            full_name=user_data.fullName,
        )
    db.add(new_role)
    db.commit()
    db.refresh(new_role)

    user_out = schemas.UserOut.model_validate(new_user)
    if user_data.role == UserRole.PATIENT:
        role_out = schemas.PatientAuthOut.model_validate(new_role)
    elif user_data.role == UserRole.DOCTOR:
        role_out = schemas.DoctorAuthOut.model_validate(new_role)
    else:
        role_out = schemas.AdminAuthOut.model_validate(new_role)
    # print(f"Registered new user: {user_out} with role {role_out}")
    return {
        "status_code": 201,
        "message": f"A new {user_data.role.value} registered successfully",
        "data": schemas.RegisterResponse(user=user_out, role=role_out),
    }


@router.post("/login", response_model=schemas.GenericResponse[schemas.LoginResponse])
def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.email.ilike(login_data.email)).first()
    if not user or not security.verify_password(
        login_data.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # checking if this role exist in the respected roles tables
    if user.role == UserRole.PATIENT:
        role_data = user.patient
        if not role_data:
            raise HTTPException(status_code=400, detail="Patient profile not found")

    elif user.role == UserRole.DOCTOR:
        role_data = user.doctor
        if not role_data:
            raise HTTPException(status_code=400, detail="Doctor profile not found")
    else:
        role_data = user.admin
        if not role_data:
            raise HTTPException(status_code=400, detail="Admin profile not found")

    # 3. Generate Token
    if user.role == UserRole.PATIENT:
        role_out = schemas.PatientAuthOut.model_validate(role_data)
    elif user.role == UserRole.DOCTOR:
        role_out = schemas.DoctorAuthOut.model_validate(role_data)
    else:
        role_out = schemas.AdminAuthOut.model_validate(role_data)

    role_id = None
    if user.role == UserRole.PATIENT:
        role_id = role_data.patient_id
    elif user.role == UserRole.DOCTOR:
        role_id = role_data.doctor_id
    else:
        role_id = role_data.admin_id

    access_token = security.create_access_token(
        data={
            "sub": user.email,
            "role": user.role,
            "user_id": user.id,
            "role_id": role_id,
        }
    )
    user_out = schemas.UserOut.model_validate(user)
    return {
        "status_code": 200,
        "message": "User logged in successfully",
        "data": schemas.LoginResponse(
            user=user_out, role=role_out, access_token=access_token
        ),
    }
