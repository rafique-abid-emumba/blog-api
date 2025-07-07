from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserLogin, UserOut, UserUpdate
from app.services.user_service import create_user, authenticate_user, update_user
from app.db.deps import get_db
from app.core.security import create_access_token, create_refresh_token, verify_refresh_token
from app.core.deps import get_current_user
from datetime import timedelta
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    user = create_user(db, user_in)
    return UserOut.from_orm(user)

@router.post("/login")
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_in.username, user_in.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.name},
        expires_delta=timedelta(minutes=30)
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "role": user.role.name},
        expires_delta=timedelta(days=7)
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh")
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    payload = verify_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user_id = payload.get("sub")
    role = payload.get("role")
    access_token = create_access_token(
        data={"sub": user_id, "role": role},
        expires_delta=timedelta(minutes=30)
    )
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/profile", response_model=UserOut)
def get_profile(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).get(int(current_user["sub"]))
    return UserOut.from_orm(user)

@router.put("/profile", response_model=UserOut)
def update_profile(
    user_update: UserUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).get(int(current_user["sub"]))
    updated_user = update_user(db, user, user_update)
    return UserOut.from_orm(updated_user)