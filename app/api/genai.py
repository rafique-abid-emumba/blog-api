from fastapi import APIRouter
from app.services.genai_service import get_title_and_tags_for_post, get_summary_for_post, answer_post_question
from app.schemas.genai import TitleTagRequest, TitleTagResponse, SummarizeRequest, SummarizeResponse, QARequest, QAResponse

router = APIRouter(prefix="/genai", tags=["GenAI"])

@router.post("/title-tags", response_model=TitleTagResponse)
def suggest_title_and_tags_endpoint(request: TitleTagRequest):
    result = get_title_and_tags_for_post(request.post_content)
    return TitleTagResponse(**result)

@router.post("/summarize", response_model=SummarizeResponse)
def summarize_post_endpoint(request: SummarizeRequest):
    result = get_summary_for_post(request.post_content)
    return SummarizeResponse(**result)

@router.post("/qa", response_model=QAResponse)
def qa_post_endpoint(request: QARequest):
    result = answer_post_question(request.post_id, request.question)
    return QAResponse(**result) 