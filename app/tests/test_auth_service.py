import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from app.services.auth_service import issue_tokens, blacklist_refresh_token_with_payload, refresh_user_token


class TestAuthService:
    
    @patch('app.services.auth_service.create_access_token')
    @patch('app.services.auth_service.create_refresh_token')
    def test_issue_tokens_success(self, mock_create_refresh, mock_create_access):
        mock_create_access.return_value = "access_token_123"
        mock_create_refresh.return_value = "refresh_token_456"
        
        result = issue_tokens("user123", "Admin")
        
        assert result["access_token"] == "access_token_123"
        assert result["refresh_token"] == "refresh_token_456"
        assert result["token_type"] == "bearer"
        
        mock_create_access.assert_called_once()
        mock_create_refresh.assert_called_once()
    
    @patch('app.services.auth_service.blacklist_token')
    @patch('app.services.auth_service.time')
    def test_blacklist_refresh_token_with_payload_success(self, mock_time, mock_blacklist):
        mock_time.time.return_value = 1000
        payload = {"exp": 1100, "sub": "user123", "role": "Admin"}
        
        blacklist_refresh_token_with_payload("refresh_token_123", payload, "user123")
        
        mock_blacklist.assert_called_once_with("refresh_token_123", 100)
    
    @patch('app.services.auth_service.blacklist_token')
    @patch('app.services.auth_service.time')
    def test_blacklist_refresh_token_with_payload_no_exp(self, mock_time, mock_blacklist):
        mock_time.time.return_value = 1000
        payload = {"sub": "user123", "role": "Admin"}
        
        blacklist_refresh_token_with_payload("refresh_token_123", payload, "user123")
        
        mock_blacklist.assert_not_called()
    
    @patch('app.services.auth_service.blacklist_token')
    @patch('app.services.auth_service.time')
    def test_blacklist_refresh_token_with_payload_expired(self, mock_time, mock_blacklist):
        mock_time.time.return_value = 1200
        payload = {"exp": 1100, "sub": "user123", "role": "Admin"}
        
        blacklist_refresh_token_with_payload("refresh_token_123", payload, "user123")
        
        mock_blacklist.assert_called_once_with("refresh_token_123", 0)
    
    @patch('app.services.auth_service.blacklist_token')
    @patch('app.services.auth_service.time')
    def test_blacklist_refresh_token_with_payload_exception(self, mock_time, mock_blacklist):
        mock_time.time.return_value = 1000
        mock_blacklist.side_effect = Exception("Redis error")
        payload = {"exp": 1100, "sub": "user123", "role": "Admin"}
        
        blacklist_refresh_token_with_payload("refresh_token_123", payload, "user123")
    
    @patch('app.services.auth_service.is_token_blacklisted')
    @patch('app.services.auth_service.verify_refresh_token')
    @patch('app.services.auth_service.issue_tokens')
    @patch('app.services.auth_service.blacklist_refresh_token_with_payload')
    def test_refresh_user_token_success(self, mock_blacklist, mock_issue, mock_verify, mock_is_blacklisted):
        mock_is_blacklisted.return_value = False
        mock_verify.return_value = {"sub": "user123", "role": "Admin", "exp": 1100}
        mock_issue.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "token_type": "bearer"
        }
        
        result = refresh_user_token("refresh_token_123")
        
        assert result["access_token"] == "new_access_token"
        assert result["refresh_token"] == "new_refresh_token"
        assert result["token_type"] == "bearer"
        
        mock_is_blacklisted.assert_called_once_with("refresh_token_123")
        mock_verify.assert_called_once_with("refresh_token_123")
        mock_issue.assert_called_once_with("user123", "Admin")
        mock_blacklist.assert_called_once_with("refresh_token_123", {"sub": "user123", "role": "Admin", "exp": 1100}, "user123")
    
    @patch('app.services.auth_service.is_token_blacklisted')
    def test_refresh_user_token_blacklisted(self, mock_is_blacklisted):
        mock_is_blacklisted.return_value = True
        
        with pytest.raises(HTTPException) as exc_info:
            refresh_user_token("refresh_token_123")
        
        assert exc_info.value.status_code == 401
        assert "Refresh token has been revoked" in str(exc_info.value.detail)
    
    @patch('app.services.auth_service.is_token_blacklisted')
    @patch('app.services.auth_service.verify_refresh_token')
    def test_refresh_user_token_invalid_token(self, mock_verify, mock_is_blacklisted):
        mock_is_blacklisted.return_value = False
        mock_verify.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            refresh_user_token("refresh_token_123")
        
        assert exc_info.value.status_code == 401
        assert "Invalid refresh token" in str(exc_info.value.detail)
    
    @patch('app.services.auth_service.is_token_blacklisted')
    @patch('app.services.auth_service.verify_refresh_token')
    def test_refresh_user_token_missing_sub(self, mock_verify, mock_is_blacklisted):
        mock_is_blacklisted.return_value = False
        mock_verify.return_value = {"role": "Admin", "exp": 1100}
        
        with pytest.raises(HTTPException) as exc_info:
            refresh_user_token("refresh_token_123")
        
        assert exc_info.value.status_code == 400
        assert "Invalid token payload" in str(exc_info.value.detail)
    
    @patch('app.services.auth_service.is_token_blacklisted')
    @patch('app.services.auth_service.verify_refresh_token')
    def test_refresh_user_token_missing_role(self, mock_verify, mock_is_blacklisted):
        mock_is_blacklisted.return_value = False
        mock_verify.return_value = {"sub": "user123", "exp": 1100}
        
        with pytest.raises(HTTPException) as exc_info:
            refresh_user_token("refresh_token_123")
        
        assert exc_info.value.status_code == 400
        assert "Invalid token payload" in str(exc_info.value.detail)
    
    @patch('app.services.auth_service.is_token_blacklisted')
    @patch('app.services.auth_service.verify_refresh_token')
    def test_refresh_user_token_unexpected_exception(self, mock_verify, mock_is_blacklisted):
        mock_is_blacklisted.return_value = False
        mock_verify.side_effect = Exception("Unexpected error")
        
        with pytest.raises(HTTPException) as exc_info:
            refresh_user_token("refresh_token_123")
        
        assert exc_info.value.status_code == 500
        assert "Failed to refresh token" in str(exc_info.value.detail)
    
    @patch('app.services.auth_service.create_access_token')
    @patch('app.services.auth_service.create_refresh_token')
    def test_issue_tokens_with_different_roles(self, mock_create_refresh, mock_create_access):
        mock_create_access.return_value = "access_token_123"
        mock_create_refresh.return_value = "refresh_token_456"
        
        roles = ["Admin", "Author", "Reader"]
        for role in roles:
            result = issue_tokens("user123", role)
            assert result["token_type"] == "bearer"
            assert "access_token" in result
            assert "refresh_token" in result
    
    @patch('app.services.auth_service.create_access_token')
    @patch('app.services.auth_service.create_refresh_token')
    def test_issue_tokens_with_different_user_ids(self, mock_create_refresh, mock_create_access):
        mock_create_access.return_value = "access_token_123"
        mock_create_refresh.return_value = "refresh_token_456"
        
        user_ids = ["user1", "user2", "admin123", "author456"]
        for user_id in user_ids:
            result = issue_tokens(user_id, "Admin")
            assert result["token_type"] == "bearer"
            assert "access_token" in result
            assert "refresh_token" in result 