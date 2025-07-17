
import logging
from fastapi import HTTPException
from app.genai.pipelines import suggest_title_and_tags, summarize_post, answer_question_about_post

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

def get_summary_for_post(post_content: str) -> dict:
    try:
        result = summarize_post(post_content)
        logger.info("GenAI summarization succeeded")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GenAI summarization: {e}")
        raise HTTPException(status_code=500, detail="Failed to summarize post")

def answer_post_question(post_id: int, question: str) -> dict:
    try:
        result = answer_question_about_post(post_id, question)
        logger.info("GenAI Q&A succeeded")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GenAI Q&A: {e}")
        raise HTTPException(status_code=500, detail="Failed to answer question") 