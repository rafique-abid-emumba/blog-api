from sqlalchemy.orm import Session
from app.models.post import Post, PostStatus
from app.models.user import User
from app.models.tag import Tag
from app.models.posttag import PostTag
from app.schemas.post import PostCreate, PostUpdate
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

def create_post(db: Session, author: User, post_in: PostCreate) -> Post:
    try:
        post = Post(
            title=post_in.title,
            content=post_in.content,
            status=post_in.status,
            author_id=author.id
        )
        db.add(post)
        db.flush()  # Get post.id before adding tags

        # Handle tags, removing duplicates from input
        if post_in.tags:
            unique_tags = set(post_in.tags)  # Remove duplicates from input
            for tag_name in unique_tags:
                tag = db.query(Tag).filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.add(tag)
                    db.flush()
                db.add(PostTag(post_id=post.id, tag_id=tag.id))
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
            logger.warning(f"Post not found: ID {post_id}")
        return post
    except Exception as e:
        logger.error(f"Error fetching post: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch post")

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
        if post_update.title is not None:
            post.title = post_update.title
        if post_update.content is not None:
            post.content = post_update.content
        if post_update.status is not None:
            post.status = post_update.status
        db.commit()
        db.refresh(post)
        logger.info(f"Post updated successfully: {post.title} (ID: {post.id})")
        return post
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating post: {e}")
        raise HTTPException(status_code=500, detail="Failed to update post")

def delete_post(db: Session, post: Post):
    try:
        db.delete(post)
        db.commit()
        logger.info(f"Post deleted: ID {post.id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting post: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete post")