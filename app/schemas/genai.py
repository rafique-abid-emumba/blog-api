from pydantic import BaseModel, constr
from typing import List

class TitleTagRequest(BaseModel):
    post_content: constr(min_length=1, max_length=5000)

class TitleTagResponse(BaseModel):
    title: str
    tags: List[str]

class SummarizeRequest(BaseModel):
    post_content: constr(min_length=1, max_length=5000)

class SummarizeResponse(BaseModel):
    summary: str
    citations: List[str]

class QARequest(BaseModel):
    post_id: int
    question: constr(min_length=1, max_length=500)

class QAResponse(BaseModel):
    answer: str
    citations: List[str] 

class CommentAnalysisRequest(BaseModel):
    comment: constr(min_length=1, max_length=500)

class CommentAnalysisResponse(BaseModel):
    comment: str
    sentiment: str
    is_abusive: bool

class TrendingTagsResponse(BaseModel):
    trending_tags: List[str]
    analysis_period_days: int
    posts_analyzed: int
    total_comments_analyzed: int