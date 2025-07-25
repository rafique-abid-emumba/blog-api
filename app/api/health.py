from fastapi import APIRouter
from app.core.redis import redis_client
from app.db.session import SessionLocal
from sqlalchemy import text

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Blog API is running"
    }

@router.get("/redis")
async def redis_health_check():
    """Check Redis connection"""
    try:
        await redis_client.ping()
        return {
            "status": "healthy",
            "service": "redis",
            "message": "Redis connection is working"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "redis",
            "error": str(e)
        }

@router.get("/database")
async def database_health_check():
    """Check database connection"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {
            "status": "healthy",
            "service": "database",
            "message": "Database connection is working"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "database",
            "error": str(e)
        } 