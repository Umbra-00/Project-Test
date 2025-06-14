from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from . import crud, schemas
from ...utils import auth_utils
from src.data_engineering.db_utils import get_db
from src.utils.logging_utils import setup_logging

# Setup logging
logger = setup_logging(__name__)

# --- Configuration for JWT ---
SECRET_KEY = "your-secret-key"  # Replace with a strong, securely generated secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- JWT Token Functions ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(db: Session, user_identifier: str, password: str):
    user = crud.get_user_by_user_identifier(db, user_identifier=user_identifier)
    if not user:
        return None
    if not auth_utils.verify_password(password, user.password_hash):
        return None
    return user

# --- Dependency for Current User ---
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_identifier: str = payload.get("sub")
        if user_identifier is None:
            raise credentials_exception
        token_data = schemas.TokenData(user_identifier=user_identifier)
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_user_identifier(db, user_identifier=token_data.user_identifier)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: schemas.User = Depends(get_current_user)):
    if not current_user.user_identifier:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user 