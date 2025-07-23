import re
from passlib.context import CryptContext
from app.constants import PASSWORD_REGEX
import logging
import json

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

def _extract_json_from_text(text: str, expect_array: bool = False) -> any:
    """
    Extracts JSON object or array from a string with improved error handling.
    """
    text = text.strip()
    
    lines = text.split('\n')
    for line in reversed(lines):
        line = line.strip()
        if line:
            try:
                if expect_array and line.startswith('[') and line.endswith(']'):
                    return json.loads(line)
                elif not expect_array and line.startswith('{') and line.endswith('}'):
                    return json.loads(line)
            except json.JSONDecodeError:
                continue
    
    pattern = r"\[.*?\]" if expect_array else r"\{.*?\}"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    
    logging.error("No valid JSON %s found in LLM response: %s", 
                 "array" if expect_array else "object", text[:200])
    raise ValueError("No valid JSON found in LLM response")

from app.genai.llm import get_llm

def _llm_complete(prompt: str) -> str:
    """
    Calls the LLM with the given prompt and returns the response text.
    """
    llm = get_llm()
    response = llm.complete(prompt=prompt)
    return response.text.strip()

def validate_content_input(content: str, min_length: int = 10, max_length: int = 5000) -> tuple[bool, str]:
    """
    Validates content input for GenAI endpoints.
    Returns (is_valid, error_message).
    """
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