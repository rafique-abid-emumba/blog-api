from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserOut(UserBase):
    id: int
    role: str

    class Config:
        from_attributes=True

    @classmethod
    def from_orm(cls, user):
        # user.role is a Role object; get its name
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role.name if user.role else None
        )