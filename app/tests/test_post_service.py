import pytest
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone
from app.models.post import PostStatus
from app.schemas.post import PostCreate, PostUpdate, PostFilters
from app.services.post_service import (
    create_post, get_post, update_post, delete_post,
    get_posts_with_filters, create_quick_post
)
from app.schemas.post import PostFilters
from unittest.mock import patch

@pytest.fixture
def published_post(db_session, test_user):
    post_data = PostCreate(
        title="Published Post",
        content="Some content",
        status=PostStatus.published,
        tags=["python", "fastapi"]
    )
    return create_post(db_session, test_user, post_data)

@pytest.fixture
def draft_post(db_session, test_user):
    post_data = PostCreate(
        title="Draft Post",
        content="Draft content",
        status=PostStatus.draft,
        tags=["draft", "test"]
    )
    return create_post(db_session, test_user, post_data)

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
        assert len(post.post_tags) == 2
    
    def test_create_post_with_duplicate_tags(self, db_session, test_user):
        post_data = PostCreate(
            title="Test Post",
            content="This is a test post content.",
            status=PostStatus.draft,
            tags=["python", "fastapi", "python"]
        )
        post = create_post(db_session, test_user, post_data)
        assert len(post.post_tags) == 2 
    
    def test_create_post_no_tags(self, db_session, test_user):
        post_data = PostCreate(
            title="Test Post",
            content="This is a test post content.",
            status=PostStatus.published
        )
        post = create_post(db_session, test_user, post_data)
        assert post.title == "Test Post"
        assert len(post.post_tags) == 0
    
    def test_get_post_success(self, db_session, test_user):
        post_data = PostCreate(
            title="Test Post",
            content="This is a test post content.",
            status=PostStatus.published
        )
        created_post = create_post(db_session, test_user, post_data)
        
        post = get_post(db_session, created_post.id)
        assert post is not None
        assert post.title == "Test Post"
    
    def test_get_post_not_found(self, db_session):
        with pytest.raises(HTTPException) as exc_info:
            get_post(db_session, 999)
        assert exc_info.value.status_code == 404
    
    def test_get_posts_success(self, db_session, test_user):
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
        
        filters = PostFilters()
        posts, total = get_posts_with_filters(db_session, filters, skip=0, limit=10)
        assert len(posts) == 2
    
    def test_get_posts_pagination(self, db_session, test_user):
        for i in range(5):
            post_data = PostCreate(
                title=f"Post {i}",
                content=f"Content {i}",
                status=PostStatus.published
            )
            create_post(db_session, test_user, post_data)
        
        filters = PostFilters()
        posts, total = get_posts_with_filters(db_session, filters, skip=0, limit=3)
        assert len(posts) == 3
        
        posts, total = get_posts_with_filters(db_session, filters, skip=3, limit=3)
        assert len(posts) == 2
    
    def test_update_post_success(self, db_session, test_user):
        post_data = PostCreate(
            title="Original Title",
            content="Original content",
            status=PostStatus.draft
        )
        post = create_post(db_session, test_user, post_data)
        
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
        post_data = PostCreate(
            title="Original Title",
            content="Original content",
            status=PostStatus.draft
        )
        post = create_post(db_session, test_user, post_data)
        
        update_data = PostUpdate(title="Updated Title")
        updated_post = update_post(db_session, post, update_data)
        assert updated_post.title == "Updated Title"
        assert updated_post.content == "Original content"
        assert updated_post.status.name == PostStatus.draft.value
    
    def test_update_post_tags(self, db_session, test_user):
        post_data = PostCreate(
            title="Tag Update Post",
            content="Content for tag update",
            status=PostStatus.published,
            tags=["python", "fastapi"]
        )
        post = create_post(db_session, test_user, post_data)
        assert len(post.post_tags) == 2

        update_data = PostUpdate(tags=["ai", "ml"])
        updated_post = update_post(db_session, post, update_data)
        tag_names = [pt.tag.name for pt in updated_post.post_tags]
        assert set(tag_names) == {"ai", "ml"}
        assert len(updated_post.post_tags) == 2

        update_data = PostUpdate(tags=[])
        updated_post = update_post(db_session, post, update_data)
        assert len(updated_post.post_tags) == 0

        update_data = PostUpdate(tags=["python"])
        updated_post = update_post(db_session, post, update_data)
        tag_names = [pt.tag.name for pt in updated_post.post_tags]
        assert set(tag_names) == {"python"}
        assert len(updated_post.post_tags) == 1
    
    def test_delete_post_success(self, db_session, test_user):
        post_data = PostCreate(
            title="Test Post",
            content="This is a test post content.",
            status=PostStatus.published
        )
        post = create_post(db_session, test_user, post_data)
        post_id = post.id
        
        delete_post(db_session, post)
        
        with pytest.raises(HTTPException) as exc_info:
            get_post(db_session, post_id)
        assert exc_info.value.status_code == 404

def test_filter_by_status(db_session, test_user, published_post, draft_post):
    filters = PostFilters(status=PostStatus.published)
    posts, total = get_posts_with_filters(db_session, filters)
    assert all(p.status == PostStatus.published for p in posts)
    filters = PostFilters(status=PostStatus.draft)
    posts, total = get_posts_with_filters(db_session, filters)
    assert all(p.status == PostStatus.draft for p in posts)

def test_filter_by_author(db_session, test_user, published_post):
    post_data = PostCreate(
        title="Author's Post",
        content="By author",
        status=PostStatus.published,
        tags=["author"]
    )
    author_post = create_post(db_session, test_user, post_data)
    filters = PostFilters(author_id=test_user.id)
    posts, total = get_posts_with_filters(db_session, filters)
    assert all(p.author_id == test_user.id for p in posts)

def test_filter_by_tags(db_session, test_user, published_post):
    filters = PostFilters(tags=["python"])
    posts, total = get_posts_with_filters(db_session, filters)
    assert any("python" in p.tags for p in posts)
    filters = PostFilters(tags=["fastapi"])
    posts, total = get_posts_with_filters(db_session, filters)
    assert any("fastapi" in p.tags for p in posts)

def test_filter_by_date(db_session, test_user, published_post):
    now = datetime.now(timezone.utc)
    filters = PostFilters(created_after=now + timedelta(days=1))
    posts, total = get_posts_with_filters(db_session, filters)
    assert total == 0
    filters = PostFilters(created_before=now + timedelta(days=1))
    posts, total = get_posts_with_filters(db_session, filters)
    assert total >= 1

def test_search_in_title_and_content(db_session, test_user, published_post):
    filters = PostFilters(search="Published")
    posts, total = get_posts_with_filters(db_session, filters)
    assert any("Published" in p.title for p in posts)
    filters = PostFilters(search="content")
    posts, total = get_posts_with_filters(db_session, filters)
    assert any("content" in p.content for p in posts)

def test_pagination(db_session, test_user):
    for i in range(15):
        create_post(db_session, test_user, PostCreate(
            title=f"Post {i}",
            content="Bulk content",
            status=PostStatus.published,
            tags=["bulk"]
        ))
    filters = PostFilters(status=PostStatus.published)
    posts, total = get_posts_with_filters(db_session, filters, skip=0, limit=10)
    assert len(posts) == 10
    posts2, _ = get_posts_with_filters(db_session, filters, skip=10, limit=10)
    assert len(posts2) == min(5, total - 10)

def test_create_quick_post_success(db_session, test_user):
    """Test successful quick post creation with AI-generated title and tags"""
    with patch("app.services.post_service.get_title_and_tags_for_post") as mock_ai:
        mock_ai.return_value = {
            "title": "AI Generated Title",
            "tags": ["ai", "python", "fastapi"]
        }
        
        post = create_quick_post(db_session, test_user, "This is some content for the quick post.")
        
        assert post.title == "AI Generated Title"
        assert post.content == "This is some content for the quick post."
        assert post.status == PostStatus.draft
        assert len(post.post_tags) == 3
        tag_names = [pt.tag.name for pt in post.post_tags]
        assert set(tag_names) == {"ai", "python", "fastapi"}

def test_create_quick_post_http_exception(db_session, test_user):
    """Test quick post creation when AI service returns HTTP exception - should re-raise"""
    with patch("app.services.post_service.get_title_and_tags_for_post") as mock_ai:
        mock_ai.side_effect = HTTPException(status_code=500, detail="AI service error")
        
        with pytest.raises(HTTPException) as exc_info:
            create_quick_post(db_session, test_user, "This is some content for the quick post.")
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Failed to create quick post"