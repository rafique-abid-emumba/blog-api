from sqlalchemy.orm import Session
from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_user(db: Session, user_in: UserCreate) -> User:
    # Make sure the roles table is seeded with default roles before creating users.
    hashed_password = get_password_hash(user_in.password)
    # Default role: Reader (or fetch by name)
    role = db.query(Role).filter(Role.name == "Reader").first()
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
        role_id=role.id if role else 1  # fallback to 1
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user