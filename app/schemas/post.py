from pydantic import BaseModel, ConfigDict, constr
from typing import List, Optional
from datetime import datetime
from enum import Enum

class PostStatus(str, Enum):
    draft = "draft"
    published = "published"

class PostBase(BaseModel):
    title: constr(min_length=1)
    content: constr(min_length=1)
    status: PostStatus = PostStatus.draft
    tags: Optional[List[str]] = None

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[constr(min_length=1)] = None
    content: Optional[constr(min_length=1)] = None
    status: Optional[PostStatus] = None
    tags: Optional[List[str]] = None

class PostOut(PostBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    author_id: int
    created_at: datetime
    updated_at: Optional[datetime]