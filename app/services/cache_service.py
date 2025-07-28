import hashlib
import json
from typing import Optional
from app.core.redis import redis_client
from app.schemas.post import PostFilters, PaginatedResponse
from app.utils.constants import POST_CACHE_TTL, POST_CACHE_PREFIX
import logging

logger = logging.getLogger(__name__)

class PostCacheService:
    CACHE_TTL = POST_CACHE_TTL
    CACHE_PREFIX = POST_CACHE_PREFIX
    
    @staticmethod
    def _generate_filters_hash(filters: PostFilters, user_role: str, author_id: Optional[int] = None) -> str:
        filter_dict = {
            "status": filters.status.value if filters.status else None,
            "author_id": author_id or filters.author_id,
            "tags": sorted(filters.tags) if filters.tags else None,
            "created_after": filters.created_after.isoformat() if filters.created_after else None,
            "created_before": filters.created_before.isoformat() if filters.created_before else None,
            "search": filters.search,
            "role": user_role
        }
        filter_str = json.dumps(filter_dict, sort_keys=True)
        return hashlib.md5(filter_str.encode()).hexdigest()[:12]
    
    @staticmethod
    def _generate_cache_key(user_role: str, filters_hash: str, page: int, size: int, author_id: Optional[int] = None) -> str:
        if user_role == "Author" and author_id:
            return f"{PostCacheService.CACHE_PREFIX}:{user_role}:{author_id}:{filters_hash}:{page}:{size}"
        return f"{PostCacheService.CACHE_PREFIX}:{user_role}:{filters_hash}:{page}:{size}"
    
    @staticmethod
    async def get_cached_posts(
        user_role: str, 
        filters: PostFilters, 
        page: int, 
        size: int, 
        author_id: Optional[int] = None
    ) -> Optional[PaginatedResponse]:
        try:
            filters_hash = PostCacheService._generate_filters_hash(filters, user_role, author_id)
            cache_key = PostCacheService._generate_cache_key(user_role, filters_hash, page, size, author_id)
            
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit for posts: {cache_key}")
                return PaginatedResponse.model_validate_json(cached_data)
            
            logger.info(f"Cache miss for posts: {cache_key}")
            return None
        except Exception as e:
            logger.warning(f"Failed to get cached posts: {e}")
            return None
    
    @staticmethod
    async def cache_posts(
        posts_response: PaginatedResponse,
        user_role: str, 
        filters: PostFilters, 
        page: int, 
        size: int, 
        author_id: Optional[int] = None
    ) -> None:
        try:
            filters_hash = PostCacheService._generate_filters_hash(filters, user_role, author_id)
            cache_key = PostCacheService._generate_cache_key(user_role, filters_hash, page, size, author_id)
            
            await redis_client.setex(
                cache_key,
                PostCacheService.CACHE_TTL,
                posts_response.model_dump_json()
            )
            logger.info(f"Cached posts: {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to cache posts: {e}")
    
    @staticmethod
    async def invalidate_user_posts(user_id: int) -> None:
        try:
            pattern = f"{PostCacheService.CACHE_PREFIX}:*:{user_id}:*"
            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cached posts for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate user posts: {e}")
    
    @staticmethod
    async def invalidate_all_posts() -> None:
        try:
            pattern = f"{PostCacheService.CACHE_PREFIX}:*"
            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cached posts")
        except Exception as e:
            logger.warning(f"Failed to invalidate all posts: {e}") 