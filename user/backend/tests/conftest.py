"""Pytest fixtures and test environment setup."""

from collections.abc import Generator
import pytest
from fastapi.testclient import TestClient
from app.config import Settings, get_settings
from app.database import Base, close_db_engine, get_db, get_engine
from app.main import create_app


@pytest.fixture(scope="session")
def test_settings(tmp_path_factory) -> Settings:
    """Provide isolated settings for the test suite."""
    upload_test_dir = str(tmp_path_factory.mktemp("test_uploads"))
    return Settings(
        app_name="AI Resume Agent - Test API",
        app_version="0.1.0-test",
        env="testing",
        debug=True,
        database_url="sqlite:///:memory:",
        cors_origins=["http://localhost:3000"],
        upload_dir=upload_test_dir,
    )


@pytest.fixture
def app(test_settings: Settings):
    """Create test application instance with test settings."""
    # Override settings dependency
    get_settings.cache_clear()
    application = create_app(test_settings)
    engine = get_engine(test_settings)
    Base.metadata.create_all(bind=engine)
    yield application
    close_db_engine()
    get_settings.cache_clear()


@pytest.fixture
def client(app) -> Generator[TestClient, None, None]:
    """Test client for issuing requests against the application."""
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
