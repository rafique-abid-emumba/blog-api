from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.post import Post, PostStatus
from app.models.user import User
from app.models.tag import Tag
from app.models.posttag import PostTag
from app.schemas.post import PostCreate, PostUpdate, PostFilters
from fastapi import HTTPException
import logging
from typing import List, Tuple

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
        return post
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating post: {e}")
        raise HTTPException(status_code=500, detail="Failed to create post")

def get_post(db: Session, post_id: int) -> Post:
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            logger.warning("Attempted to get non-existent post")
            raise HTTPException(status_code=404, detail="Post not found")
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

def apply_search(query, search: str):
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
        
        posts = query.offset(skip).limit(limit).all()
        
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
    posts, total = get_posts_with_filters(db, filters, skip, limit)
    logger.info(f"Admin fetched {len(posts)} posts with filters (total: {total})")
    return posts, total

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
        
        posts = query.offset(skip).limit(limit).all()
        
        logger.info(f"Author {author_id} fetched {len(posts)} posts with filters (total: {total})")
        return posts, total
    except Exception as e:
        logger.error(f"Error fetching posts for author {author_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch posts")

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

def get_posts(db: Session, skip: int = 0, limit: int = 10):
    try:
        posts = db.query(Post).offset(skip).limit(limit).all()
        logger.info(f"Fetched {len(posts)} posts (skip={skip}, limit={limit})")
        return posts
    except Exception as e:
        logger.error(f"Error fetching posts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch posts")

def update_post(db: Session, post: Post, post_update: PostUpdate) -> Post:
    try:
        if not post:
            logger.warning("Attempted to update non-existent post")
            raise HTTPException(status_code=404, detail="Post not found")
        
        if post_update.title is not None:
            post.title = post_update.title
        if post_update.content is not None:
            post.content = post_update.content
        if post_update.status is not None:
            post.status = post_update.status
        if post_update.tags is not None:
            db.query(PostTag).filter(PostTag.post_id == post.id).delete()
            db.flush()
            set_post_tags(db, post, post_update.tags)
        db.commit()
        db.refresh(post)
        logger.info(f"Post updated successfully: {post.title} (ID: {post.id})")
        return post
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating post: {e}")
        raise HTTPException(status_code=500, detail="Failed to update post")

def delete_post(db: Session, post: Post):
    try:
        if not post:
            logger.warning("Attempted to delete non-existent post")
            raise HTTPException(status_code=404, detail="Post not found")
        
        db.delete(post)
        db.commit()
        logger.info(f"Post deleted: ID {post.id}")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting post: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete post")