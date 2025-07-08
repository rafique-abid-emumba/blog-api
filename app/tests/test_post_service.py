import pytest
from fastapi import HTTPException
from app.services.post_service import (
    create_post, get_post, get_posts, update_post, delete_post
)
from app.schemas.post import PostCreate, PostUpdate, PostStatus
from app.models.user import User
from app.models.role import Role

class TestPostService:
    
    def test_create_post_success(self, db_session, test_user):
        post_data = PostCreate(
            title="Test Post",
            content="This is a test post content.",
            status=PostStatus.published,
            tags=["python", "fastapi"]
        )
        post = create_post(db_session, test_user, post_data)
        assert post.title == "Test Post"
        assert post.content == "This is a test post content."
        assert post.status.name == PostStatus.published.value
        assert post.author_id == test_user.id
        assert len(post.post_tags) == 2  # Should have 2 tags
    
    def test_create_post_with_duplicate_tags(self, db_session, test_user):
        post_data = PostCreate(
            title="Test Post",
            content="This is a test post content.",
            status=PostStatus.draft,
            tags=["python", "fastapi", "python"]  # Duplicate tag
        )
        post = create_post(db_session, test_user, post_data)
        assert len(post.post_tags) == 2  # Should only have 2 unique tags
    
    def test_create_post_no_tags(self, db_session, test_user):
        post_data = PostCreate(
            title="Test Post",
            content="This is a test post content.",
            status=PostStatus.published
        )
        post = create_post(db_session, test_user, post_data)
        assert post.title == "Test Post"
        assert len(post.post_tags) == 0  # No tags
    
    def test_get_post_success(self, db_session, test_user):
        # Create a post first
        post_data = PostCreate(
            title="Test Post",
            content="This is a test post content.",
            status=PostStatus.published
        )
        created_post = create_post(db_session, test_user, post_data)
        
        # Get the post
        post = get_post(db_session, created_post.id)
        assert post is not None
        assert post.title == "Test Post"
    
    def test_get_post_not_found(self, db_session):
        post = get_post(db_session, 999)  # Non-existent ID
        assert post is None
    
    def test_get_posts_success(self, db_session, test_user):
        # Create multiple posts
        post_data1 = PostCreate(
            title="Post 1",
            content="Content 1",
            status=PostStatus.published
        )
        post_data2 = PostCreate(
            title="Post 2",
            content="Content 2",
            status=PostStatus.published
        )
        create_post(db_session, test_user, post_data1)
        create_post(db_session, test_user, post_data2)
        
        # Get posts
        posts = get_posts(db_session, skip=0, limit=10)
        assert len(posts) == 2
    
    def test_get_posts_pagination(self, db_session, test_user):
        # Create multiple posts
        for i in range(5):
            post_data = PostCreate(
                title=f"Post {i}",
                content=f"Content {i}",
                status=PostStatus.published
            )
            create_post(db_session, test_user, post_data)
        
        # Test pagination
        posts = get_posts(db_session, skip=0, limit=3)
        assert len(posts) == 3
        
        posts = get_posts(db_session, skip=3, limit=3)
        assert len(posts) == 2  # Only 2 posts left
    
    def test_update_post_success(self, db_session, test_user):
        # Create a post first
        post_data = PostCreate(
            title="Original Title",
            content="Original content",
            status=PostStatus.draft
        )
        post = create_post(db_session, test_user, post_data)
        
        # Update the post
        update_data = PostUpdate(
            title="Updated Title",
            content="Updated content",
            status=PostStatus.published
        )
        updated_post = update_post(db_session, post, update_data)
        assert updated_post.title == "Updated Title"
        assert updated_post.content == "Updated content"
        assert updated_post.status.name == PostStatus.published.value
    
    def test_update_post_partial(self, db_session, test_user):
        # Create a post first
        post_data = PostCreate(
            title="Original Title",
            content="Original content",
            status=PostStatus.draft
        )
        post = create_post(db_session, test_user, post_data)
        
        # Update only title
        update_data = PostUpdate(title="Updated Title")
        updated_post = update_post(db_session, post, update_data)
        assert updated_post.title == "Updated Title"
        assert updated_post.content == "Original content"  # Unchanged
        assert updated_post.status.name == PostStatus.draft.value  # Unchanged
    
    def test_delete_post_success(self, db_session, test_user):
        # Create a post first
        post_data = PostCreate(
            title="Test Post",
            content="This is a test post content.",
            status=PostStatus.published
        )
        post = create_post(db_session, test_user, post_data)
        post_id = post.id
        
        # Delete the post
        delete_post(db_session, post)
        
        # Verify it's deleted
        deleted_post = get_post(db_session, post_id)
        assert deleted_post is None 