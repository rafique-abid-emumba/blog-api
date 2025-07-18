import pytest
from app.schemas.comment import CommentCreate, CommentUpdate
from app.schemas.post import PostCreate
from app.schemas.user import UserCreate
from app.services.comment_service import (
    create_comment, get_comment, update_comment, delete_comment,
    list_comments_for_post, serialize_comment, serialize_comments,
    MAX_COMMENTS_PER_USER_PER_POST, MAX_COMMENTS_PER_POST
)
from app.services.post_service import create_post
from app.services.user_service import create_user
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from unittest.mock import patch

@pytest.fixture
def post(db_session, test_user):
    post_data = PostCreate(
        title="Test Post",
        content="Test Content",
        status="published",
        tags=[]
    )
    return create_post(db_session, test_user, post_data)

@pytest.fixture
def another_user(db_session):
    user_data = UserCreate(
        username="anotheruser",
        email="another@example.com",
        password="AnotherPass123!"
    )
    return create_user(db_session, user_data)

def test_create_top_level_comment(db_session, test_user, post):
    comment_in = CommentCreate(content="Top level", post_id=post.id)
    comment = create_comment(db_session, test_user, post, comment_in)
    assert comment.id is not None
    assert comment.parent_id is None
    assert comment.content == "Top level"

def test_create_reply_comment(db_session, test_user, post):
    parent = create_comment(db_session, test_user, post, CommentCreate(content="Parent", post_id=post.id))
    reply_in = CommentCreate(content="Reply", post_id=post.id, parent_id=parent.id)
    reply = create_comment(db_session, test_user, post, reply_in)
    assert reply.parent_id == parent.id
    db_session.refresh(parent)
    assert any(r.id == reply.id for r in parent.replies)

def test_per_user_per_post_limit(db_session, test_user, post):
    for i in range(MAX_COMMENTS_PER_USER_PER_POST):
        create_comment(db_session, test_user, post, CommentCreate(content=f"Comment {i}", post_id=post.id))
    with pytest.raises(HTTPException) as exc:
        create_comment(db_session, test_user, post, CommentCreate(content="Exceed", post_id=post.id))
    assert exc.value.status_code == 400
    assert "User can only comment" in exc.value.detail

def test_per_post_limit(db_session, test_user, another_user, post):
    original_limit = MAX_COMMENTS_PER_POST
    try:
        import app.services.comment_service as cs
        cs.MAX_COMMENTS_PER_POST = 5
        
        for i in range(5):
            user = test_user if i % 2 == 0 else another_user
            create_comment(db_session, user, post, CommentCreate(content=f"Comment {i}", post_id=post.id))
        with pytest.raises(HTTPException) as exc:
            create_comment(db_session, test_user, post, CommentCreate(content="Exceed", post_id=post.id))
        assert exc.value.status_code == 400
    finally:
        cs.MAX_COMMENTS_PER_POST = original_limit

def test_get_comment(db_session, test_user, post):
    comment = create_comment(db_session, test_user, post, CommentCreate(content="Get me", post_id=post.id))
    fetched = get_comment(db_session, comment.id)
    assert fetched.id == comment.id
    assert fetched.content == "Get me"

def test_list_comments_for_post(db_session, test_user, post):
    c1 = create_comment(db_session, test_user, post, CommentCreate(content="C1", post_id=post.id))
    c2 = create_comment(db_session, test_user, post, CommentCreate(content="C2", post_id=post.id))
    comments = list_comments_for_post(db_session, post.id)
    assert len(comments) == 2
    ids = {c.id for c in comments}
    assert c1.id in ids and c2.id in ids

def test_serialize_comment_with_replies(db_session, test_user, post):
    parent = create_comment(db_session, test_user, post, CommentCreate(content="Parent", post_id=post.id))
    reply = create_comment(db_session, test_user, post, CommentCreate(content="Reply", post_id=post.id, parent_id=parent.id))
    db_session.refresh(parent)
    data = serialize_comment(parent, max_depth=2)
    assert data["id"] == parent.id
    assert len(data["replies"]) == 1
    assert data["replies"][0]["id"] == reply.id

def test_update_comment_by_owner(db_session, test_user, post):
    comment = create_comment(db_session, test_user, post, CommentCreate(content="Old", post_id=post.id))
    updated = update_comment(db_session, comment, CommentUpdate(content="New"), test_user)
    assert updated.content == "New"

def test_update_comment_by_non_owner(db_session, test_user, another_user, post):
    comment = create_comment(db_session, test_user, post, CommentCreate(content="Old", post_id=post.id))
    with pytest.raises(HTTPException) as exc:
        update_comment(db_session, comment, CommentUpdate(content="Hack"), another_user)
    assert exc.value.status_code == 403

def test_delete_comment_by_owner(db_session, test_user, post):
    comment = create_comment(db_session, test_user, post, CommentCreate(content="Bye", post_id=post.id))
    delete_comment(db_session, comment, test_user)
    with pytest.raises(HTTPException) as exc:
        get_comment(db_session, comment.id)
    assert exc.value.status_code == 404

def test_delete_comment_by_non_owner(db_session, test_user, another_user, post):
    comment = create_comment(db_session, test_user, post, CommentCreate(content="Bye", post_id=post.id))
    with pytest.raises(HTTPException) as exc:
        delete_comment(db_session, comment, another_user)
    assert exc.value.status_code == 403

def test_cascade_delete_replies(db_session, test_user, post):
    parent = create_comment(db_session, test_user, post, CommentCreate(content="Parent", post_id=post.id))
    reply = create_comment(db_session, test_user, post, CommentCreate(content="Reply", post_id=post.id, parent_id=parent.id))
    delete_comment(db_session, parent, test_user)
    with pytest.raises(HTTPException) as exc:
        get_comment(db_session, parent.id)
    assert exc.value.status_code == 404
    with pytest.raises(HTTPException) as exc:
        get_comment(db_session, reply.id)
    assert exc.value.status_code == 404

def test_create_comment_with_sentiment_and_abuse(db_session, test_user, post):
    with patch("app.services.comment_service.analyze_comment") as mock_analyze:
        mock_analyze.return_value.sentiment = "positive"
        mock_analyze.return_value.abusive_flag = False

        comment_in = CommentCreate(content="Nice post!", post_id=post.id)
        comment = create_comment(db_session, test_user, post, comment_in)
        assert comment.sentiment == "positive"
        assert comment.is_abusive == 0

def test_create_comment_abusive_flag(db_session, test_user, post):
    with patch("app.services.comment_service.analyze_comment") as mock_analyze:
        mock_analyze.return_value.sentiment = "negative"
        mock_analyze.return_value.abusive_flag = True

        comment_in = CommentCreate(content="You are terrible!", post_id=post.id)
        comment = create_comment(db_session, test_user, post, comment_in)
        assert comment.sentiment == "negative"
        assert comment.is_abusive == 1

def test_update_comment_reanalyzes_sentiment_and_abuse(db_session, test_user, post):
    with patch("app.services.comment_service.analyze_comment") as mock_analyze:
        mock_analyze.return_value.sentiment = "neutral"
        mock_analyze.return_value.abusive_flag = False
        comment = create_comment(db_session, test_user, post, CommentCreate(content="OK", post_id=post.id))
        assert comment.sentiment == "neutral"
        assert comment.is_abusive == 0

        mock_analyze.return_value.sentiment = "negative"
        mock_analyze.return_value.abusive_flag = True
        updated = update_comment(db_session, comment, CommentUpdate(content="You suck!"), test_user)
        assert updated.sentiment == "negative"
        assert updated.is_abusive == 1

def test_create_comment_analysis_failure_defaults(db_session, test_user, post):
    with patch("app.services.comment_service.analyze_comment", side_effect=Exception("GenAI error")):
        comment_in = CommentCreate(content="Whatever", post_id=post.id)
        comment = create_comment(db_session, test_user, post, comment_in)
        assert comment.sentiment == "neutral"
        assert comment.is_abusive == 0

def test_update_comment_analysis_failure_keeps_existing(db_session, test_user, post):
    with patch("app.services.comment_service.analyze_comment") as mock_analyze:
        mock_analyze.return_value.sentiment = "positive"
        mock_analyze.return_value.abusive_flag = False
        comment = create_comment(db_session, test_user, post, CommentCreate(content="Nice!", post_id=post.id))
        assert comment.sentiment == "positive"
        assert comment.is_abusive == 0

    with patch("app.services.comment_service.analyze_comment", side_effect=Exception("GenAI error")):
        updated = update_comment(db_session, comment, CommentUpdate(content="Changed!"), test_user)
        assert updated.sentiment == "positive"
        assert updated.is_abusive == 0