import pytest
from unittest.mock import patch
from datetime import datetime
from app.services.cache_service import PostCacheService
from app.schemas.post import PostFilters, PaginatedResponse, PostStatus

class TestPostCacheService:
    
    def test_generate_filters_hash_basic(self):
        filters = PostFilters(
            status=PostStatus.published,
            search="test",
            tags=["python", "fastapi"]
        )
        
        hash_result = PostCacheService._generate_filters_hash(filters, "Admin")
        
        assert isinstance(hash_result, str)
        assert len(hash_result) == 12
    
    def test_generate_filters_hash_with_all_fields(self):
        filters = PostFilters(
            status=PostStatus.published,
            author_id=123,
            search="test search",
            tags=["python", "fastapi"],
            created_after=datetime(2023, 1, 1),
            created_before=datetime(2023, 12, 31)
        )
        
        hash_result = PostCacheService._generate_filters_hash(filters, "Author", author_id=456)
        
        assert isinstance(hash_result, str)
        assert len(hash_result) == 12
    
    def test_generate_filters_hash_different_roles(self):
        filters = PostFilters(search="test")
        
        hash_admin = PostCacheService._generate_filters_hash(filters, "Admin")
        hash_author = PostCacheService._generate_filters_hash(filters, "Author")
        hash_reader = PostCacheService._generate_filters_hash(filters, "Reader")
        
        assert hash_admin != hash_author
        assert hash_admin != hash_reader
        assert hash_author != hash_reader
    
    def test_generate_filters_hash_with_author_id_override(self):
        filters = PostFilters(author_id=123)
        
        hash_with_override = PostCacheService._generate_filters_hash(filters, "Author", author_id=456)
        hash_without_override = PostCacheService._generate_filters_hash(filters, "Author")
        
        assert hash_with_override != hash_without_override
    
    def test_generate_cache_key_admin(self):
        filters_hash = "abc123def456"
        cache_key = PostCacheService._generate_cache_key("Admin", filters_hash, 1, 10)
        
        assert cache_key == f"{PostCacheService.CACHE_PREFIX}:Admin:{filters_hash}:1:10"
    
    def test_generate_cache_key_author_with_author_id(self):
        filters_hash = "abc123def456"
        cache_key = PostCacheService._generate_cache_key("Author", filters_hash, 2, 20, author_id=123)
        
        assert cache_key == f"{PostCacheService.CACHE_PREFIX}:Author:123:{filters_hash}:2:20"
    
    def test_generate_cache_key_author_without_author_id(self):
        filters_hash = "abc123def456"
        cache_key = PostCacheService._generate_cache_key("Author", filters_hash, 1, 10)
        
        assert cache_key == f"{PostCacheService.CACHE_PREFIX}:Author:{filters_hash}:1:10"
    
    @pytest.mark.asyncio
    @patch('app.services.cache_service.redis_client')
    async def test_get_cached_posts_cache_hit(self, mock_redis):
        filters = PostFilters(search="test")
        mock_response = PaginatedResponse(
            items=[],
            total=0,
            page=1,
            size=10,
            pages=0
        )
        
        mock_redis.get.return_value = mock_response.model_dump_json()
        
        result = await PostCacheService.get_cached_posts("Admin", filters, 1, 10)
        
        assert result is not None
        assert isinstance(result, PaginatedResponse)
        mock_redis.get.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.services.cache_service.redis_client')
    async def test_get_cached_posts_cache_miss(self, mock_redis):
        filters = PostFilters(search="test")
        mock_redis.get.return_value = None
        
        result = await PostCacheService.get_cached_posts("Admin", filters, 1, 10)
        
        assert result is None
        mock_redis.get.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.services.cache_service.redis_client')
    async def test_get_cached_posts_exception(self, mock_redis):
        filters = PostFilters(search="test")
        mock_redis.get.side_effect = Exception("Redis error")
        
        result = await PostCacheService.get_cached_posts("Admin", filters, 1, 10)
        
        assert result is None
    
    @pytest.mark.asyncio
    @patch('app.services.cache_service.redis_client')
    async def test_cache_posts_success(self, mock_redis):
        filters = PostFilters(search="test")
        posts_response = PaginatedResponse(
            items=[],
            total=0,
            page=1,
            size=10,
            pages=0
        )
        
        await PostCacheService.cache_posts(posts_response, "Admin", filters, 1, 10)
        
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert len(call_args[0]) == 3
        assert call_args[0][1] == PostCacheService.CACHE_TTL
        assert call_args[0][2] == posts_response.model_dump_json()
    
    @pytest.mark.asyncio
    @patch('app.services.cache_service.redis_client')
    async def test_cache_posts_with_author_id(self, mock_redis):
        filters = PostFilters(search="test")
        posts_response = PaginatedResponse(
            items=[],
            total=0,
            page=1,
            size=10,
            pages=0
        )
        
        await PostCacheService.cache_posts(posts_response, "Author", filters, 1, 10, author_id=123)
        
        mock_redis.setex.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.services.cache_service.redis_client')
    async def test_cache_posts_exception(self, mock_redis):
        filters = PostFilters(search="test")
        posts_response = PaginatedResponse(
            items=[],
            total=0,
            page=1,
            size=10,
            pages=0
        )
        mock_redis.setex.side_effect = Exception("Redis error")
        
        await PostCacheService.cache_posts(posts_response, "Admin", filters, 1, 10)
    
    @pytest.mark.asyncio
    @patch('app.services.cache_service.redis_client')
    async def test_invalidate_user_posts_success(self, mock_redis):
        mock_redis.keys.return_value = ["post:Author:123:abc:1:10", "post:Author:123:def:2:20"]
        mock_redis.delete.return_value = 2
        
        await PostCacheService.invalidate_user_posts(123)
        
        mock_redis.keys.assert_called_once_with(f"{PostCacheService.CACHE_PREFIX}:*:123:*")
        mock_redis.delete.assert_called_once_with("post:Author:123:abc:1:10", "post:Author:123:def:2:20")
    
    @pytest.mark.asyncio
    @patch('app.services.cache_service.redis_client')
    async def test_invalidate_user_posts_no_keys(self, mock_redis):
        mock_redis.keys.return_value = []
        
        await PostCacheService.invalidate_user_posts(123)
        
        mock_redis.keys.assert_called_once_with(f"{PostCacheService.CACHE_PREFIX}:*:123:*")
        mock_redis.delete.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('app.services.cache_service.redis_client')
    async def test_invalidate_user_posts_exception(self, mock_redis):
        mock_redis.keys.side_effect = Exception("Redis error")
        
        await PostCacheService.invalidate_user_posts(123)
    
    @pytest.mark.asyncio
    @patch('app.services.cache_service.redis_client')
    async def test_invalidate_all_posts_success(self, mock_redis):
        mock_redis.keys.return_value = ["post:Admin:abc:1:10", "post:Author:123:def:2:20"]
        mock_redis.delete.return_value = 2
        
        await PostCacheService.invalidate_all_posts()
        
        mock_redis.keys.assert_called_once_with(f"{PostCacheService.CACHE_PREFIX}:*")
        mock_redis.delete.assert_called_once_with("post:Admin:abc:1:10", "post:Author:123:def:2:20")
    
    @pytest.mark.asyncio
    @patch('app.services.cache_service.redis_client')
    async def test_invalidate_all_posts_no_keys(self, mock_redis):
        mock_redis.keys.return_value = []
        
        await PostCacheService.invalidate_all_posts()
        
        mock_redis.keys.assert_called_once_with(f"{PostCacheService.CACHE_PREFIX}:*")
        mock_redis.delete.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('app.services.cache_service.redis_client')
    async def test_invalidate_all_posts_exception(self, mock_redis):
        mock_redis.keys.side_effect = Exception("Redis error")
        
        await PostCacheService.invalidate_all_posts()
    
    def test_generate_filters_hash_edge_cases(self):
        filters = PostFilters()
        hash_result = PostCacheService._generate_filters_hash(filters, "Admin")
        assert isinstance(hash_result, str)
        
        filters = PostFilters(tags=[])
        hash_result = PostCacheService._generate_filters_hash(filters, "Admin")
        assert isinstance(hash_result, str)
        
        filters = PostFilters(author_id=None)
        hash_result = PostCacheService._generate_filters_hash(filters, "Admin", author_id=None)
        assert isinstance(hash_result, str)
    
    def test_generate_cache_key_edge_cases(self):
        filters_hash = "abc123def456"
        
        cache_key = PostCacheService._generate_cache_key("Author", filters_hash, 1, 10, author_id=None)
        assert cache_key == f"{PostCacheService.CACHE_PREFIX}:Author:{filters_hash}:1:10"
        
        cache_key = PostCacheService._generate_cache_key("Admin", filters_hash, 0, 0)
        assert cache_key == f"{PostCacheService.CACHE_PREFIX}:Admin:{filters_hash}:0:0" 