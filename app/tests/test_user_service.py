import pytest
from fastapi import HTTPException
from app.services.user_service import (
    create_user, authenticate_user, update_user, 
    is_duplicate_username, is_duplicate_email, is_strong_password,
    get_user, get_user_by_username
)
from app.schemas.user import UserCreate, UserUpdate

class TestUserService:
    
    def test_create_user_success(self, db_session, add_roles_to_db):
        user_data = UserCreate(
            username="newuser",
            email="new@example.com",
            password="StrongPass123!"
        )
        user = create_user(db_session, user_data)
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.role_id == 3
    
    def test_create_user_duplicate_username(self, db_session, add_roles_to_db):
        user_data1 = UserCreate(
            username="testuser",
            email="test1@example.com",
            password="StrongPass123!"
        )
        create_user(db_session, user_data1)
        
        user_data2 = UserCreate(
            username="testuser",
            email="test2@example.com",
            password="StrongPass123!"
        )
        with pytest.raises(HTTPException) as exc_info:
            create_user(db_session, user_data2)
        assert exc_info.value.status_code == 400
        assert "Username already registered" in exc_info.value.detail
    
    def test_create_user_duplicate_email(self, db_session, add_roles_to_db):
        user_data1 = UserCreate(
            username="user1",
            email="test@example.com",
            password="StrongPass123!"
        )
        create_user(db_session, user_data1)
        
        user_data2 = UserCreate(
            username="user2",
            email="test@example.com",
            password="StrongPass123!"
        )
        with pytest.raises(HTTPException) as exc_info:
            create_user(db_session, user_data2)
        assert exc_info.value.status_code == 400
        assert "Email already registered" in exc_info.value.detail
    
    def test_create_user_weak_password(self, db_session):
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="weak"
        )
        with pytest.raises(HTTPException) as exc_info:
            create_user(db_session, user_data)
        assert exc_info.value.status_code == 400
        assert "Password must be at least 8 characters" in exc_info.value.detail
    
    def test_authenticate_user_success(self, db_session, test_user):
        user = authenticate_user(db_session, "testuser", "TestPass123!")
        assert user is not None
        assert user.username == "testuser"
    
    def test_authenticate_user_wrong_password(self, db_session, test_user):
        with pytest.raises(HTTPException) as exc_info:
            authenticate_user(db_session, "testuser", "wrongpassword")
        assert exc_info.value.status_code == 401
        assert "Invalid credentials" in exc_info.value.detail
    
    def test_authenticate_user_nonexistent_user(self, db_session):
        with pytest.raises(HTTPException) as exc_info:
            authenticate_user(db_session, "nonexistent", "password")
        assert exc_info.value.status_code == 404
        assert "User not found" in exc_info.value.detail
    
    def test_update_user_success(self, db_session, test_user):
        update_data = UserUpdate(username="updateduser")
        updated_user = update_user(db_session, test_user, update_data)
        assert updated_user.username == "updateduser"
    
    def test_update_user_not_found(self, db_session):
        update_data = UserUpdate(username="updateduser")
        with pytest.raises(HTTPException) as exc_info:
            update_user(db_session, None, update_data)
        assert exc_info.value.status_code == 500
        assert "Failed to update user" in exc_info.value.detail
    
    def test_is_strong_password_valid(self):
        assert is_strong_password("StrongPass123!") == True
        assert is_strong_password("Another1@") == True
    
    def test_is_strong_password_invalid(self):
        assert is_strong_password("weak") == False
        assert is_strong_password("nouppercase123!") == False
        assert is_strong_password("NoNumbers!") == False
        assert is_strong_password("NoSpecial123") == False
    
    def test_is_duplicate_username_true(self, db_session, test_user):
        assert is_duplicate_username(db_session, "testuser") == True
    
    def test_is_duplicate_username_false(self, db_session):
        assert is_duplicate_username(db_session, "nonexistent") == False
    
    def test_is_duplicate_email_true(self, db_session, test_user):
        assert is_duplicate_email(db_session, "test@example.com") == True
    
    def test_is_duplicate_email_false(self, db_session):
        assert is_duplicate_email(db_session, "nonexistent@example.com") == False

    def test_get_user_success(self, db_session, test_user):
        user = get_user(db_session, test_user.id)
        assert user is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_get_user_not_found(self, db_session):
        with pytest.raises(HTTPException) as exc_info:
            get_user(db_session, 999)
        assert exc_info.value.status_code == 404
        assert "User not found" in exc_info.value.detail

    def test_get_user_by_username_success(self, db_session, test_user):
        user = get_user_by_username(db_session, "testuser")
        assert user is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_get_user_by_username_not_found(self, db_session):
        with pytest.raises(HTTPException) as exc_info:
            get_user_by_username(db_session, "nonexistent")
        assert exc_info.value.status_code == 404
        assert "User not found" in exc_info.value.detail

    def test_update_user_with_duplicate_username(self, db_session, test_user):
        user_data = UserCreate(
            username="anotheruser",
            email="another@example.com",
            password="StrongPass123!"
        )
        another_user = create_user(db_session, user_data)
        
        update_data = UserUpdate(username="anotheruser")
        with pytest.raises(HTTPException) as exc_info:
            update_user(db_session, test_user, update_data)
        assert exc_info.value.status_code == 400
        assert "Username already taken" in exc_info.value.detail

    def test_update_user_with_duplicate_email(self, db_session, test_user):
        user_data = UserCreate(
            username="anotheruser",
            email="another@example.com",
            password="StrongPass123!"
        )
        another_user = create_user(db_session, user_data)
        
        update_data = UserUpdate(email="another@example.com")
        with pytest.raises(HTTPException) as exc_info:
            update_user(db_session, test_user, update_data)
        assert exc_info.value.status_code == 400
        assert "Email already taken" in exc_info.value.detail

    def test_update_user_with_weak_password(self, db_session, test_user):
        update_data = UserUpdate(password="weak")
        with pytest.raises(HTTPException) as exc_info:
            update_user(db_session, test_user, update_data)
        assert exc_info.value.status_code == 400
        assert "Password must be at least 8 characters" in exc_info.value.detail

    def test_update_user_with_same_username(self, db_session, test_user):
        update_data = UserUpdate(username="testuser")
        updated_user = update_user(db_session, test_user, update_data)
        assert updated_user.username == "testuser"

    def test_update_user_with_same_email(self, db_session, test_user):
        update_data = UserUpdate(email="test@example.com")
        updated_user = update_user(db_session, test_user, update_data)
        assert updated_user.email == "test@example.com"

    def test_update_user_with_new_password(self, db_session, test_user):
        update_data = UserUpdate(password="NewStrongPass123!")
        updated_user = update_user(db_session, test_user, update_data)
        assert updated_user is not None

    def test_update_user_multiple_fields(self, db_session, test_user):
        update_data = UserUpdate(
            username="newusername",
            email="newemail@example.com"
        )
        updated_user = update_user(db_session, test_user, update_data)
        assert updated_user.username == "newusername"
        assert updated_user.email == "newemail@example.com"

    def test_create_user_async_success(self, db_session, add_roles_to_db):
        user_data = UserCreate(
            username="newuserasync",
            email="newasync@example.com",
            password="StrongPass123!"
        )
        user = create_user(db_session, user_data)
        assert user.username == "newuserasync"
        assert user.email == "newasync@example.com"

    def test_get_user_async_success(self, db_session, test_user):
        user = get_user(db_session, test_user.id)
        assert user is not None
        assert user.username == "testuser"

    def test_get_user_by_username_async_success(self, db_session, test_user):
        user = get_user_by_username(db_session, "testuser")
        assert user is not None
        assert user.username == "testuser"

    def test_authenticate_user_async_success(self, db_session, test_user):
        user = authenticate_user(db_session, "testuser", "TestPass123!")
        assert user is not None
        assert user.username == "testuser"

    def test_update_user_async_success(self, db_session, test_user):
        update_data = UserUpdate(username="updateduserasync")
        updated_user = update_user(db_session, test_user, update_data)
        assert updated_user.username == "updateduserasync"

    def test_create_user_exception_handling(self, db_session, add_roles_to_db):
        user_data = UserCreate(
            username="exceptiontestuser",
            email="exceptiontest@example.com",
            password="StrongPass123!"
        )
        
        user = create_user(db_session, user_data)
        assert user is not None

    def test_get_user_exception_handling(self, db_session, test_user):
        user = get_user(db_session, test_user.id)
        assert user is not None

    def test_get_user_by_username_exception_handling(self, db_session, test_user):
        user = get_user_by_username(db_session, "testuser")
        assert user is not None

    def test_authenticate_user_exception_handling(self, db_session, test_user):
        user = authenticate_user(db_session, "testuser", "TestPass123!")
        assert user is not None

    def test_update_user_exception_handling(self, db_session, test_user):
        update_data = UserUpdate(username="exceptiontest")
        updated_user = update_user(db_session, test_user, update_data)
        assert updated_user.username == "exceptiontest" 