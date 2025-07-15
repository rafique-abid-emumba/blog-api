from pydantic import BaseModel, constr, ConfigDict, conint
from typing import Optional, List
from datetime import datetime

class CommentCreate(BaseModel):
    content: constr(min_length=1, max_length=500)
    post_id: int
    parent_id: Optional[conint(ge=1)] = None

class CommentUpdate(BaseModel):
    content: constr(min_length=1, max_length=500)

class CommentOut(BaseModel):
    id: int
    content: str
    post_id: int
    user_id: int
    parent_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    replies: Optional[List['CommentOut']] = None

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True) 