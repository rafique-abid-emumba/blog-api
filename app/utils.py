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
    Extracts the first JSON object or array from a string.
    """
    pattern = r"\[.*?\]" if expect_array else r"\{.*?\}"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        logging.error("No valid JSON %s found in LLM response", "array" if expect_array else "object")
        raise ValueError("No valid JSON found in LLM response")
    return json.loads(match.group(0))

from app.genai.llm import get_llm

def _llm_complete(prompt: str) -> str:
    """
    Calls the LLM with the given prompt and returns the response text.
    """
    llm = get_llm()
    response = llm.complete(prompt=prompt)
    return response.text.strip() 