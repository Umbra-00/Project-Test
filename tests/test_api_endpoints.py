"""
Tests for FastAPI endpoints to ensure proper functionality.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from src.api.v1.main import app
from src.data_engineering.database_models import Course


@pytest.fixture
def client():
    """Create a test client for FastAPI."""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def sample_course_data():
    """Sample course data for testing."""
    return {
        "title": "Test Course",
        "description": "A test course description",
        "url": "https://example.com/test-course",
        "difficulty": "Beginner",
        "category": "Programming",
    }


@pytest.fixture
def sample_course_db_object():
    """Sample course database object."""
    from datetime import datetime
    return Course(
        id=1,
        title="Test Course",
        description="A test course description",
        url="https://example.com/test-course",
        difficulty="Beginner",
        category="Programming",
        creation_date=datetime.utcnow(),
        ai_generated_version=1,
    )


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_check_success(self, client):
        """Test successful health check."""
        with patch("src.data_engineering.db_utils.check_db_health", return_value=True):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json() == {
                "status": "healthy",
                "database_connection": "successful",
            }

    def test_health_check_failure(self, client):
        """Test health check with database failure."""
        with patch("src.data_engineering.db_utils.check_db_health", return_value=False):
            response = client.get("/health")
            assert response.status_code == 500


class TestCoursesEndpoint:
    """Test the courses endpoints."""

    def test_get_courses_empty(self, client, mock_db):
        """Test getting courses when database is empty."""
        with patch("src.data_engineering.db_utils.get_db", return_value=mock_db), patch(
            "src.api.v1.crud.get_courses", return_value=[]
        ):

            response = client.get("/courses/")
            assert response.status_code == 200
            assert response.json() == []

    def test_get_courses_with_data(self, client, mock_db, sample_course_db_object):
        """Test getting courses with data."""
        with patch("src.data_engineering.db_utils.get_db", return_value=mock_db), patch(
            "src.api.v1.crud.get_courses", return_value=[sample_course_db_object]
        ):

            response = client.get("/courses/")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["title"] == "Test Course"

    def test_get_courses_with_filters(self, client, mock_db):
        """Test getting courses with filters."""
        with patch("src.data_engineering.db_utils.get_db", return_value=mock_db), patch(
            "src.api.v1.crud.get_courses", return_value=[]
        ):

            response = client.get(
                "/courses/",
                params={
                    "limit": 10,
                    "skip": 0,
                    "sort_by": "title",
                    "sort_order": "asc",
                    "filter_criteria": '{"difficulty": "Beginner"}',
                },
            )
            assert response.status_code == 200

    def test_get_courses_invalid_filter(self, client, mock_db):
        """Test getting courses with invalid filter JSON."""
        with patch("src.data_engineering.db_utils.get_db", return_value=mock_db):
            response = client.get(
                "/courses/", params={"filter_criteria": "invalid-json"}
            )
            assert response.status_code == 400

    def test_post_courses_valid(
        self, client, mock_db, sample_course_data, sample_course_db_object
    ):
        """Test posting valid course data."""
        with patch("src.data_engineering.db_utils.get_db", return_value=mock_db), patch(
            "src.data_collection.data_ingestion.validate_scraped_data",
            return_value=True,
        ), patch("src.api.v1.crud.create_course", return_value=sample_course_db_object):

            response = client.post("/courses/", json=[sample_course_data])
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["title"] == "Test Course"

    def test_post_courses_invalid_data(self, client, mock_db):
        """Test posting invalid course data."""
        with patch("src.data_engineering.db_utils.get_db", return_value=mock_db), patch(
            "src.data_collection.data_ingestion.validate_scraped_data",
            return_value=False,
        ):

            response = client.post("/courses/", json=[{"title": "", "url": ""}])
            assert response.status_code == 400

    def test_post_courses_empty_data(self, client, mock_db):
        """Test posting empty course data."""
        with patch("src.data_engineering.db_utils.get_db", return_value=mock_db):
            response = client.post("/courses/", json=[])
            assert response.status_code == 400

    def test_get_course_by_url_success(self, client, mock_db, sample_course_db_object):
        """Test getting a course by URL successfully."""
        with patch("src.data_engineering.db_utils.get_db", return_value=mock_db), patch(
            "src.api.v1.crud.get_course_by_url", return_value=sample_course_db_object
        ):

            response = client.get("/courses/https://example.com/test-course")
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Test Course"

    def test_get_course_by_url_not_found(self, client, mock_db):
        """Test getting a course by URL when not found."""
        with patch("src.data_engineering.db_utils.get_db", return_value=mock_db), patch(
            "src.api.v1.crud.get_course_by_url", return_value=None
        ):

            response = client.get("/courses/https://example.com/nonexistent")
            assert response.status_code == 404


class TestAPIDocumentation:
    """Test API documentation endpoints."""

    def test_docs_available(self, client):
        """Test that API documentation is available."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema(self, client):
        """Test that OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert "openapi" in response.json()
