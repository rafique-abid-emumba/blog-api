from fastapi import APIRouter
from app.services.genai_service import get_title_and_tags_for_post
from app.schemas.genai import TitleTagRequest, TitleTagResponse

router = APIRouter(prefix="/genai", tags=["GenAI"])

@router.post("/title-tags", response_model=TitleTagResponse)
def suggest_title_and_tags_endpoint(request: TitleTagRequest):
    result = get_title_and_tags_for_post(request.post_content)
    return TitleTagResponse(**result) 