from pydantic import BaseModel, EmailStr, ConfigDict, constr
from typing import Optional

class UserBase(BaseModel):
    username: constr(min_length=1)
    email: EmailStr

class UserCreate(UserBase):
    password: constr(min_length=1)

class UserLogin(BaseModel):
    username: constr(min_length=1)
    password: constr(min_length=1)

class UserUpdate(BaseModel):
    username: Optional[constr(min_length=1)] = None
    email: Optional[EmailStr] = None
    password: Optional[constr(min_length=1)] = None

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