from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
import hashlib
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.core.security import get_password_hash, verify_password, create_access_token
from backend.app.models.user import User, Role, Profile, Session as UserSession
from backend.app.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse, UserSummary
from backend.app.schemas.user import UserResponse, ProfileResponse, ProfileUpdateRequest, PasswordChangeRequest
from backend.app.api.deps import get_current_user, record_audit_log

router = APIRouter()

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserRegisterRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    # Enforce lowercase normalized email
    email = payload.email.lower().strip()

    # Check for existing account
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Public registration strictly assigns role USER
    user_role = db.query(Role).filter(Role.name == "USER").first()
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="System role configuration missing."
        )

    # Hash password with Argon2id
    hashed_pwd = get_password_hash(payload.password)

    new_user = User(
        email=email,
        password_hash=hashed_pwd,
        role_id=user_role.id,
        is_active=True,
        is_verified=False
    )
    db.add(new_user)
    db.flush()  # Generate user id

    # Create user profile
    new_profile = Profile(
        user_id=new_user.id,
        full_name=payload.full_name.strip(),
        phone_number=payload.phone_number.strip() if payload.phone_number else None,
        preferred_language=payload.preferred_language,
        senior_mode=False
    )
    db.add(new_profile)

    # Generate JWT token
    access_token = create_access_token(subject=new_user.id, role="USER")
    token_hash = hashlib.sha256(access_token.encode()).hexdigest()

    # Create session record
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    session_record = UserSession(
        user_id=new_user.id,
        token_hash=token_hash,
        ip_address=client_ip,
        user_agent=user_agent,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    db.add(session_record)
    db.commit()

    # Record audit log
    record_audit_log(
        db=db,
        action="USER_REGISTRATION",
        resource_type="USER",
        resource_id=new_user.id,
        details={"email": email, "language": payload.preferred_language},
        user_id=new_user.id,
        ip_address=client_ip,
        user_agent=user_agent
    )

    # Set secure HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=settings.ENVIRONMENT == "production"
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserSummary(
            id=new_user.id,
            email=new_user.email,
            full_name=new_profile.full_name,
            role="USER",
            preferred_language=new_profile.preferred_language,
            senior_mode=new_profile.senior_mode
        )
    )

@router.post("/login", response_model=TokenResponse)
def login_user(
    payload: UserLoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        # Record failed login attempt in audit log
        client_ip = request.client.host if request.client else None
        record_audit_log(
            db=db,
            action="LOGIN_FAILED",
            resource_type="AUTH",
            resource_id=email,
            details={"reason": "Invalid credentials", "attempted_email": email},
            ip_address=client_ip,
            user_agent=request.headers.get("user-agent")
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email address or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated or suspended. Please contact support."
        )

    role_name = user.role.name if user.role else "USER"
    access_token = create_access_token(subject=user.id, role=role_name)
    token_hash = hashlib.sha256(access_token.encode()).hexdigest()

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    session_record = UserSession(
        user_id=user.id,
        token_hash=token_hash,
        ip_address=client_ip,
        user_agent=user_agent,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    db.add(session_record)
    db.commit()

    record_audit_log(
        db=db,
        action="ADMIN_LOGIN" if role_name == "ADMIN" else "USER_LOGIN",
        resource_type="USER",
        resource_id=user.id,
        details={"role": role_name},
        user_id=user.id,
        ip_address=client_ip,
        user_agent=user_agent
    )

    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=settings.ENVIRONMENT == "production"
    )

    full_name = user.profile.full_name if user.profile else user.email.split("@")[0]
    lang = user.profile.preferred_language if user.profile else "en"
    senior_mode = user.profile.senior_mode if user.profile else False

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserSummary(
            id=user.id,
            email=user.email,
            full_name=full_name,
            role=role_name,
            preferred_language=lang,
            senior_mode=senior_mode
        )
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    profile_data = None
    if current_user.profile:
        profile_data = ProfileResponse(
            full_name=current_user.profile.full_name,
            phone_number=current_user.profile.phone_number,
            preferred_language=current_user.profile.preferred_language,
            senior_mode=current_user.profile.senior_mode,
            avatar_url=current_user.profile.avatar_url
        )

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role.name if current_user.role else "USER",
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        profile=profile_data
    )

@router.put("/me/profile", response_model=UserResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = current_user.profile
    if not profile:
        profile = Profile(user_id=current_user.id, full_name=current_user.email.split("@")[0])
        db.add(profile)

    if payload.full_name is not None:
        profile.full_name = payload.full_name.strip()
    if payload.phone_number is not None:
        profile.phone_number = payload.phone_number.strip() if payload.phone_number else None
    if payload.preferred_language is not None:
        profile.preferred_language = payload.preferred_language
    if payload.senior_mode is not None:
        profile.senior_mode = payload.senior_mode

    db.commit()
    db.refresh(current_user)

    return get_current_user_profile(current_user)

@router.put("/me/password")
def change_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The current password you provided is incorrect."
        )

    current_user.password_hash = get_password_hash(payload.new_password)
    db.commit()

    record_audit_log(
        db=db,
        action="PASSWORD_CHANGED",
        resource_type="USER",
        resource_id=current_user.id,
        details={"user_id": current_user.id},
        user_id=current_user.id
    )

    return {"message": "Password changed successfully."}

@router.post("/logout")
def logout_user(
    response: Response,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Remove sessions for this user
    db.query(UserSession).filter(UserSession.user_id == current_user.id).delete()
    db.commit()

    record_audit_log(
        db=db,
        action="USER_LOGOUT",
        resource_type="USER",
        resource_id=current_user.id,
        details={"email": current_user.email},
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    response.delete_cookie("access_token")
    return {"message": "Successfully logged out."}

