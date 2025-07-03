from sqlalchemy.orm import Session
from app.models.post import Post, PostStatus
from app.models.user import User
from app.models.tag import Tag
from app.models.posttag import PostTag
from app.schemas.post import PostCreate, PostUpdate

def create_post(db: Session, author: User, post_in: PostCreate) -> Post:
    post = Post(
        title=post_in.title,
        content=post_in.content,
        status=post_in.status,
        author_id=author.id
    )
    db.add(post)
    db.flush()  # Get post.id before adding tags

    # Handle tags
    if post_in.tags:
        for tag_name in post_in.tags:
            tag = db.query(Tag).filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                db.flush()
            db.add(PostTag(post_id=post.id, tag_id=tag.id))
    db.commit()
    db.refresh(post)
    return post

def get_post(db: Session, post_id: int) -> Post:
    return db.query(Post).filter(Post.id == post_id).first()

def get_posts(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Post).offset(skip).limit(limit).all()

def update_post(db: Session, post: Post, post_update: PostUpdate) -> Post:
    if post_update.title is not None:
        post.title = post_update.title
    if post_update.content is not None:
        post.content = post_update.content
    if post_update.status is not None:
        post.status = post_update.status
    db.commit()
    db.refresh(post)
    return post

def delete_post(db: Session, post: Post):
    db.delete(post)
    db.commit()