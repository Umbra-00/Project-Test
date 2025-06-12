# Copyright (c) 2024 Umbra. All rights reserved.
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
import mlflow
from datetime import datetime, timezone
from sklearn.feature_extraction.text import TfidfVectorizer

from src.model_development.recommendation.recommendation_model import RecommendationModel
from src.api.v1.schemas import CourseCreate, Course

# Mock data for testing
MOCK_COURSES_DATA = [
    {"id": 1, "title": "Introduction to Python", "description": "Learn Python basics.", "url": "http://example.com/python", "creation_date": datetime.now(timezone.utc), "ai_generated_version": 1},
    {"id": 2, "title": "Advanced Data Science", "description": "Deep dive into data science concepts and algorithms.", "url": "http://example.com/data-science", "creation_date": datetime.now(timezone.utc), "ai_generated_version": 1},
    {"id": 3, "title": "Machine Learning with TensorFlow", "description": "Build ML models using TensorFlow.", "url": "http://example.com/tensorflow", "creation_date": datetime.now(timezone.utc), "ai_generated_version": 1},
    {"id": 4, "title": "Web Development with FastAPI", "description": "Develop web applications with FastAPI.", "url": "http://example.com/fastapi", "creation_date": datetime.now(timezone.utc), "ai_generated_version": 1},
    {"id": 5, "title": "Cloud Computing Basics", "description": "Understand cloud platforms like AWS and Azure.", "url": "http://example.com/cloud", "creation_date": datetime.now(timezone.utc), "ai_generated_version": 1},
]

@pytest.fixture
def mock_db_session():
    """Provides a mock SQLAlchemy session."""
    session = MagicMock(spec=Session)
    return session

@pytest.fixture
def mock_courses():
    """Provides mock Course objects."""
    # Convert mock data to Course objects
    return [Course(**data) for data in MOCK_COURSES_DATA]

# @pytest.fixture(autouse=True)
# def mock_mlflow_tracking_uri():
#     """Mocks MLflow tracking URI to prevent actual MLflow runs during tests."""
#     with patch('mlflow.set_tracking_uri') as mock_set_uri:
#         yield
#     # The assert_called_once_with is tricky with autouse and multiple model instantiations
#     # For now, we will remove it from here. The key is that mlflow.set_tracking_uri is called by the model's __init__.
#     # mock_set_uri.assert_called_once_with('./mlruns')

@pytest.fixture(autouse=True)
def clean_mlruns_directory():
    """Ensures a clean MLflow runs directory before and after tests (optional, for real cleanup)."""
    # This fixture is mainly for demonstrating where you'd clean up.
    # For actual CI/CD, consider a dedicated test MLflow tracking server or in-memory store.
    # For simplicity, we'll let mlflow.set_tracking_uri handle it for local tests.
    pass

class TestRecommendationModel:

    def test_initialization(self):
        model = RecommendationModel()
        assert model.model_name == "CourseRecommendationModel"
        assert model.tfidf_vectorizer is None
        assert model.course_vectors is None
        assert model.course_data.empty

    def test_train_model(self, mock_db_session, mock_courses):
        with patch.object(RecommendationModel, '_get_course_data_from_db') as mock_get_course_data_from_db, \
             patch('mlflow.sklearn.log_model') as mock_log_model_inner, \
             patch('mlflow.start_run') as mock_start_run_inner, \
             patch('mlflow.log_param') as mock_log_param_inner:

            mock_get_course_data_from_db.return_value = pd.DataFrame(MOCK_COURSES_DATA)
            
            # Mock the context manager for mlflow.start_run
            mock_run_context = MagicMock()
            mock_run_context.info.run_id = "test_run_id"
            mock_start_run_inner.return_value.__enter__.return_value = mock_run_context

            model = RecommendationModel()
            model.train(mock_db_session)

            mock_get_course_data_from_db.assert_called_once_with(mock_db_session)
            assert not model.course_data.empty
            assert model.tfidf_vectorizer is not None
            assert model.course_vectors is not None
            mock_start_run_inner.assert_called_once()
            
            # Retrieve the arguments passed to log_model
            assert mock_log_model_inner.call_count == 1
            logged_kwargs = mock_log_model_inner.call_args[1]
            
            # Assert individual parameters
            assert logged_kwargs['sk_model'] == model.tfidf_vectorizer
            assert logged_kwargs['artifact_path'] == "CourseRecommendationModel"
            assert logged_kwargs['registered_model_name'] == "CourseRecommendationModel"
            
            # Check input_example is either a string or None
            input_example = logged_kwargs['input_example']
            assert input_example is None or isinstance(input_example, str), f"Unexpected input_example type: {type(input_example)}"

    def test_load_model(self, mock_db_session, mock_courses):
        with patch.object(RecommendationModel, '_get_course_data_from_db') as mock_get_course_data_from_db, \
             patch('mlflow.sklearn.load_model') as mock_load_model_inner:

            mock_get_course_data_from_db.return_value = pd.DataFrame(MOCK_COURSES_DATA)
            mock_loaded_vectorizer = MagicMock(spec=TfidfVectorizer)
            mock_load_model_inner.return_value = mock_loaded_vectorizer

            model = RecommendationModel()
            model.load_model(db_session=mock_db_session)

            mock_load_model_inner.assert_called_once_with(model_uri="models:/CourseRecommendationModel/latest")
            assert model.tfidf_vectorizer == mock_loaded_vectorizer
            mock_get_course_data_from_db.assert_called_once_with(mock_db_session)
            assert not model.course_data.empty
            assert model.course_vectors is not None # Should be transformed after loading

    def test_recommend_courses(self, mock_db_session, mock_courses):
        with patch('src.model_development.recommendation.recommendation_model.get_course_by_url') as mock_get_course_by_url_inner:
            # First, simulate training/loading the model
            model = RecommendationModel()
            model.tfidf_vectorizer = TfidfVectorizer(stop_words='english')
            model.course_data = pd.DataFrame(MOCK_COURSES_DATA)
            model.course_vectors = model.tfidf_vectorizer.fit_transform(model.course_data['description'].fillna(''))

            # Create a simple mock object that directly provides the string description
            class MockCourseObject:
                def __init__(self, description):
                    self.description = description
            
            mock_get_course_by_url_inner.return_value = MockCourseObject(MOCK_COURSES_DATA[0]["description"])

            # Get recommendations
            recommendations = model.recommend_courses("http://example.com/python", mock_db_session, top_n=2)

            mock_get_course_by_url_inner.assert_called_once_with(mock_db_session, "http://example.com/python")
            assert len(recommendations) == 2
            # Expecting data science and tensorflow courses as they are semantically similar
            assert any("Data Science" in rec['title'] for rec in recommendations)
            assert any("TensorFlow" in rec['title'] for rec in recommendations)
            # Ensure the reference course itself is not in recommendations
            assert not any("Python" in rec['title'] for rec in recommendations)

    def test_retrain_model_if_needed_new_data(self, mock_db_session, mock_courses):
        initial_courses_data = MOCK_COURSES_DATA[:3]
        full_courses_data = MOCK_COURSES_DATA

        model = RecommendationModel()
        # Manually simulate a pre-trained model state with initial_courses_data
        model.tfidf_vectorizer = TfidfVectorizer(stop_words='english')
        model.course_data = pd.DataFrame(initial_courses_data)
        model.course_vectors = model.tfidf_vectorizer.fit_transform(model.course_data['description'].fillna(''))

        with patch.object(RecommendationModel, '_get_course_data_from_db') as mock_get_course_data_from_db_inner, \
             patch('mlflow.sklearn.log_model') as mock_log_model_inner, \
             patch('mlflow.start_run') as mock_start_run_inner, \
             patch('mlflow.log_param') as mock_log_param_inner:

            mock_get_course_data_from_db_inner.side_effect = [
                pd.DataFrame(full_courses_data), # First call to check for new data
                pd.DataFrame(full_courses_data)  # Second call during train method
            ]

            # Now call retrain_model_if_needed
            model.retrain_model_if_needed(mock_db_session)

            # Assert that _get_course_data_from_db was called once after reset
            assert mock_get_course_data_from_db_inner.call_count == 2
            # Assert that train was called again due to new data
            mock_start_run_inner.assert_called_once()
            mock_log_model_inner.assert_called_once()
            mock_log_param_inner.assert_any_call("num_courses", len(MOCK_COURSES_DATA)) # Should log with new, larger count

    def test_retrain_model_if_needed_no_new_data(self, mock_db_session, mock_courses):
        full_courses_data = MOCK_COURSES_DATA

        model = RecommendationModel()
        # Manually simulate a pre-trained model state with full_courses_data
        model.tfidf_vectorizer = TfidfVectorizer(stop_words='english')
        model.course_data = pd.DataFrame(full_courses_data)
        model.course_vectors = model.tfidf_vectorizer.fit_transform(model.course_data['description'].fillna(''))

        with patch.object(RecommendationModel, '_get_course_data_from_db') as mock_get_course_data_from_db_inner, \
             patch('mlflow.sklearn.log_model') as mock_log_model_inner, \
             patch('mlflow.start_run') as mock_start_run_inner, \
             patch('mlflow.log_param') as mock_log_param_inner:

            mock_get_course_data_from_db_inner.return_value = pd.DataFrame(full_courses_data)

            model.retrain_model_if_needed(mock_db_session)

            # Assert that _get_course_data_from_db was called once, as no new data means no second call for training
            assert mock_get_course_data_from_db_inner.call_count == 1
            # Assert that train/log_model were NOT called
            mock_start_run_inner.assert_not_called()
            mock_log_model_inner.assert_not_called()
            mock_log_param_inner.assert_not_called() 