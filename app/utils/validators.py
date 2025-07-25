from functools import wraps
from fastapi import HTTPException
from app.utils.sanitizer import validate_content_length

def validate_input(max_length: int = 10000):
    """Decorator to validate input content length"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            content = kwargs.get('content') or kwargs.get('post_in', {}).get('content', '')
            
            if not validate_content_length(content, max_length):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Content too long. Maximum {max_length} characters allowed."
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator 