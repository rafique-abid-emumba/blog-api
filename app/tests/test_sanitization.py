from app.utils.sanitizer import sanitize_html_content, sanitize_username, sanitize_email, validate_content_length

def test_sanitize_html_content():
    malicious_content = "<script>alert('xss')</script><p>Hello</p>"
    sanitized = sanitize_html_content(malicious_content)
    assert "<script>" not in sanitized
    assert "alert('xss')" not in sanitized
    assert "<p>Hello</p>" in sanitized
    
    safe_content = "<p>Hello <strong>world</strong></p>"
    sanitized = sanitize_html_content(safe_content)
    assert "<p>" in sanitized
    assert "<strong>" in sanitized
    
    long_content = "a" * 10001
    sanitized = sanitize_html_content(long_content, max_length=10000)
    assert len(sanitized) <= 10003
    assert sanitized.endswith("...")

def test_sanitize_username():
    username = "user@name!123"
    sanitized = sanitize_username(username)
    assert sanitized == "username123"
    
    long_username = "a" * 60
    sanitized = sanitize_username(long_username)
    assert len(sanitized) <= 50
    
    assert sanitize_username("") == ""
    assert sanitize_username(None) == ""

def test_sanitize_email():
    email = "test@example.com"
    sanitized = sanitize_email(email)
    assert sanitized == "test@example.com"
    
    invalid_email = "invalid-email"
    sanitized = sanitize_email(invalid_email)
    assert sanitized == ""
    
    email_with_spaces = "  TEST@EXAMPLE.COM  "
    sanitized = sanitize_email(email_with_spaces)
    assert sanitized == "test@example.com"

def test_validate_content_length():
    content = "a" * 1000
    assert validate_content_length(content, max_length=10000) == True
    
    long_content = "a" * 10001
    assert validate_content_length(long_content, max_length=10000) == False
    
    assert validate_content_length("", max_length=10000) == True

def test_html_escaping():
    content = "<script>alert('xss')</script>"
    sanitized = sanitize_html_content(content)
    
    assert "" in sanitized

def test_dangerous_tags_removal():
    dangerous_content = """
    <script>alert('xss')</script>
    <iframe src="malicious.com"></iframe>
    <object data="bad.com"></object>
    <form action="evil.com"></form>
    <p>Safe content</p>
    """
    sanitized = sanitize_html_content(dangerous_content)
    
    assert "<script>" not in sanitized
    assert "<iframe>" not in sanitized
    assert "<object>" not in sanitized
    assert "<form>" not in sanitized
    
    assert "<p>Safe content</p>" in sanitized 