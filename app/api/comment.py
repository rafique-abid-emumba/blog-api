from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.schemas.comment import CommentCreate, CommentUpdate, CommentOut
from app.services.comment_service import (
    create_comment, get_comment, update_comment, delete_comment,
    list_comments_for_post, serialize_comment, serialize_comments
)
from app.services.user_service import get_user
from app.db.deps import get_db
from app.core.deps import get_current_user
from app.services.post_service import get_post
import logging
from app.services.comment_service import MAX_COMMENT_DEPTH

router = APIRouter(prefix="/comments", tags=["comments"])
logger = logging.getLogger(__name__)

@router.post("/", response_model=CommentOut, status_code=201)
def create_new_comment(
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user = get_user(db, int(current_user["sub"]))
    post = get_post(db, comment_in.post_id)
    comment = create_comment(db, user, post, comment_in)
    logger.info(f"User {user.id} created comment {comment.id} on post {post.id}")
    return serialize_comment(comment)

@router.get("/{comment_id}", response_model=CommentOut)
def read_comment(
    comment_id: int,
    db: Session = Depends(get_db)
):
    comment = get_comment(db, comment_id)
    return serialize_comment(comment)

@router.put("/{comment_id}", response_model=CommentOut)
def update_existing_comment(
    comment_id: int,
    comment_update: CommentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    comment = get_comment(db, comment_id)
    user = get_user(db, int(current_user["sub"]))
    updated_comment = update_comment(db, comment, comment_update, user)
    logger.info(f"User {user.id} updated comment {comment_id}")
    return serialize_comment(updated_comment)

@router.delete("/{comment_id}", status_code=204)
def delete_existing_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    comment = get_comment(db, comment_id)
    user = get_user(db, int(current_user["sub"]))
    delete_comment(db, comment, user)
    logger.info(f"User {user.id} deleted comment {comment_id}")
    return

@router.get("/post/{post_id}", response_model=List[CommentOut])
def list_comments(
    post_id: int,
    db: Session = Depends(get_db),
    max_depth: int = Query(MAX_COMMENT_DEPTH, ge=1, le=MAX_COMMENT_DEPTH),
    skip: int = Query(0, ge=0, le=99),
    limit: int = Query(20, ge=1, le=100)
):
    comments = list_comments_for_post(db, post_id)
    paginated = comments[skip:skip+limit]
    return serialize_comments(paginated, max_depth=max_depth) 