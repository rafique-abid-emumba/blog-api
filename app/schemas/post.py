from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class PostStatus(str, Enum):
    draft = "draft"
    published = "published"

class PostBase(BaseModel):
    title: str
    content: str
    status: PostStatus = PostStatus.draft
    tags: Optional[List[str]] = []

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[PostStatus] = None
    tags: Optional[List[str]] = None

class PostOut(PostBase):
    id: int
    author_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True