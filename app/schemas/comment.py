from pydantic import BaseModel, constr, ConfigDict, conint, field_validator
from typing import Optional, List
from datetime import datetime
from app.utils.sanitizer import sanitize_html_content

class CommentCreate(BaseModel):
    content: constr(min_length=1, max_length=1000)
    post_id: int
    parent_id: Optional[conint(ge=1)] = None

    @field_validator('content')
    @classmethod
    def sanitize_content(cls, v):
        return sanitize_html_content(v, max_length=1000)

class CommentUpdate(BaseModel):
    content: constr(min_length=1, max_length=1000)

    @field_validator('content')
    @classmethod
    def sanitize_content(cls, v):
        return sanitize_html_content(v, max_length=1000)

class CommentOut(BaseModel):
    id: int
    content: str
    post_id: int
    user_id: int
    parent_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    replies: Optional[List['CommentOut']] = None
    sentiment: Optional[str] = None
    is_abusive: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

CommentOut.model_rebuild() 