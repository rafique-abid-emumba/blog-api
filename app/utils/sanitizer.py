import re
import html

def sanitize_html_content(content: str, max_length: int = 10000) -> str:
    if not content:
        return ""
    
    dangerous_tags = ['script', 'iframe', 'object', 'embed', 'form', 'input', 'button']
    for tag in dangerous_tags:
        content = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(f'<{tag}[^>]*>', '', content, flags=re.IGNORECASE)
    
    allowed_tags = ['p', 'br', 'strong', 'b', 'em', 'i', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'blockquote', 'code', 'pre']
    
    temp_replacements = {}
    for i, tag in enumerate(allowed_tags):
        opening_placeholder = f"__OPEN_TAG_{i}__"
        temp_replacements[opening_placeholder] = f"<{tag}>"
        content = re.sub(f'<{tag}[^>]*>', opening_placeholder, content, flags=re.IGNORECASE)
        
        closing_placeholder = f"__CLOSE_TAG_{i}__"
        temp_replacements[closing_placeholder] = f"</{tag}>"
        content = re.sub(f'</{tag}>', closing_placeholder, content, flags=re.IGNORECASE)
    
    content = html.escape(content)
    
    for placeholder, tag in temp_replacements.items():
        content = content.replace(placeholder, tag)
    
    if len(content) > max_length:
        content = content[:max_length] + "..."
    
    return content

def sanitize_username(username: str) -> str:
    if not username:
        return ""
    
    username = re.sub(r'[^a-zA-Z0-9_]', '', username)
    return username[:50]

def sanitize_email(email: str) -> str:
    if not email:
        return ""
    
    email = email.strip()
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(email_pattern, email):
        return email.lower()
    return ""

def validate_content_length(content: str, max_length: int = 10000) -> bool:
    return len(content) <= max_length 