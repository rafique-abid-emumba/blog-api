import re
from passlib.context import CryptContext
from app.constants import PASSWORD_REGEX
import logging

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def is_strong_password(password: str) -> bool:
    pattern = PASSWORD_REGEX
    return bool(re.match(pattern, password))

def get_comment_depth(comment):
    depth = 1
    while comment.parent is not None:
        depth += 1
        comment = comment.parent
    return depth

def validate_content_input(content: str, min_length: int = 10, max_length: int = 5000) -> tuple[bool, str]:
    if not content or not content.strip():
        return False, "Content cannot be empty"
    
    content = content.strip()
    
    if len(content) < min_length:
        return False, f"Content must be at least {min_length} characters long"
    
    if len(content) > max_length:
        return False, f"Content cannot exceed {max_length} characters"
    
    if content.isdigit():
        return False, "Content cannot be only numbers"
    
    if not any(c.isalpha() for c in content):
        return False, "Content must contain at least some text"
    
    if len(set(content)) <= 2 and len(content) > 5:
        return False, "Content appears to be repetitive or meaningless"
    
    return True, "" 