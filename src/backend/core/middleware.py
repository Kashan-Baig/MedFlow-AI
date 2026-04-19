from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

load_dotenv()

security_scheme = HTTPBearer()

# Configuration from .env
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# Password Hashing Setup (Bcrypt directly)


def hash_password(password: str) -> str:
    """Transforms plain password into a secure hash."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks if the provided password matches the stored hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generates a JWT token for the Flutter app to store."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


def get_current_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admins only."
        )
    return payload

def extract_user_from_access_token(token: str) -> Optional[dict]:
    """Extracts and verifies user data from a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

# This tells Swagger: "Just give me a text box for the Authorization header"
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


def get_current_user(token: str = Depends(api_key_header)) -> dict:
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")
    clean_token = token.replace("Bearer ", "") if "Bearer " in token else token
    user_data = extract_user_from_access_token(clean_token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token or expired")
    return user_data


def get_current_doctor(user: dict = Depends(get_current_user)) -> dict:
    if str(user.get("role")).lower() != "doctor":
        raise HTTPException(status_code=403, detail="Not authorized as doctor")
    return user


def get_current_patient(user: dict = Depends(get_current_user)) -> dict:
    if str(user.get("role")).lower() != "patient":
        raise HTTPException(status_code=403, detail="Not authorized as patient")
    return user

