from pydantic import BaseModel, EmailStr, ConfigDict, constr, field_validator
from typing import Optional
from app.utils.sanitizer import sanitize_username, sanitize_email

class UserBase(BaseModel):
    username: constr(min_length=1)
    email: EmailStr

    @field_validator('username')
    @classmethod
    def sanitize_username(cls, v):
        return sanitize_username(v)

    @field_validator('email')
    @classmethod
    def sanitize_email(cls, v):
        return sanitize_email(str(v))

class UserCreate(UserBase):
    password: constr(min_length=1)

class UserLogin(BaseModel):
    username: constr(min_length=1)
    password: constr(min_length=1)

class UserUpdate(BaseModel):
    username: Optional[constr(min_length=1)] = None
    email: Optional[EmailStr] = None
    password: Optional[constr(min_length=1)] = None

    @field_validator('username')
    @classmethod
    def sanitize_username(cls, v):
        if v:
            return sanitize_username(v)
        return v

    @field_validator('email')
    @classmethod
    def sanitize_email(cls, v):
        if v:
            return sanitize_email(str(v))
        return v

class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    role: str

    @classmethod
    def from_orm(cls, user):
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role.name if user.role else None
        )