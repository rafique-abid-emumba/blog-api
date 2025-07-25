from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.user import router as user_router
from app.api.post import router as post_router
from app.api.comment import router as comment_router
from app.api.genai import router as genai_router
from app.api.health import router as health_router
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from sqlalchemy.exc import OperationalError
from sqlalchemy import text
from app.db.session import engine
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful.")
    except OperationalError as e:
        logger.critical(f"Database connection failed: {e}")
        raise RuntimeError("Database connection failed. Check logs for details.")
    
    yield
    
    logger.info("Application shutting down.")

app = FastAPI(lifespan=lifespan)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

app.include_router(health_router)
app.include_router(user_router)
app.include_router(post_router)
app.include_router(comment_router)
app.include_router(genai_router)
