
import logging
from fastapi import HTTPException
from app.genai.pipelines import suggest_title_and_tags

logger = logging.getLogger(__name__)


def get_title_and_tags_for_post(post_content: str) -> dict:
    try:
        result = suggest_title_and_tags(post_content)
        logger.info("GenAI title/tag suggestion succeeded")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GenAI title/tag suggestion: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate title and tags") 