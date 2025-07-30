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

# Cache constants
POST_CACHE_TTL = 300  # 5 minutes
POST_CACHE_PREFIX = "posts"

# Evaluation test cases
QA_TEST_CASES = [
    {
        "question": "What is FastAPI?",
        "context": "FastAPI is a modern web framework for building APIs with Python. It provides automatic API documentation and is built on top of Starlette.",
        "expected_answer": "FastAPI is a modern web framework for building APIs with Python that provides automatic API documentation."
    },
    {
        "question": "How does Redis work?",
        "context": "Redis is an in-memory data structure store that can be used as a database, cache, and message broker. It supports various data structures.",
        "expected_answer": "Redis is an in-memory data structure store that can be used as a database, cache, and message broker."
    }
]

GLOBAL_QA_TEST_CASES = [
    {
        "question": "What are the main features of modern web frameworks?",
        "context": "Modern web frameworks like FastAPI, Django, and Flask provide features such as automatic API documentation, request validation, and database integration. They help developers build scalable web applications quickly.",
        "expected_answer": "Modern web frameworks provide features like automatic API documentation, request validation, and database integration to help build scalable web applications."
    },
    {
        "question": "How do vector databases work?",
        "context": "Vector databases store and retrieve high-dimensional vectors efficiently. They use similarity search algorithms to find the most relevant vectors for a given query, making them ideal for AI applications.",
        "expected_answer": "Vector databases store high-dimensional vectors and use similarity search algorithms to find relevant vectors for queries, making them ideal for AI applications."
    }
]

SUMMARIZATION_TEST_CASES = [
    {
        "content": "Docker is a platform for developing, shipping, and running applications in containers. Containers are lightweight and include everything needed to run the application.",
        "expected_summary": "Docker is a platform for containerizing applications, making them lightweight and portable."
    },
    {
        "content": "Python is a high-level programming language known for its simplicity and readability. It's widely used in web development, data science, and AI.",
        "expected_summary": "Python is a high-level programming language valued for simplicity and used in web development, data science, and AI."
    }
] 