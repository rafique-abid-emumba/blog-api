from pydantic import BaseModel, constr
from typing import List

class TitleTagRequest(BaseModel):
    post_content: constr(min_length=1, max_length=5000)

class TitleTagResponse(BaseModel):
    title: str
    tags: List[str] 