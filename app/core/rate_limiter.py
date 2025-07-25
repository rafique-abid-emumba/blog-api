import time
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.default_limit = 100
        self.default_window = 60
        
        self.endpoint_limits: Dict[str, Dict[str, Any]] = {
            "/users/login": {"limit": 5, "window": 300},
            "/users/register": {"limit": 3, "window": 3600},
            "/posts/": {"limit": 50, "window": 60},
            "/posts/quick-post": {"limit": 10, "window": 300},
            "/comments/": {"limit": 20, "window": 60},
            "/genai/": {"limit": 30, "window": 60},
            "/health/redis": {"limit": 10, "window": 60},
            "/health/database": {"limit": 5, "window": 60},
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host
    
    def _get_user_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting"""
        client_ip = self._get_client_ip(request)
        
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}:{client_ip}"
        
        return f"ip:{client_ip}"
    
    def _get_endpoint_key(self, path: str) -> str:
        """Get the rate limit configuration for an endpoint"""
        for endpoint, config in self.endpoint_limits.items():
            if path.startswith(endpoint):
                return endpoint
        return "default"
    
    async def _get_rate_limit_config(self, path: str) -> Dict[str, Any]:
        """Get rate limit configuration for the endpoint"""
        endpoint_key = self._get_endpoint_key(path)
        return self.endpoint_limits.get(endpoint_key, {
            "limit": self.default_limit,
            "window": self.default_window
        })
    
    async def _check_rate_limit(self, identifier: str, path: str) -> Dict[str, Any]:
        """Check if request is within rate limits"""
        config = await self._get_rate_limit_config(path)
        limit = config["limit"]
        window = config["window"]
        
        key = f"rate_limit:{identifier}:{path}"
        current_time = int(time.time())
        
        try:
            pipe = self.redis.pipeline()
            
            pipe.zremrangebyscore(key, 0, current_time - window)
            
            pipe.zcard(key)
            
            pipe.zadd(key, {str(current_time): current_time})
            
            pipe.expire(key, window)
            
            results = await pipe.execute()
            current_count = results[1]
            
            remaining = max(0, limit - current_count)
            reset_time = current_time + window
            
            return {
                "limit": limit,
                "remaining": remaining,
                "reset": reset_time,
                "window": window,
                "exceeded": current_count >= limit
            }
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            return {
                "limit": limit,
                "remaining": limit,
                "reset": current_time + window,
                "window": window,
                "exceeded": False
            }
    
    async def check_rate_limit(self, request: Request) -> Dict[str, Any]:
        """Main method to check rate limits"""
        identifier = self._get_user_identifier(request)
        path = request.url.path
        
        rate_limit_info = await self._check_rate_limit(identifier, path)
        
        if rate_limit_info["exceeded"]:
            logger.warning(f"Rate limit exceeded for {identifier} on {path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": rate_limit_info["limit"],
                    "window": rate_limit_info["window"],
                    "reset": rate_limit_info["reset"]
                }
            )
        
        return rate_limit_info

rate_limiter: Optional[RateLimiter] = None

def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance"""
    global rate_limiter
    if rate_limiter is None:
        from app.core.redis import redis_client
        rate_limiter = RateLimiter(redis_client)
    return rate_limiter 