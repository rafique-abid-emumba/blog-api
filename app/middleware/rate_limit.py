from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.rate_limiter import get_rate_limiter
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        excluded_paths = ["/health/", "/docs", "/redoc", "/openapi.json"]
        if request.url.path in excluded_paths:
            return await call_next(request)
        
        try:
            rate_limiter = get_rate_limiter()
            
            rate_limit_info = await rate_limiter.check_rate_limit(request)
            
            response = await call_next(request)
            
            response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_limit_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_limit_info["reset"])
            response.headers["X-RateLimit-Window"] = str(rate_limit_info["window"])
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting middleware error: {e}")
            return await call_next(request) 