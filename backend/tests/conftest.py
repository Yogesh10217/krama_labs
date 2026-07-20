import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend root is on sys.path so 'app' is importable
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.db.base import Base
from app.db.session import get_db
from app.db.models import *  # Ensure all models are imported and registered
from app.db.models.organization import Organization
from app.main import create_app

# SQLite in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create test database schema once per session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Provides an isolated database session per test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback() # Ensure rollback after each test
        session.close()

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture(scope="session")
def app_instance():
    """FastAPI application instance with overridden dependencies."""
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    return app

@pytest.fixture(scope="session")
def client(app_instance):
    """Session-scoped FastAPI TestClient."""
    with TestClient(app_instance, raise_server_exceptions=False) as test_client:
        yield test_client

@pytest.fixture(scope="function")
def test_org(db_session):
    """Provides a default test organization."""
    org = Organization(name="Test Org", slug=f"test-org-{uuid.uuid4().hex[:8]}")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org

