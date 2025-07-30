from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.schemas.post import PostCreate, PostUpdate, PostOut, PostStatus, PostFilters, PaginatedResponse
from app.services.post_service import (
    create_post_async, get_post_async, get_posts_for_admin_with_filters_async,
    get_posts_for_author_with_filters_async, get_posts_for_reader_with_filters_async,
    update_post_async, delete_post_async, create_quick_post_async
)
from app.services.user_service import get_user_async
from app.db.deps import get_db, get_async_db
from app.core.deps import get_current_user, require_role
from app.utils.utilities import validate_content_input
from datetime import datetime

router = APIRouter(prefix="/posts", tags=["posts"])

@router.post("/", response_model=PostOut, dependencies=[Depends(require_role(["Admin", "Author"]))])
async def create_new_post(
    post_in: PostCreate,
    db: Session = Depends(get_async_db),
    current_user=Depends(get_current_user)
):
    user = await get_user_async(db, int(current_user["sub"]))
    return await create_post_async(db, user, post_in)

@router.get("/{post_id}", response_model=PostOut)
async def read_post(
    post_id: int,
    include_summary: bool = Query(False, description="Include AI-generated summary of the post"),
    db: Session = Depends(get_async_db),
    current_user=Depends(get_current_user)
):
    post = await get_post_async(db, post_id, include_summary)
    if post.status == PostStatus.draft:
        if post.author_id != int(current_user["sub"]) and current_user["role"] != "Admin":
            raise HTTPException(status_code=403, detail="You do not have access to this draft post")
    return post

@router.get("/", response_model=PaginatedResponse)
async def list_posts(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[PostStatus] = Query(None, description="Filter by post status"),
    author_id: Optional[int] = Query(None, ge=1, description="Filter by author ID"),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags"),
    created_after: Optional[datetime] = Query(None, description="Filter posts created after this date"),
    created_before: Optional[datetime] = Query(None, description="Filter posts created before this date"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    db: Session = Depends(get_async_db),
    current_user=Depends(get_current_user)
):
    skip = (page - 1) * size
    
    tag_list = None
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    filters = PostFilters(
        status=status,
        author_id=author_id,
        tags=tag_list,
        created_after=created_after,
        created_before=created_before,
        search=search
    )
    
    if current_user["role"] == "Admin":
        posts, total = await get_posts_for_admin_with_filters_async(db, filters, skip, size)
    elif current_user["role"] == "Author":
        posts, total = await get_posts_for_author_with_filters_async(db, int(current_user["sub"]), filters, skip, size)
    else:
        posts, total = await get_posts_for_reader_with_filters_async(db, filters, skip, size)
    
    pages = (total + size - 1) // size
    
    return PaginatedResponse(
        items=posts,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.put("/{post_id}", response_model=PostOut, dependencies=[Depends(require_role(["Admin", "Author"]))])
async def update_existing_post(
    post_id: int,
    post_update: PostUpdate,
    db: Session = Depends(get_async_db),
    current_user=Depends(get_current_user)
):
    post = await get_post_async(db, post_id)

    if post.author_id != int(current_user["sub"]) and current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Not allowed to update this post")
    return await update_post_async(db, post, post_update)

@router.delete("/{post_id}", status_code=204, dependencies=[Depends(require_role(["Admin", "Author"]))])
async def delete_existing_post(
    post_id: int,
    db: Session = Depends(get_async_db),
    current_user=Depends(get_current_user)
):
    post = await get_post_async(db, post_id)
    
    if post.author_id != int(current_user["sub"]) and current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Not allowed to delete this post")
    
    await delete_post_async(db, post)
    return

@router.post("/ai-quick-post", response_model=PostOut, dependencies=[Depends(require_role(["Admin", "Author"]))])
async def ai_quick_create_post(
    content: str = Query(..., min_length=1, max_length=5000, description="Post content - AI will generate title and tags"),
    db: Session = Depends(get_async_db),
    current_user=Depends(get_current_user)
):
    is_valid, error_message = validate_content_input(content, min_length=10, max_length=5000)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    user = await get_user_async(db, int(current_user["sub"]))
    return await create_quick_post_async(db, user, content)