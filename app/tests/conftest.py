import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import Base
from app.models.user import User
from app.models.role import Role
from app.services.user_service import create_user
from app.schemas.user import UserCreate

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_user(db_session):
    # Create test roles
    admin_role = Role(name="Admin")
    author_role = Role(name="Author")
    reader_role = Role(name="Reader")
    db_session.add_all([admin_role, author_role, reader_role])
    db_session.commit()
    
    # Create test user
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="TestPass123!"
    )
    user = create_user(db_session, user_data)
    return user 