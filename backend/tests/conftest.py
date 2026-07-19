"""Common test configurations and fixtures."""

import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path so 'app' is importable
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)


@pytest.fixture(scope="session")
def client():
    """Session-scoped FastAPI TestClient."""
    from app.main import create_app
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
