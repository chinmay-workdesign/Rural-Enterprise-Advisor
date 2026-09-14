from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import crud, models
from app.auth.security import hash_password, verify_password, create_access_token, decode_access_token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

COOKIE_NAME = "sca_auth_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days

class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    email: str
    password: str = Field(min_length=6, description="Password must be at least 6 characters")
    full_name: str = Field(min_length=2)
    role: str = Field(default="FIELD_OFFICER")
    district: Optional[str] = "Belagavi"
    badge_number: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    district: Optional[str] = None
    badge_number: Optional[str] = None
    is_active: bool

def _set_auth_cookie(response: Response, token: str, request: Optional[Request] = None):
    is_secure = False
    if request:
        proto = request.headers.get("x-forwarded-proto", "").lower()
        is_secure = (proto == "https" or request.url.scheme == "https")
    if settings.ENVIRONMENT.lower() in ["production", "staging"]:
        is_secure = True

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        path="/",
        httponly=True,
        samesite="lax",
        secure=is_secure
    )

def _clear_auth_cookie(response: Response):
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax"
    )



def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> models.User:
    """
    Extract authenticated user from either HttpOnly Cookie or Authorization header.
    Raises 401 if unauthenticated or token is expired/invalid.
    """
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in."
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please log in again."
        )

    user = crud.get_user_by_id(db, payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or deactivated."
        )

    return user

def get_optional_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    """
    Tries to extract the current user; falls back to default demo user or None.
    Allows backward-compatible API access without crashing existing automated workflows.
    """
    try:
        return get_current_user(request, db)
    except HTTPException:
        # Fallback to default demo field officer for seamless developer experience
        return crud.get_user_by_email(db, "officer.belagavi@sca.gov.in")

@router.post("/signup", response_model=Dict[str, Any])
def signup(
    payload: SignupRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new State Channelizing Agency field officer or manager."""
    email_clean = payload.email.strip().lower()
    existing = crud.get_user_by_email(db, email_clean)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this official email already exists."
        )

    hashed = hash_password(payload.password)
    user = crud.create_user(db, {
        "email": email_clean,
        "hashed_password": hashed,
        "full_name": payload.full_name.strip(),
        "role": payload.role.strip().upper(),
        "district": (payload.district or "Belagavi").strip(),
        "badge_number": payload.badge_number.strip() if payload.badge_number else None,
        "is_active": True
    })

    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "district": user.district,
        "name": user.full_name
    })

    _set_auth_cookie(response, token, request)

    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "district": user.district,
            "badge_number": user.badge_number,
        }
    }

@router.post("/login", response_model=Dict[str, Any])
def login(
    payload: LoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticate officer via email and password, establishing an HttpOnly session."""
    email_clean = payload.email.strip().lower()
    user = crud.get_user_by_email(db, email_clean)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid official email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This officer account is inactive. Please contact your SCA administrator."
        )

    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "district": user.district,
        "name": user.full_name
    })

    _set_auth_cookie(response, token, request)


    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "district": user.district,
            "badge_number": user.badge_number,
        }
    }

@router.post("/logout")
def logout(response: Response):
    """Terminate the active officer session."""
    _clear_auth_cookie(response)
    return {"status": "success", "message": "Successfully logged out"}

@router.get("/me")
def get_current_user_profile(user: models.User = Depends(get_current_user)):
    """Retrieve verified profile of currently logged-in officer."""
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "district": user.district,
        "badge_number": user.badge_number,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }
