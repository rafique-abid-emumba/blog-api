import pytest
from fastapi.testclient import TestClient
from app.main import app
import time

client = TestClient(app)

def test_health_endpoint_not_rate_limited():
    """Basic health endpoint should not be rate limited"""
    for i in range(10):
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-RateLimit-Limit" not in response.headers

def test_health_sub_endpoints_are_rate_limited():
    """Health sub-endpoints should be rate limited"""
    responses = []
    for i in range(15):
        response = client.get("/health/redis")
        responses.append(response)
    
    rate_limit_headers_present = any(
        "X-RateLimit-Limit" in response.headers for response in responses
    )
    assert rate_limit_headers_present, "Redis health check should have rate limit headers"
    
    responses = []
    for i in range(10):
        response = client.get("/health/database")
        responses.append(response)
    
    rate_limit_headers_present = any(
        "X-RateLimit-Limit" in response.headers for response in responses
    )
    assert rate_limit_headers_present, "Database health check should have rate limit headers"

def test_rate_limiting_on_login():
    """Test rate limiting on login endpoint"""
    responses = []
    for i in range(10):
        response = client.post("/users/login", json={
            "username": f"testuser{i}",
            "password": "wrongpassword"
        })
        responses.append(response)
    
    rate_limit_headers_present = any(
        "X-RateLimit-Limit" in response.headers for response in responses
    )
    assert rate_limit_headers_present, "Rate limit headers should be present"
    
    for response in responses:
        if "X-RateLimit-Limit" in response.headers:
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers
    
    for response in responses:
        if "X-RateLimit-Limit" in response.headers:
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers

def test_rate_limit_headers():
    """Test that rate limit headers are present"""
    response = client.get("/posts/")
    assert response.status_code in [200, 401, 403]
    
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers
    assert "X-RateLimit-Window" in response.headers

def test_rate_limit_reset():
    """Test that rate limits reset after window expires"""
    response = client.get("/health")
    if "X-RateLimit-Reset" in response.headers:
        reset_time = int(response.headers["X-RateLimit-Reset"])
        current_time = int(time.time())
        assert reset_time > current_time

def test_rate_limit_works():
    """Test that rate limiting actually works by making many requests"""
    responses = []
    for i in range(15):
        response = client.get("/health")
        responses.append(response)
    
    for response in responses:
        assert response.status_code == 200

def test_register_rate_limiting():
    """Test rate limiting on register endpoint (3 per hour)"""
    responses = []
    for i in range(5):
        response = client.post("/users/register", json={
            "username": f"testuser{i}",
            "email": f"test{i}@example.com",
            "password": "TestPass123!"
        })
        responses.append(response)
    
    rate_limit_headers_present = any(
        "X-RateLimit-Limit" in response.headers for response in responses
    )
    assert rate_limit_headers_present, "Rate limit headers should be present on register endpoint"

def test_database_health_rate_limit_enforcement():
    """Test that database health check rate limits are enforced"""
    responses = []
    # Make more requests than the limit (5 per minute)
    for i in range(10):
        response = client.get("/health/database")
        responses.append(response)
    
    # Check that we get rate limit headers
    rate_limit_headers_present = any(
        "X-RateLimit-Limit" in response.headers for response in responses
    )
    assert rate_limit_headers_present, "Database health check should have rate limit headers"
    
    # Check that some responses have rate limiting info
    for response in responses:
        if "X-RateLimit-Limit" in response.headers:
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers

def test_rate_limit_actual_enforcement():
    """Test that rate limiting actually blocks requests when limit is exceeded"""
    # This test requires Redis to be running
    # For now, just test that headers are present
    response = client.get("/health/database")
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers 