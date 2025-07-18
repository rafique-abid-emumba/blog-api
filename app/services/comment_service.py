from sqlalchemy.orm import Session, joinedload
from app.models.comment import Comment
from app.models.user import User
from app.models.post import Post
from app.schemas.comment import CommentCreate, CommentUpdate
from fastapi import HTTPException, status
from typing import List, Optional
import logging
from app.constants import MAX_COMMENTS_PER_USER_PER_POST, MAX_COMMENTS_PER_POST, MAX_COMMENT_DEPTH
from app.utils import get_comment_depth
from app.services.genai_service import analyze_comment

logger = logging.getLogger(__name__)

def validate_user_comment_limit(db, user_id, post_id):
    count = db.query(Comment).filter(Comment.post_id == post_id, Comment.user_id == user_id).count()
    if count >= MAX_COMMENTS_PER_USER_PER_POST:
        logger.warning(f"User {user_id} exceeded per-post comment limit on post {post_id}")
        raise HTTPException(status_code=400, detail=f"User can only comment {MAX_COMMENTS_PER_USER_PER_POST} times per post.")

def validate_post_comment_limit(db, post_id):
    count = db.query(Comment).filter(Comment.post_id == post_id).count()
    if count >= MAX_COMMENTS_PER_POST:
        logger.warning(f"Post {post_id} exceeded total comment limit")
        raise HTTPException(status_code=400, detail=f"Post can only have {MAX_COMMENTS_PER_POST} comments.")

def validate_parent_comment(db, parent_id, post_id):
    parent = db.query(Comment).filter(Comment.id == parent_id).first()
    if not parent or parent.post_id != post_id:
        logger.warning(f"Parent comment {parent_id} does not exist or is not for the same post {post_id}")
        raise HTTPException(status_code=400, detail="Parent comment does not exist or is not for the same post.")
    if get_comment_depth(parent) >= MAX_COMMENT_DEPTH:
        logger.warning(f"Cannot reply to comment {parent.id}: max depth {MAX_COMMENT_DEPTH} reached")
        raise HTTPException(status_code=400, detail=f"Cannot reply: max comment depth of {MAX_COMMENT_DEPTH} reached.")
    return parent

def create_comment(db: Session, user: User, post: Post, comment_in: CommentCreate) -> Comment:
    try:
        validate_user_comment_limit(db, user.id, comment_in.post_id)
        validate_post_comment_limit(db, comment_in.post_id)
        parent = None
        if comment_in.parent_id is not None:
            parent = validate_parent_comment(db, comment_in.parent_id, comment_in.post_id)
        
        try:
            analysis = analyze_comment(comment_in.content)
            sentiment = analysis.sentiment
            is_abusive = 1 if analysis.abusive_flag else 0
            logger.info(f"Comment analysis completed for user {user.id}")
        except Exception as e:
            logger.warning(f"GenAI analysis failed for comment, using defaults: {e}")
            sentiment = "neutral"
            is_abusive = 0
        
        comment = Comment(
            content=comment_in.content,
            post_id=comment_in.post_id,
            user_id=user.id,
            parent_id=comment_in.parent_id,
            sentiment=sentiment,
            is_abusive=is_abusive
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        if comment.parent_id:
            db.refresh(comment.parent)
        logger.info(f"Comment {comment.id} created by user {user.id} on post {post.id}")
        return comment
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to create comment")

def get_comment(db: Session, comment_id: int) -> Comment:
    try:
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            logger.warning(f"Comment {comment_id} not found")
            raise HTTPException(status_code=404, detail="Comment not found")
        return comment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching comment {comment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch comment")

def update_comment(db: Session, comment: Comment, comment_update: CommentUpdate, user: User) -> Comment:
    try:
        if comment.user_id != user.id:
            logger.warning(f"User {user.id} not allowed to update comment {comment.id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to update this comment")
        comment.content = comment_update.content
        
        try:
            analysis = analyze_comment(comment_update.content)
            comment.sentiment = analysis.sentiment
            comment.is_abusive = 1 if analysis.is_abusive else 0
            logger.info(f"Comment re-analysis completed for comment {comment.id}")
        except Exception as e:
            logger.warning(f"GenAI re-analysis failed for comment {comment.id}, keeping existing analysis: {e}")
        
        db.commit()
        db.refresh(comment)
        logger.info(f"Comment {comment.id} updated by user {user.id}")
        return comment
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating comment {comment.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update comment")

def delete_comment(db: Session, comment: Comment, user: User):
    try:
        if comment.user_id != user.id:
            logger.warning(f"User {user.id} not allowed to delete comment {comment.id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete this comment")
        db.delete(comment)
        db.commit()
        logger.info(f"Comment {comment.id} deleted by user {user.id}")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting comment {comment.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete comment")

def list_comments_for_post(db: Session, post_id: int) -> List[Comment]:
    try:
        return db.query(Comment).options(
            joinedload(Comment.replies)
        ).filter(Comment.post_id == post_id, Comment.parent_id == None).all()
    except Exception as e:
        logger.error(f"Error listing comments for post {post_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list comments")

def serialize_comment(comment: Comment, current_depth: int = 1, max_depth: int = MAX_COMMENT_DEPTH):
    data = {
        "id": comment.id,
        "content": comment.content,
        "post_id": comment.post_id,
        "user_id": comment.user_id,
        "parent_id": comment.parent_id,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
        "sentiment": comment.sentiment,
        "is_abusive": bool(comment.is_abusive) if comment.is_abusive is not None else None,
    }
    if current_depth < max_depth:
        data["replies"] = [
            serialize_comment(reply, current_depth + 1, max_depth)
            for reply in getattr(comment, "replies", [])
        ]
    else:
        data["replies"] = []
    return data

def serialize_comments(comments: List[Comment], max_depth: int = MAX_COMMENT_DEPTH):
    return [serialize_comment(c, 1, max_depth) for c in comments] 