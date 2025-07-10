from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.schemas.post import PostCreate, PostUpdate, PostOut, PostStatus
from app.services.post_service import (
    create_post, get_post, get_posts_for_admin, 
    get_posts_for_author, get_posts_for_reader, 
    update_post, delete_post
)
from app.services.user_service import get_user
from app.db.deps import get_db
from app.core.deps import get_current_user, require_role

router = APIRouter(prefix="/posts", tags=["posts"])

@router.post("/", response_model=PostOut, dependencies=[Depends(require_role(["Admin", "Author"]))])
def create_new_post(
    post_in: PostCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user = get_user(db, int(current_user["sub"]))
    return create_post(db, user, post_in)

@router.get("/{post_id}", response_model=PostOut)
def read_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    post = get_post(db, post_id)
    if post.status == PostStatus.draft:
        if post.author_id != int(current_user["sub"]) and current_user["role"] != "Admin":
            raise HTTPException(status_code=403, detail="You do not have access to this draft post")
    return post

@router.get("/", response_model=List[PostOut])
def list_posts(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user["role"] == "Admin":
        return get_posts_for_admin(db, skip, limit)
    elif current_user["role"] == "Author":
        return get_posts_for_author(db, int(current_user["sub"]), skip, limit)
    else:
        return get_posts_for_reader(db, skip, limit)

@router.put("/{post_id}", response_model=PostOut, dependencies=[Depends(require_role(["Admin", "Author"]))])
def update_existing_post(
    post_id: int,
    post_update: PostUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    post = get_post(db, post_id)

    if post.author_id != int(current_user["sub"]) and current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Not allowed to update this post")
    return update_post(db, post, post_update)

@router.delete("/{post_id}", status_code=204, dependencies=[Depends(require_role(["Admin", "Author"]))])
def delete_existing_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    post = get_post(db, post_id)
    # Only author or admin can delete
    if post.author_id != int(current_user["sub"]) and current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Not allowed to delete this post")
    delete_post(db, post)
    return