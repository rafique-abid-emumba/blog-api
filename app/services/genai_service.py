import logging
from fastapi import HTTPException
from app.genai.pipelines import suggest_title_and_tags, summarize_post, answer_question_about_post, analyze_comment_sentiment, suggest_trending_tags, answer_question_global
from app.schemas.genai import CommentAnalysisResponse
from app.models.post import Post
from app.models.comment import Comment
from datetime import datetime, timedelta, timezone

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
    
def analyze_comment(comment: str) -> CommentAnalysisResponse:
    try:
        analysis_result = analyze_comment_sentiment(comment)
        result = CommentAnalysisResponse(
            comment=comment,
            sentiment=analysis_result['sentiment'],
            is_abusive=analysis_result['is_abusive']
        )
        logger.info("GenAI comment analysis succeeded")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GenAI comment analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze comment")

def answer_question_from_all_posts(question: str, top_k: int = 5) -> dict:
    """
    Answer a question using RAG across all content in the vector database.
    """
    try:
        result = answer_question_global(question, top_k)
        logger.info("Global Q&A succeeded")
        return result
    except Exception as e:
        logger.error(f"Error in global Q&A: {e}")
        return {
            "answer": "I cannot find specific information to answer this question based on the available content.",
            "citations": [],
            "relevant_posts": []
        }

def get_trending_tags_ai(db, top_k: int = 10, days: int = 7) -> dict:
    """
    Get trending tags using GenAI analysis of recent posts and their top-level comments.
    """
    try:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        posts = db.query(Post).filter(Post.created_at >= since).all()
        
        posts_with_comments = []
        for post in posts:
            top_comments = db.query(Comment).filter(
                Comment.post_id == post.id,
                Comment.parent_id == None
            ).limit(10).all()
            
            post_data = {
                "title": post.title,
                "content": post.content,
                "tags": [pt.tag.name for pt in post.post_tags],
                "comments": [
                    {
                        "content": comment.content,
                        "sentiment": comment.sentiment,
                        "is_abusive": bool(comment.is_abusive) if comment.is_abusive is not None else None
                    }
                    for comment in top_comments
                ]
            }
            posts_with_comments.append(post_data)
        
        if not posts_with_comments:
            logger.warning(f"No posts found in the last {days} days for trending analysis")
            return {"trending_tags": []}
        
        trending_tags = suggest_trending_tags(posts_with_comments, top_k=top_k)
        
        result = {
            "trending_tags": trending_tags,
            "analysis_period_days": days,
            "posts_analyzed": len(posts_with_comments),
            "total_comments_analyzed": sum(len(p["comments"]) for p in posts_with_comments)
        }
        
        logger.info(f"GenAI trending tags analysis succeeded: {len(trending_tags)} tags identified")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GenAI trending tags analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze trending tags")