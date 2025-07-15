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