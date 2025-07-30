from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import selectinload
from app.models.post import Post, PostStatus
from app.models.user import User
from app.models.tag import Tag
from app.models.posttag import PostTag
from app.schemas.post import PostCreate, PostUpdate, PostFilters, PaginatedResponse
from fastapi import HTTPException
import logging
from typing import List, Tuple, Optional
from app.services.embedding_service import embed_and_store_post, delete_post_embeddings
from app.services.genai_service import get_summary_for_post, get_title_and_tags_for_post
from app.services.cache_service import PostCacheService

logger = logging.getLogger(__name__)

def set_post_tags(db: Session, post: Post, tags: list[str]):
    unique_tags = set(tags)
    for tag_name in unique_tags:
        tag = db.query(Tag).filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            db.flush()
        db.add(PostTag(post_id=post.id, tag_id=tag.id))

async def set_post_tags_async(db, post: Post, tags: list[str]):
    unique_tags = set(tags)
    for tag_name in unique_tags:
        result = await db.execute(select(Tag).filter(Tag.name == tag_name))
        tag = result.scalar_one_or_none()
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            await db.flush()
        db.add(PostTag(post_id=post.id, tag_id=tag.id))

def create_post(db: Session, author: User, post_in: PostCreate) -> Post:
    try:
        post = Post(
            title=post_in.title,
            content=post_in.content,
            status=post_in.status,
            author_id=author.id
        )
        db.add(post)
        db.flush()

        if post_in.tags:
            set_post_tags(db, post, post_in.tags)
        db.commit()
        db.refresh(post)
        logger.info(f"Post created successfully: {post.title} (ID: {post.id})")
        
        if post.status == PostStatus.published.value:
            embed_and_store_post(post.id, post.content)
            logger.info(f"Embeddings stored for published post {post.id}")
        else:
            logger.info(f"Skipping embedding storage for draft post {post.id}")
        
        return post
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating post: {e}")
        raise HTTPException(status_code=500, detail="Failed to create post")

async def create_post_async(db, author: User, post_in: PostCreate) -> Post:
    try:
        post = Post(
            title=post_in.title,
            content=post_in.content,
            status=post_in.status,
            author_id=author.id
        )
        db.add(post)
        await db.flush()

        if post_in.tags:
            await set_post_tags_async(db, post, post_in.tags)
        await db.commit()

        result = await db.execute(
            select(Post)
            .options(
                selectinload(Post.author),
                selectinload(Post.post_tags).selectinload(PostTag.tag)
            )
            .filter(Post.id == post.id)
        )
        post = result.scalar_one()
        logger.info(f"Post created successfully: {post.title} (ID: {post.id})")
        
        if post.status == PostStatus.published.value:
            embed_and_store_post(post.id, post.content)
            logger.info(f"Embeddings stored for published post {post.id}")
        else:
            logger.info(f"Skipping embedding storage for draft post {post.id}")
        
        await PostCacheService.invalidate_user_posts(author.id)
        await PostCacheService.invalidate_all_posts()
        
        return post
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating post: {e}")
        raise HTTPException(status_code=500, detail="Failed to create post")

def get_post(db: Session, post_id: int, include_summary: bool = False) -> Post:
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            logger.warning("Attempted to get non-existent post")
            raise HTTPException(status_code=404, detail="Post not found")
        
        if include_summary:
            try:
                summary_result = get_summary_for_post(post.content)
                post.summary = summary_result.get("summary", "")
                logger.info(f"Summary generated for post {post_id}")
            except Exception as e:
                logger.warning(f"Failed to generate summary for post {post_id}: {e}")
                post.summary = None
        
        return post
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching post: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch post")

async def get_post_async(db, post_id: int, include_summary: bool = False) -> Post:
    try:
        result = await db.execute(
            select(Post)
            .options(
                selectinload(Post.author),
                selectinload(Post.post_tags).selectinload(PostTag.tag)
            )
            .filter(Post.id == post_id)
        )
        post = result.scalar_one_or_none()
        
        if not post:
            logger.warning("Attempted to get non-existent post")
            raise HTTPException(status_code=404, detail="Post not found")
        
        if include_summary:
            try:
                summary_result = get_summary_for_post(post.content)
                post.summary = summary_result.get("summary", "")
                logger.info(f"Summary generated for post {post_id}")
            except Exception as e:
                logger.warning(f"Failed to generate summary for post {post_id}: {e}")
                post.summary = None
        
        return post
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching post: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch post")

def apply_tag_filter(db: Session, query, tags: List[str]):
    tag_ids = db.query(Tag.id).filter(Tag.name.in_(tags)).subquery()
    post_tag_ids = db.query(PostTag.post_id).filter(PostTag.tag_id.in_(tag_ids.select())).subquery()
    return query.filter(Post.id.in_(post_tag_ids.select()))

async def apply_tag_filter_async(db, query, tags: List[str]):
    result = await db.execute(select(Tag.id).filter(Tag.name.in_(tags)))
    tag_ids = result.scalars().all()
    
    if tag_ids:
        result = await db.execute(select(PostTag.post_id).filter(PostTag.tag_id.in_(tag_ids)))
        post_tag_ids = result.scalars().all()
        return query.filter(Post.id.in_(post_tag_ids))
    return query.filter(False)

def apply_filters(query, filters: PostFilters, db: Session):
    if filters.status:
        query = query.filter(Post.status == filters.status.value)
    if filters.author_id:
        query = query.filter(Post.author_id == filters.author_id)
    if filters.created_after:
        query = query.filter(Post.created_at >= filters.created_after)
    if filters.created_before:
        query = query.filter(Post.created_at <= filters.created_before)
    if filters.tags:
        query = apply_tag_filter(db, query, filters.tags)
    return query

async def apply_filters_async(query, filters: PostFilters, db):
    if filters.status:
        query = query.filter(Post.status == filters.status.value)
    if filters.author_id:
        query = query.filter(Post.author_id == filters.author_id)
    if filters.created_after:
        query = query.filter(Post.created_at >= filters.created_after)
    if filters.created_before:
        query = query.filter(Post.created_at <= filters.created_before)
    if filters.tags:
        query = await apply_tag_filter_async(db, query, filters.tags)
    return query

def apply_search(query, search: str):
    search_term = f"%{search}%"
    return query.filter(
        or_(
            Post.title.ilike(search_term),
            Post.content.ilike(search_term)
        )
    )

async def apply_search_async(query, search: str):
    search_term = f"%{search}%"
    return query.filter(
        or_(
            Post.title.ilike(search_term),
            Post.content.ilike(search_term)
        )
    )

def get_posts_with_filters(
    db: Session, 
    filters: PostFilters, 
    skip: int = 0, 
    limit: int = 10
) -> Tuple[List[Post], int]:
    try:
        query = db.query(Post)
        query = apply_filters(query, filters, db)
        
        if filters.search:
            query = apply_search(query, filters.search)
        
        total = query.count()
        posts = query.order_by(Post.created_at.desc()).offset(skip).limit(limit).all()
        
        logger.info(f"Fetched {len(posts)} posts with filters (total: {total})")
        return posts, total
    except Exception as e:
        logger.error(f"Error fetching posts with filters: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch posts")

async def get_posts_with_filters_async(
    db, 
    filters: PostFilters, 
    skip: int = 0, 
    limit: int = 10,
    user_role: str = "Reader",
    author_id: Optional[int] = None
) -> Tuple[List[Post], int]:
    page = (skip // limit) + 1
    
    cached_response = await PostCacheService.get_cached_posts(
        user_role, filters, page, limit, author_id
    )
    if cached_response:
        return cached_response.items, cached_response.total
    
    try:
        query = select(Post).options(
            selectinload(Post.author),
            selectinload(Post.post_tags).selectinload(PostTag.tag)
        )
        
        if user_role == "Author" and author_id:
            query = query.filter(
                or_(
                    Post.status == PostStatus.published,
                    and_(Post.status == PostStatus.draft, Post.author_id == author_id)
                )
            )
        
        query = await apply_filters_async(query, filters, db)
        
        if filters.search:
            query = await apply_search_async(query, filters.search)
        
        count_result = await db.execute(query)
        total = len(count_result.scalars().all())
        
        posts_result = await db.execute(
            query.order_by(Post.created_at.desc()).offset(skip).limit(limit)
        )
        posts = posts_result.scalars().all()
        
        response = PaginatedResponse(
            items=posts,
            total=total,
            page=page,
            size=limit,
            pages=(total + limit - 1) // limit
        )
        
        await PostCacheService.cache_posts(response, user_role, filters, page, limit, author_id)
        
        logger.info(f"Fetched {len(posts)} posts with filters (total: {total})")
        return posts, total
    except Exception as e:
        logger.error(f"Error fetching posts with filters: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch posts")

def get_posts_for_admin_with_filters(
    db: Session, 
    filters: PostFilters, 
    skip: int = 0, 
    limit: int = 10
) -> Tuple[List[Post], int]:
    return get_posts_with_filters(db, filters, skip, limit)

async def get_posts_for_admin_with_filters_async(
    db, 
    filters: PostFilters, 
    skip: int = 0, 
    limit: int = 10
) -> Tuple[List[Post], int]:
    return await get_posts_with_filters_async(db, filters, skip, limit, "Admin")

def get_posts_for_author_with_filters(
    db: Session, 
    author_id: int, 
    filters: PostFilters, 
    skip: int = 0, 
    limit: int = 10
) -> Tuple[List[Post], int]:
    try:
        query = db.query(Post).filter(
            or_(
                Post.status == PostStatus.published,
                and_(Post.status == PostStatus.draft, Post.author_id == author_id)
            )
        )
        query = apply_filters(query, filters, db)
        
        if filters.search:
            query = apply_search(query, filters.search)
        
        total = query.count()
        posts = query.order_by(Post.created_at.desc()).offset(skip).limit(limit).all()
        
        logger.info(f"Author {author_id} fetched {len(posts)} posts with filters (total: {total})")
        return posts, total
    except Exception as e:
        logger.error(f"Error fetching posts for author {author_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch posts")

async def get_posts_for_author_with_filters_async(
    db, 
    author_id: int, 
    filters: PostFilters, 
    skip: int = 0, 
    limit: int = 10
) -> Tuple[List[Post], int]:
    return await get_posts_with_filters_async(db, filters, skip, limit, "Author", author_id)

def get_posts_for_reader_with_filters(
    db: Session, 
    filters: PostFilters, 
    skip: int = 0, 
    limit: int = 10
) -> Tuple[List[Post], int]:
    try:
        filters.status = PostStatus.published
        posts, total = get_posts_with_filters(db, filters, skip, limit)
        logger.info(f"Reader fetched {len(posts)} published posts with filters (total: {total})")
        return posts, total
    except Exception as e:
        logger.error(f"Error fetching posts for reader: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch posts")

async def get_posts_for_reader_with_filters_async(
    db, 
    filters: PostFilters, 
    skip: int = 0, 
    limit: int = 10
) -> Tuple[List[Post], int]:
    try:
        filters.status = PostStatus.published
        posts, total = await get_posts_with_filters_async(db, filters, skip, limit, "Reader")
        logger.info(f"Reader fetched {len(posts)} published posts with filters (total: {total})")
        return posts, total
    except Exception as e:
        logger.error(f"Error fetching posts for reader: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch posts")


def update_post(db: Session, post: Post, post_update: PostUpdate) -> Post:
    try:
        update_data = post_update.model_dump(exclude_unset=True)
        
        tags_to_update = update_data.pop('tags', None)
        
        for field, value in update_data.items():
            setattr(post, field, value)
        
        if tags_to_update is not None:
            db.query(PostTag).filter(PostTag.post_id == post.id).delete()
            db.flush()
            set_post_tags(db, post, tags_to_update)
        
        db.commit()
        db.refresh(post)
        logger.info(f"Post updated successfully: {post.title} (ID: {post.id})")
        
        if post_update.content is not None or post_update.status is not None:
            delete_post_embeddings(post.id)
            
            if post.status == PostStatus.published.value:
                embed_and_store_post(post.id, post.content)
                logger.info(f"Embeddings stored for published post {post.id}")
            else:
                logger.info(f"Skipping embedding storage for draft post {post.id}")
        
        return post
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating post: {e}")
        raise HTTPException(status_code=500, detail="Failed to update post")

async def update_post_async(db, post: Post, post_update: PostUpdate) -> Post:
    try:
        update_data = post_update.model_dump(exclude_unset=True)
        
        tags_to_update = update_data.pop('tags', None)
        
        for field, value in update_data.items():
            setattr(post, field, value)
        
        if tags_to_update is not None:
            await db.execute(select(PostTag).filter(PostTag.post_id == post.id))
            await db.commit()
            await set_post_tags_async(db, post, tags_to_update)
        
        await db.commit()
        result = await db.execute(
            select(Post)
            .options(
                selectinload(Post.author),
                selectinload(Post.post_tags).selectinload(PostTag.tag)
            )
            .filter(Post.id == post.id)
        )
        post = result.scalar_one()
        logger.info(f"Post updated successfully: {post.title} (ID: {post.id})")
        
        if post_update.content is not None or post_update.status is not None:
            delete_post_embeddings(post.id)
            
            if post.status == PostStatus.published.value:
                embed_and_store_post(post.id, post.content)
                logger.info(f"Embeddings stored for published post {post.id}")
            else:
                logger.info(f"Skipping embedding storage for draft post {post.id}")
        
        await PostCacheService.invalidate_user_posts(post.author_id)
        await PostCacheService.invalidate_all_posts()
        
        return post
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating post: {e}")
        raise HTTPException(status_code=500, detail="Failed to update post")

def delete_post(db: Session, post: Post):
    try:
        delete_post_embeddings(post.id)
        
        db.delete(post)
        db.commit()
        logger.info(f"Post deleted successfully: {post.title} (ID: {post.id})")
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting post: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete post")

async def delete_post_async(db, post: Post):
    try:
        delete_post_embeddings(post.id)
        
        await db.delete(post)
        await db.commit()
        logger.info(f"Post deleted successfully: {post.title} (ID: {post.id})")
        
        await PostCacheService.invalidate_user_posts(post.author_id)
        await PostCacheService.invalidate_all_posts()
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting post: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete post")

def create_quick_post(db, user, content: str):
    try:
        ai_result = get_title_and_tags_for_post(content)
        
        post = Post(
            title=ai_result.get("title", "Quick Post"),
            content=content,
            status=PostStatus.draft,
            author_id=user.id
        )
        db.add(post)
        db.flush()
        
        tags = ai_result.get("tags", ["quick", "draft"])
        set_post_tags(db, post, tags)
        
        db.commit()
        db.refresh(post)
        logger.info(f"Quick post created: {post.title} (ID: {post.id})")
        return post
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating quick post: {e}")
        raise HTTPException(status_code=500, detail="Failed to create quick post")

async def create_quick_post_async(db, user, content: str):
    try:
        ai_result = get_title_and_tags_for_post(content)
        
        post = Post(
            title=ai_result.get("title", "Quick Post"),
            content=content,
            status=PostStatus.draft,
            author_id=user.id
        )
        db.add(post)
        await db.flush()
        
        tags = ai_result.get("tags", ["quick", "draft"])
        await set_post_tags_async(db, post, tags)
        
        await db.commit()
        
        result = await db.execute(
            select(Post)
            .options(
                selectinload(Post.author),
                selectinload(Post.post_tags).selectinload(PostTag.tag)
            )
            .filter(Post.id == post.id)
        )
        post = result.scalar_one()
        logger.info(f"Quick post created: {post.title} (ID: {post.id})")
        
        await PostCacheService.invalidate_user_posts(user.id)
        await PostCacheService.invalidate_all_posts()
        
        return post
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating quick post: {e}")
        raise HTTPException(status_code=500, detail="Failed to create quick post")