from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.api.v1 import crud, schemas
from src.utils.auth_utils import verify_password
from src.api.v1.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_current_active_user
from src.data_engineering.db_utils import get_db
from src.utils.logging_utils import setup_logging

router = APIRouter()
logger = setup_logging(__name__)


@router.post("/register", response_model=schemas.User, summary="Register a new user", tags=["User Management"])
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_user_identifier(db, user_identifier=user.user_identifier)
    if db_user:
        raise HTTPException(status_code=400, detail="User ID already registered")
    return crud.create_user(db=db, user=user)


@router.post("/token", response_model=schemas.Token, summary="Login and retrieve access token", tags=["Authentication"])
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = crud.get_user_by_user_identifier(db, user_identifier=form_data.username)

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user ID or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.user_identifier, "role": user.role}, expires_delta=access_token_expires
    )
    logger.info(f"User {user.user_identifier} logged in successfully.")
    return {"access_token": access_token, "token_type": "bearer"}


@router.put("/update-profile", response_model=schemas.User, summary="Update user profile", tags=["User Management"])
def update_user_profile(
    user_update: schemas.UserUpdate, 
    db: Session = Depends(get_db), 
    current_user: schemas.User = Depends(get_current_active_user)
):
    db_user = crud.get_user(db, user_id=current_user.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    updated_user = crud.update_user_profile(db, user_id=current_user.id, user_update=user_update)
    logger.info(f"User {current_user.user_identifier} profile updated successfully.")
    return updated_user
