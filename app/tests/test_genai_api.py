from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch

client = TestClient(app)



def test_trending_tags_endpoint():
    with patch("app.services.genai_service.suggest_trending_tags") as mock_trending:
        mock_trending.return_value = ["python", "fastapi", "llm"]
        response = client.get("/genai/trending-ai?limit=3&days=7")
        assert response.status_code == 200
        data = response.json()
        assert "trending_tags" in data
        assert isinstance(data["trending_tags"], list)
        assert data["trending_tags"] == ["python", "fastapi", "llm"]
        assert "analysis_period_days" in data
        assert "posts_analyzed" in data
        assert "total_comments_analyzed" in data

def test_title_tag_suggestion():
    with patch("app.services.genai_service.suggest_title_and_tags") as mock_suggest:
        mock_suggest.return_value = {"title": "AI in Python", "tags": ["python", "ai", "llm"]}
        payload = {"post_content": "Python is a popular programming language for AI."}
        response = client.post("/genai/title-tags", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "AI in Python"
        assert data["tags"] == ["python", "ai", "llm"]

def test_summarize_post():
    with patch("app.services.genai_service.summarize_post") as mock_summarize:
        mock_summarize.return_value = {"summary": "Docker helps containerize apps.", "citations": ["Docker"]}
        payload = {"post_content": "Docker is a platform for containerizing applications."}
        response = client.post("/genai/summarize", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["summary"] == "Docker helps containerize apps."
        assert data["citations"] == ["Docker"]

def test_qa_post():
    with patch("app.services.genai_service.answer_question_about_post") as mock_qa:
        mock_qa.return_value = {"answer": "FastAPI is used for documented APIs.", "citations": ["FastAPI"]}
        payload = {"post_id": 1, "question": "What we use FastAPI?"}
        response = client.post("/genai/qa", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "FastAPI is used for" in data["answer"]
        assert data["citations"] == ["FastAPI"]

def test_comment_analysis():
    with patch("app.services.genai_service.analyze_comment_sentiment") as mock_analysis:
        mock_analysis.return_value = {"sentiment": "positive", "is_abusive": False}
        payload = {"comment": "Great post!"}
        response = client.post("/genai/comment-analysis", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["sentiment"] == "positive"
        assert data["is_abusive"] is False
        assert data["comment"] == "Great post!"

def test_qa_global_success():
    with patch("app.services.genai_service.answer_question_global") as mock_qa:
        mock_qa.return_value = {
            "answer": "FastAPI is a modern web framework for building APIs with Python.",
            "citations": [
                {"text": "FastAPI provides automatic API documentation", "post_id": 1},
                {"text": "FastAPI is built on top of Starlette", "post_id": 2}
            ]
        }
        payload = {"question": "What is FastAPI?"}
        response = client.post("/genai/qa-global", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "FastAPI is a modern web framework" in data["answer"]
        assert len(data["citations"]) == 2
        assert data["citations"][0]["text"] == "FastAPI provides automatic API documentation"
        assert data["citations"][0]["post_id"] == 1

def test_qa_global_no_posts():
    """Test global Q&A when no published posts exist"""
    with patch("app.services.genai_service.answer_question_global") as mock_qa:
        mock_qa.return_value = {
            "answer": "No published content is available to answer this question.",
            "citations": []
        }
        payload = {"question": "What is Python?"}
        response = client.post("/genai/qa-global", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "No published content is available" in data["answer"]
        assert data["citations"] == []

def test_qa_global_no_vector_data():
    """Test global Q&A when no vector data is available"""
    with patch("app.services.genai_service.answer_question_global") as mock_qa:
        mock_qa.return_value = {
            "answer": "No content is available in the vector database to answer this question.",
            "citations": []
        }
        payload = {"question": "What is Python?"}
        response = client.post("/genai/qa-global", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "No content is available in the vector database" in data["answer"]
        assert data["citations"] == []

def test_qa_global_validation_short_question():
    """Test global Q&A endpoint with very short question"""
    payload = {"question": "Hi"}
    response = client.post("/genai/qa-global", json=payload)
    assert response.status_code == 400
    assert "Content must be at least 10 characters long" in response.json()["detail"]

def test_qa_global_validation_numeric_question():
    """Test global Q&A endpoint with only numbers"""
    payload = {"question": "12345678945"}
    response = client.post("/genai/qa-global", json=payload)
    assert response.status_code == 400
    assert "Content cannot be only numbers" in response.json()["detail"]

def test_title_tags_validation_short_content():
    payload = {"post_content": "Hi"}
    response = client.post("/genai/title-tags", json=payload)
    assert response.status_code == 400
    assert "Content must be at least 10 characters long" in response.json()["detail"]

def test_title_tags_validation_numeric_content():
    payload = {"post_content": "12345678901234567890"}
    response = client.post("/genai/title-tags", json=payload)
    assert response.status_code == 400
    assert "Content cannot be only numbers" in response.json()["detail"]

def test_title_tags_validation_repetitive_content():
    payload = {"post_content": "aaaaaaaaaaaaaaaa"}
    response = client.post("/genai/title-tags", json=payload)
    assert response.status_code == 400
    assert "Content appears to be repetitive" in response.json()["detail"]

def test_summarize_validation_short_content():
    payload = {"post_content": "Hello world"}
    response = client.post("/genai/summarize", json=payload)
    assert response.status_code == 400
    assert "Content must be at least 20 characters long" in response.json()["detail"]

def test_summarize_validation_numeric_content():
    payload = {"post_content": "12345678901234567890"}
    response = client.post("/genai/summarize", json=payload)
    assert response.status_code == 400
    assert "Content cannot be only numbers" in response.json()["detail"]

def test_qa_validation_short_question():
    payload = {"post_id": 1, "question": "Hi"}
    response = client.post("/genai/qa", json=payload)
    assert response.status_code == 400
    assert "Content must be at least 10 characters long" in response.json()["detail"]

def test_qa_validation_numeric_question():
    payload = {"post_id": 1, "question": "12345678945"}
    response = client.post("/genai/qa", json=payload)
    assert response.status_code == 400
    assert "Content cannot be only numbers" in response.json()["detail"]

def test_comment_analysis_validation_short_comment():
    payload = {"comment": "Hi"}
    response = client.post("/genai/comment-analysis", json=payload)
    assert response.status_code == 400
    assert "Content must be at least 3 characters long" in response.json()["detail"]

def test_comment_analysis_validation_numeric_comment():
    payload = {"comment": "12345678945"}
    response = client.post("/genai/comment-analysis", json=payload)
    assert response.status_code == 400
    assert "Content cannot be only numbers" in response.json()["detail"]