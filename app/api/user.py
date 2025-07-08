from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserLogin, UserOut, UserUpdate
from app.services.user_service import create_user, authenticate_user, update_user, get_user
from app.services.auth_service import issue_tokens, refresh_user_token
from app.db.deps import get_db
from app.core.deps import get_current_user

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
    return issue_tokens(str(user.id), user.role.name)

@router.post("/refresh")
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    return refresh_user_token(refresh_token)

@router.get("/profile", response_model=UserOut)
def get_profile(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user = get_user(db, int(current_user["sub"]))
    return UserOut.from_orm(user)

@router.put("/profile", response_model=UserOut)
def update_profile(
    user_update: UserUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user(db, int(current_user["sub"]))
    updated_user = update_user(db, user, user_update)
    return UserOut.from_orm(updated_user)