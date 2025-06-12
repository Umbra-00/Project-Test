import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from src.data_collection.data_ingestion import ingest_course_data_batch, validate_scraped_data
from src.data_engineering.database_models import Course

# Mock data for testing
@pytest.fixture
def mock_session():
    return MagicMock(spec=Session)

@pytest.fixture
def sample_valid_course_data():
    return {
        "title": "Test Course",
        "description": "A test description.",
        "url": "https://test.com/course"
    }

@pytest.fixture
def sample_invalid_course_data():
    return {"title": "", "url": ""} # Missing title and URL

def test_validate_scraped_data_valid(sample_valid_course_data):
    assert validate_scraped_data(sample_valid_course_data) is True

def test_validate_scraped_data_invalid(sample_invalid_course_data):
    assert validate_scraped_data(sample_invalid_course_data) is False

def test_ingest_course_data_batch_new_course(mock_session, sample_valid_course_data):
    # Simulate no existing course
    mock_session.query.return_value.filter_by.return_value.first.return_value = None
    
    ingest_course_data_batch([sample_valid_course_data], mock_session)
    
    # Verify that add and commit were called
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()

def test_ingest_course_data_batch_existing_course(mock_session, sample_valid_course_data):
    # Simulate an existing course
    mock_session.query.return_value.filter_by.return_value.first.return_value = Course(id=1, title="Existing Course", url=sample_valid_course_data["url"])
    
    ingest_course_data_batch([sample_valid_course_data], mock_session)
    
    # Verify that add and commit were NOT called, as the course already exists
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()

def test_ingest_course_data_batch_invalid_data_skipped(mock_session, sample_invalid_course_data):
    ingest_course_data_batch([sample_invalid_course_data], mock_session)
    
    # Verify that add and commit were NOT called for invalid data
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()

def test_ingest_course_data_batch_mixed_data(mock_session, sample_valid_course_data, sample_invalid_course_data):
    # Simulate a list with both valid and invalid data
    mixed_data = [sample_valid_course_data, sample_invalid_course_data]
    mock_session.query.return_value.filter_by.return_value.first.return_value = None # No existing valid course
    
    ingest_course_data_batch(mixed_data, mock_session)
    
    # Verify that add and commit were called once for the valid data
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once() 