from sqlalchemy.orm import Session
from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate, UserUpdate
from passlib.context import CryptContext
from fastapi import HTTPException
import logging
import re

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def is_duplicate_username(db: Session, username: str) -> bool:
    return db.query(User).filter(User.username == username).first() is not None

def is_duplicate_email(db: Session, email: str) -> bool:
    return db.query(User).filter(User.email == email).first() is not None

def is_strong_password(password: str) -> bool:
    # Minimum 8 chars, 1 uppercase, 1 number, 1 special char
    pattern = r'^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\\\-={{}}\[\]:\";\'<>?,./]).{8,}$'
    return bool(re.match(pattern, password))

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_user(db: Session, user_id: int) -> User:
    """Get user by ID"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found: ID {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user")

def create_user(db: Session, user_in: UserCreate) -> User:
    try:
        if is_duplicate_username(db, user_in.username):
            logger.warning(f"Username already exists: {user_in.username}")
            raise HTTPException(status_code=400, detail="Username already exists")
        if is_duplicate_email(db, user_in.email):
            logger.warning(f"Email already exists: {user_in.email}")
            raise HTTPException(status_code=400, detail="Email already exists")
        if not is_strong_password(user_in.password):
            logger.warning("Password does not meet strength requirements")
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters long, contain at least 1 uppercase letter, 1 number, and 1 special character."
            )
        
        hashed_password = get_password_hash(user_in.password)
        # Default role: Reader (or fetch by name)
        role = db.query(Role).filter(Role.name == "Reader").first()
        user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hashed_password,
            role_id=role.id if role else 1
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"User created successfully: {user.username}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")

def authenticate_user(db: Session, username: str, password: str):
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed for username: {username}")
            return None
        logger.info(f"User authenticated: {username}")
        return user
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to authenticate user")

def update_user(db: Session, user: User, user_update: UserUpdate) -> User:
    try:
        if not user:
            logger.warning("Attempted to update non-existent user")
            raise HTTPException(status_code=404, detail="User not found")
        
        if user_update.username is not None and user_update.username != user.username:
            if is_duplicate_username(db, user_update.username):
                logger.warning(f"Username already exists: {user_update.username}")
                raise HTTPException(status_code=400, detail="Username already exists")
            user.username = user_update.username
        if user_update.email is not None and user_update.email != user.email:
            if is_duplicate_email(db, user_update.email):
                logger.warning(f"Email already exists: {user_update.email}")
                raise HTTPException(status_code=400, detail="Email already exists")
            user.email = user_update.email
        if user_update.password is not None and user_update.password != user.password:
            if not is_strong_password(user_update.password):
                logger.warning("Password does not meet strength requirements")
                raise HTTPException(
                    status_code=400,
                    detail="Password must be at least 8 characters long, contain at least 1 uppercase letter, 1 number, and 1 special character."
                )
            user.hashed_password = get_password_hash(user_update.password)
        db.commit()
        db.refresh(user)
        logger.info(f"User updated successfully: {user.username}")
        return user
    except HTTPException:
        raise 
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")