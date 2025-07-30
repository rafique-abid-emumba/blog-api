from pydantic import BaseModel, ConfigDict, constr, field_validator
from typing import List, Optional
from datetime import datetime
from enum import Enum
from app.utils.sanitizer import sanitize_html_content

class PostStatus(str, Enum):
    draft = "draft"
    published = "published"

class PostBase(BaseModel):
    title: constr(min_length=1, max_length=300)
    content: constr(min_length=1, max_length=10000)
    status: PostStatus = PostStatus.draft
    tags: Optional[List[str]] = None

    @field_validator('title')
    @classmethod
    def sanitize_title(cls, v):
        return sanitize_html_content(v, max_length=300)

    @field_validator('content')
    @classmethod
    def sanitize_content(cls, v):
        return sanitize_html_content(v, max_length=10000)

    @field_validator('tags')
    @classmethod
    def sanitize_tags(cls, v):
        if v:
            return [tag.strip()[:50] for tag in v if tag.strip()]
        return v

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[constr(min_length=1, max_length=300)] = None
    content: Optional[constr(min_length=1, max_length=10000)] = None
    status: Optional[PostStatus] = None
    tags: Optional[List[str]] = None

    @field_validator('title')
    @classmethod
    def sanitize_title(cls, v):
        if v:
            return sanitize_html_content(v, max_length=300)
        return v

    @field_validator('content')
    @classmethod
    def sanitize_content(cls, v):
        if v:
            return sanitize_html_content(v, max_length=10000)
        return v

    @field_validator('tags')
    @classmethod
    def sanitize_tags(cls, v):
        if v:
            return [tag.strip()[:50] for tag in v if tag.strip()]
        return v

class PostOut(PostBase):
    model_config = ConfigDict(from_attributes=True)
    
    summary: Optional[str] = None
    id: int
    author_id: int
    created_at: datetime
    updated_at: Optional[datetime]

class PostFilters(BaseModel):
    status: Optional[PostStatus] = None
    author_id: Optional[int] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    search: Optional[str] = None

class PaginatedResponse(BaseModel):
    items: List[PostOut]
    total: int
    page: int
    size: int
    pages: int

    model_config = ConfigDict(from_attributes=True)