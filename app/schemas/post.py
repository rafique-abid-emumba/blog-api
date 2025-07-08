from pydantic import BaseModel, ConfigDict
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
    tags: Optional[List[str]] = None

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[PostStatus] = None
    tags: Optional[List[str]] = None

class PostOut(PostBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    author_id: int
    created_at: datetime
    updated_at: Optional[datetime]