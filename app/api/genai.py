from fastapi import APIRouter, Depends, Query, HTTPException
from app.services.genai_service import get_title_and_tags_for_post, get_summary_for_post, answer_post_question, answer_question_from_all_posts, analyze_comment, get_trending_tags_ai
from app.schemas.genai import TitleTagRequest, TitleTagResponse, SummarizeRequest, SummarizeResponse, QARequest, QAResponse, GlobalQARequest, GlobalQAResponse, CommentAnalysisRequest, CommentAnalysisResponse, TrendingTagsResponse
from app.db.deps import get_db
from app.utils.utilities import validate_content_input
from sqlalchemy.orm import Session

router = APIRouter(prefix="/genai", tags=["GenAI"])

@router.post("/title-tags", response_model=TitleTagResponse)
def suggest_title_and_tags_endpoint(request: TitleTagRequest):
    is_valid, error_message = validate_content_input(request.post_content, min_length=10, max_length=5000)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    result = get_title_and_tags_for_post(request.post_content)
    return TitleTagResponse(**result)

@router.post("/summarize", response_model=SummarizeResponse)
def summarize_post_endpoint(request: SummarizeRequest):
    is_valid, error_message = validate_content_input(request.post_content, min_length=20, max_length=5000)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    result = get_summary_for_post(request.post_content)
    return SummarizeResponse(**result)

@router.post("/qa", response_model=QAResponse)
def qa_post_endpoint(request: QARequest):
    is_valid, error_message = validate_content_input(request.question, min_length=10, max_length=500)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    result = answer_post_question(request.post_id, request.question)
    return QAResponse(**result)

@router.post("/qa-global", response_model=GlobalQAResponse)
def qa_global_endpoint(request: GlobalQARequest):
    is_valid, error_message = validate_content_input(request.question, min_length=10, max_length=500)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    result = answer_question_from_all_posts(request.question)
    return GlobalQAResponse(**result)

@router.post("/comment-analysis", response_model=CommentAnalysisResponse)
def analyze_comment_endpoint(request: CommentAnalysisRequest):
    is_valid, error_message = validate_content_input(request.comment, min_length=3, max_length=500)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    result = analyze_comment(request.comment)
    return result

@router.get("/trending-ai", response_model=TrendingTagsResponse)
def trending_tags_ai(
    limit: int = Query(10, ge=1, le=20, description="Number of trending tags to return (1-50)"),
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze (1-90)"),
    db: Session = Depends(get_db)
):
    result = get_trending_tags_ai(db, top_k=limit, days=days)
    return TrendingTagsResponse(**result)