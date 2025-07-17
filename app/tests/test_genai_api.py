import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_title_tag_suggestion():
    payload = {
        "post_content": "Python is a popular programming language for web development, data science, and more."
    }
    response = client.post("/genai/title-tags", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "title" in data
    assert isinstance(data["title"], str)
    assert "tags" in data
    assert isinstance(data["tags"], list)
    assert all(isinstance(tag, str) for tag in data["tags"])

def test_summarize_post():
    payload = {
        "post_content": "Docker is a platform that helps developers containerize applications easily. It allows for consistent environments and simplifies deployment across different systems. With Docker, you can package your app and its dependencies into a single container, making it portable and scalable."
    }
    response = client.post("/genai/summarize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert isinstance(data["summary"], str)
    assert "citations" in data
    assert isinstance(data["citations"], list)
    assert all(isinstance(c, str) for c in data["citations"])

def test_qa_post():
    post_id = 123
    post_content = "FastAPI is a modern, fast web framework for building APIs with Python. It is based on standard Python type hints."
    from app.genai.embeddings_store import embed_and_store_post
    embed_and_store_post(post_id, post_content)
    payload = {
        "post_id": post_id,
        "question": "What is FastAPI used for?"
    }
    response = client.post("/genai/qa", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert isinstance(data["answer"], str)
    assert "citations" in data
    assert isinstance(data["citations"], list)
    assert all(isinstance(c, str) for c in data["citations"]) 