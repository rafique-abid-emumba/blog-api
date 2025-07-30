from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate, UserUpdate
from fastapi import HTTPException
import logging
from app.utils.constants import DEFAULT_ROLE, PASSWORD_REQUIREMENTS_MSG
from app.utils.utilities import verify_password, get_password_hash, is_strong_password

logger = logging.getLogger(__name__)

def is_duplicate_username(db: Session, username: str) -> bool:
    return db.query(User).filter(User.username == username).first() is not None

async def is_duplicate_username_async(db, username: str) -> bool:
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalar_one_or_none() is not None

def is_duplicate_email(db: Session, email: str) -> bool:
    return db.query(User).filter(User.email == email).first() is not None

async def is_duplicate_email_async(db, email: str) -> bool:
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none() is not None

def create_user(db: Session, user_in: UserCreate) -> User:
    try:
        if is_duplicate_username(db, user_in.username):
            logger.warning(f"Username already exists: {user_in.username}")
            raise HTTPException(status_code=400, detail="Username already registered")
        
        if is_duplicate_email(db, user_in.email):
            logger.warning(f"Email already exists: {user_in.email}")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        if not is_strong_password(user_in.password):
            logger.warning("Password does not meet strength requirements")
            raise HTTPException(status_code=400, detail=PASSWORD_REQUIREMENTS_MSG)
        
        default_role = db.query(Role).filter(Role.name == DEFAULT_ROLE).first()
        if not default_role:
            raise HTTPException(status_code=500, detail="Default role not found")
        
        hashed_password = get_password_hash(user_in.password)
        user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hashed_password,
            role_id=default_role.id
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"User created successfully: {user.username} (ID: {user.id})")
        return user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")

async def create_user_async(db, user_in: UserCreate) -> User:
    try:
        if await is_duplicate_username_async(db, user_in.username):
            logger.warning(f"Username already exists: {user_in.username}")
            raise HTTPException(status_code=400, detail="Username already registered")
        
        if await is_duplicate_email_async(db, user_in.email):
            logger.warning(f"Email already exists: {user_in.email}")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        if not is_strong_password(user_in.password):
            logger.warning("Password does not meet strength requirements")
            raise HTTPException(status_code=400, detail=PASSWORD_REQUIREMENTS_MSG)
        
        result = await db.execute(select(Role).filter(Role.name == DEFAULT_ROLE))
        default_role = result.scalar_one_or_none()
        if not default_role:
            raise HTTPException(status_code=500, detail="Default role not found")
        
        hashed_password = get_password_hash(user_in.password)
        user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hashed_password,
            role_id=default_role.id
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"User created successfully: {user.username} (ID: {user.id})")
        return user
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")

def get_user(db: Session, user_id: int) -> User:
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning("Attempted to get non-existent user")
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user")

async def get_user_async(db, user_id: int) -> User:
    try:
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            logger.warning("Attempted to get non-existent user")
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user")

def get_user_by_username(db: Session, username: str) -> User:
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            logger.warning(f"Attempted to get non-existent user by username: {username}")
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user by username: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user")

async def get_user_by_username_async(db, username: str) -> User:
    try:
        result = await db.execute(select(User).filter(User.username == username))
        user = result.scalar_one_or_none()
        if not user:
            logger.warning(f"Attempted to get non-existent user by username: {username}")
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user by username: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user")

def authenticate_user(db: Session, username: str, password: str) -> User:
    try:
        user = get_user_by_username(db, username)
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Invalid password for user: {username}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")

async def authenticate_user_async(db, username: str, password: str) -> User:
    try:
        user = await get_user_by_username_async(db, username)
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Invalid password for user: {username}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")

def update_user(db: Session, user: User, user_update: UserUpdate) -> User:
    try:
        update_data = user_update.model_dump(exclude_unset=True)
        
        if user_update.username and user_update.username != user.username:
            if is_duplicate_username(db, user_update.username):
                logger.warning(f"Username already exists: {user_update.username}")
                raise HTTPException(status_code=400, detail="Username already taken")
        
        if user_update.email and user_update.email != user.email:
            if is_duplicate_email(db, user_update.email):
                logger.warning(f"Email already exists: {user_update.email}")
                raise HTTPException(status_code=400, detail="Email already taken")
        
        if user_update.password:
            if not is_strong_password(user_update.password):
                logger.warning("Password does not meet strength requirements")
                raise HTTPException(status_code=400, detail=PASSWORD_REQUIREMENTS_MSG)
            update_data["hashed_password"] = get_password_hash(user_update.password)
            del update_data["password"]
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"User updated successfully: {user.username} (ID: {user.id})")
        return user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")

async def update_user_async(db, user: User, user_update: UserUpdate) -> User:
    try:
        update_data = user_update.model_dump(exclude_unset=True)
        
        if user_update.username and user_update.username != user.username:
            if await is_duplicate_username_async(db, user_update.username):
                logger.warning(f"Username already exists: {user_update.username}")
                raise HTTPException(status_code=400, detail="Username already taken")
        
        if user_update.email and user_update.email != user.email:
            if await is_duplicate_email_async(db, user_update.email):
                logger.warning(f"Email already exists: {user_update.email}")
                raise HTTPException(status_code=400, detail="Email already taken")
        
        if user_update.password:
            if not is_strong_password(user_update.password):
                logger.warning("Password does not meet strength requirements")
                raise HTTPException(status_code=400, detail=PASSWORD_REQUIREMENTS_MSG)
            update_data["hashed_password"] = get_password_hash(user_update.password)
            del update_data["password"]
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"User updated successfully: {user.username} (ID: {user.id})")
        return user
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")