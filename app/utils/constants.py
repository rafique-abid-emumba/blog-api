# Centralized application constants

# Comment limits
MAX_COMMENTS_PER_USER_PER_POST = 10
MAX_COMMENTS_PER_POST = 100
MAX_COMMENT_DEPTH = 3

# User roles
default_roles = ["Admin", "Author", "Reader"]
DEFAULT_ROLE = "Reader"

# Password policy
PASSWORD_REGEX = r'^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\\\-={{}}\[\]:\";\'<>?,./]).{8,}$'
PASSWORD_REQUIREMENTS_MSG = (
    "Password must be at least 8 characters long, "
    "contain at least 1 uppercase letter, 1 number, and 1 special character."
)

# JWT Token
ENCODING_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7 

#Embedding constants
CHUNK_SIZE = 200 