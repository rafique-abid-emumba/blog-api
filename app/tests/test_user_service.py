import pytest
from fastapi import HTTPException
from app.services.user_service import (
    create_user, authenticate_user, update_user, 
    is_duplicate_username, is_duplicate_email, is_strong_password
)
from app.schemas.user import UserCreate, UserUpdate
from app.models.role import Role

class TestUserService:
    
    def test_create_user_success(self, db_session):
        # Create test roles
        admin_role = Role(name="Admin")
        author_role = Role(name="Author")
        reader_role = Role(name="Reader")
        db_session.add_all([admin_role, author_role, reader_role])
        db_session.commit()

        user_data = UserCreate(
            username="newuser",
            email="new@example.com",
            password="StrongPass123!"
        )
        user = create_user(db_session, user_data)
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.role_id == 3
    
    def test_create_user_duplicate_username(self, db_session):
        # Create first user
        user_data1 = UserCreate(
            username="testuser",
            email="test1@example.com",
            password="StrongPass123!"
        )
        create_user(db_session, user_data1)
        
        # Try to create second user with same username
        user_data2 = UserCreate(
            username="testuser",
            email="test2@example.com",
            password="StrongPass123!"
        )
        with pytest.raises(HTTPException) as exc_info:
            create_user(db_session, user_data2)
        assert exc_info.value.status_code == 400
        assert "Username already exists" in exc_info.value.detail
    
    def test_create_user_duplicate_email(self, db_session):
        # Create first user
        user_data1 = UserCreate(
            username="user1",
            email="test@example.com",
            password="StrongPass123!"
        )
        create_user(db_session, user_data1)
        
        # Try to create second user with same email
        user_data2 = UserCreate(
            username="user2",
            email="test@example.com",
            password="StrongPass123!"
        )
        with pytest.raises(HTTPException) as exc_info:
            create_user(db_session, user_data2)
        assert exc_info.value.status_code == 400
        assert "Email already exists" in exc_info.value.detail
    
    def test_create_user_weak_password(self, db_session):
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="weak"  # Too short, no uppercase, no number, no special char
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
        user = authenticate_user(db_session, "testuser", "wrongpassword")
        assert user is None
    
    def test_authenticate_user_nonexistent_user(self, db_session):
        user = authenticate_user(db_session, "nonexistent", "password")
        assert user is None
    
    def test_update_user_success(self, db_session, test_user):
        update_data = UserUpdate(username="updateduser")
        updated_user = update_user(db_session, test_user, update_data)
        assert updated_user.username == "updateduser"
    
    def test_update_user_not_found(self, db_session):
        update_data = UserUpdate(username="updateduser")
        with pytest.raises(HTTPException) as exc_info:
            update_user(db_session, None, update_data)
        assert exc_info.value.status_code == 404
    
    def test_is_strong_password_valid(self):
        assert is_strong_password("StrongPass123!") == True
        assert is_strong_password("Another1@") == True
    
    def test_is_strong_password_invalid(self):
        assert is_strong_password("weak") == False  # Too short
        assert is_strong_password("nouppercase123!") == False  # No uppercase
        assert is_strong_password("NoNumbers!") == False  # No numbers
        assert is_strong_password("NoSpecial123") == False  # No special chars
    
    def test_is_duplicate_username_true(self, db_session, test_user):
        assert is_duplicate_username(db_session, "testuser") == True
    
    def test_is_duplicate_username_false(self, db_session):
        assert is_duplicate_username(db_session, "nonexistent") == False
    
    def test_is_duplicate_email_true(self, db_session, test_user):
        assert is_duplicate_email(db_session, "test@example.com") == True
    
    def test_is_duplicate_email_false(self, db_session):
        assert is_duplicate_email(db_session, "nonexistent@example.com") == False 