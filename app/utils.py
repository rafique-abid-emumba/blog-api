import re
from passlib.context import CryptContext
from app.constants import PASSWORD_REGEX

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