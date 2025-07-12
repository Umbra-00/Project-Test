# Copyright (c) 2024 Umbra. All rights reserved.
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import mlflow
import mlflow.sklearn
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func

from src.utils.logging_utils import setup_logging
from src.api.v1.crud import get_courses, get_course_by_url
from src.data_engineering.database_models import Course

logger = setup_logging(__name__)

# Configure MLflow tracking URI (can be set via environment variable MLFLOW_TRACKING_URI)
# For local development, this defaults to ./mlruns
# mlflow.set_tracking_uri("http://localhost:5000") # Uncomment if you have a remote MLflow server


class RecommendationModel:
    """
    A content-based recommendation model that uses TF-IDF and cosine similarity
    to recommend courses based on course descriptions.
    """

    def __init__(self, model_name: str = "CourseRecommendationModel"):
        self.model_name = model_name
        self.tfidf_vectorizer = None
        self.course_vectors = None
        self.course_data = pd.DataFrame()  # Store course data fetched from DB
        self.mlflow_tracking_uri = "./mlruns"  # Local MLflow tracking URI
        mlflow.set_tracking_uri(self.mlflow_tracking_uri)

    def _get_course_data_from_db(self, db_session: Session) -> pd.DataFrame:
        """
        Fetches all courses from the database and returns them as a Pandas DataFrame.
        """
        logger.info("Fetching course data from database...")
        courses_db = get_courses(db_session)  # Use the CRUD function to get courses
        if not courses_db:
            logger.warning("No courses found in the database.")
            return pd.DataFrame()

        # Convert SQLAlchemy objects to dictionaries for DataFrame creation
        courses_data = []
        for course in courses_db:
            courses_data.append(
                {
                    "id": course.id,
                    "title": course.title,
                    "description": course.description,
                    "url": course.url,
                }
            )
        df = pd.DataFrame(courses_data)
        logger.info(f"Fetched {len(df)} courses from the database.")
        return df

    def _get_course_count_from_db(self, db_session: Session) -> int:
        """
        Fetches the total count of courses from the database.
        """
        logger.info("Fetching course count from database...")
        try:
            count = db_session.query(func.count(Course.id)).scalar()
            logger.info(f"Fetched {count} courses in the database.")
            return count
        except Exception as e:
            logger.error(f"Error fetching course count from DB: {e}")
            return 0

    def train(self, db_session: Session):
        """
        Trains the TF-IDF vectorizer and computes course similarity vectors.
        Logs the model to MLflow.
        """
        self.course_data = self._get_course_data_from_db(db_session)
        if self.course_data.empty:
            logger.warning("Cannot train model: No course data available.")
            return

        # Fill any potential NaN descriptions with an empty string
        self.course_data["description"] = self.course_data["description"].fillna("")

        # Initialize TF-IDF Vectorizer with max_features to limit vocabulary size
        self.tfidf_vectorizer = TfidfVectorizer(stop_words="english", max_features=5000) # Added max_features
        self.course_vectors = self.tfidf_vectorizer.fit_transform(
            self.course_data["description"]
        )
        logger.info(
            f"Recommendation model trained with {len(self.course_data)} courses."
        )

        # Log model with MLflow
        with mlflow.start_run():
            mlflow.sklearn.log_model(
                sk_model=self.tfidf_vectorizer,
                artifact_path=self.model_name,  # Use model_name as artifact_path
                registered_model_name=self.model_name,
                input_example=(
                    self.course_data["description"].iloc[0]
                    if not self.course_data.empty
                    else None
                ),
            )
            mlflow.log_param("num_courses", len(self.course_data))
            mlflow.log_param("vectorizer_type", "tfidf_max_features") # Log this change
            logger.info(
                f"TF-IDF model logged to MLflow under model name: {self.model_name}"
            )

    def load_model(self, db_session: Session):
        try:
            # Define the model URI based on MLFLOW_TRACKING_URI and model name
            # Assuming MLflow is serving artifacts from /mlruns as configured
            # and model is registered as 'CourseRecommendationModel'
            model_uri = f"models:/CourseRecommendationModel/latest"
            self.tfidf_vectorizer = mlflow.sklearn.load_model(model_uri)
            self.model = mlflow.pyfunc.load_model(model_uri)
            logger.info(f"Successfully loaded model '{model_uri}' from MLflow.")

            # Re-train only if the model couldn't be loaded or if data is empty
            if self.model is None or not self.course_data:
                logger.info("Model not loaded or course data empty, attempting to train.")
                self.train(db_session=db_session)  # Pass db_session to train

        except Exception as e:
            logger.error(f"Failed to load model 'CourseRecommendationModel' version 'latest' from MLflow: {e}")
            # Fallback to training if loading fails
            logger.info("Attempting to train model due to loading failure.")
            self.train(db_session=db_session)  # Pass db_session to train

    def retrain_model_if_needed(self, db_session: Session):
        """
        Retrains the model if new course data is available or on a scheduled basis.
        For simplicity, this example always retrains with the latest data.
        In a real MLOps pipeline, you'd add logic to decide *when* to retrain
        (e.g., data drift, performance decay, new data thresholds).
        """
        logger.info("Checking for new data to retrain recommendation model...")
        latest_course_count = self._get_course_count_from_db(db_session)

        if latest_course_count == 0:
            logger.warning("No course data available for retraining.")
            return

        # Simple check: if the number of courses has changed, retrain.
        # In a more advanced setup, you'd compare data hashes or content.

        if self.course_data.empty or latest_course_count > len(self.course_data):
            logger.info(
                f"New courses detected ({latest_course_count} vs {len(self.course_data) if not self.course_data.empty else 0}). Retraining model..."
            )
            self.train(db_session)
            logger.info("Recommendation model retrained successfully with new data.")
        elif (
            self.tfidf_vectorizer is None
            or self.course_vectors is None
            or self.course_data.empty
        ):
            logger.info(
                "Model not initialized or loaded. Training model for the first time."
            )
            self.train(db_session)
        else:
            logger.info(
                "No significant new data detected for retraining or model is already trained and loaded."
            )
            # Optionally, you could force a retrain periodically here regardless of data changes
            # self.train(db_session) # Uncomment to force periodic retraining

    def recommend_courses(
        self, course_url: str, db_session: Session, top_n: int = 5
    ) -> List[dict]:
        """
        Recommends similar courses based on a given course URL.

        Args:
            course_url (str): The URL of the reference course.
            db_session (Session): The database session.
            top_n (int): The number of top recommendations to return.

        Returns:
            List[dict]: A list of dictionaries, each representing a recommended course.
        """
        if (
            self.tfidf_vectorizer is None
            or self.course_vectors is None
            or self.course_data.empty
        ):
            logger.warning(
                "Model not trained or loaded. Cannot provide recommendations."
            )
            return []

        # Fetch the reference course from the database using the CRUD function
        reference_course = get_course_by_url(db_session, course_url)
        if not reference_course:
            logger.warning(f"Reference course with URL {course_url} not found.")
            return []

        # Find the index of the reference course in the DataFrame
        ref_course_idx = self.course_data[self.course_data["url"] == course_url].index
        if ref_course_idx.empty:
            logger.warning(
                f"Reference course URL {course_url} not found in model's course data."
            )
            return []
        ref_course_idx = ref_course_idx[0]

        # Compute cosine similarity between the reference course and all other courses
        # Ensure description is not None before vectorizing
        reference_vector = self.tfidf_vectorizer.transform(
            [reference_course.description if reference_course.description else ""]
        )
        similarities = cosine_similarity(
            reference_vector, self.course_vectors
        ).flatten()

        # Get top_n similar courses, excluding the reference course itself
        # Create a Series to easily sort with original indices
        similar_courses_indices = (
            pd.Series(similarities).sort_values(ascending=False).index
        )

        recommended_courses = []
        for idx in similar_courses_indices:
            if idx == ref_course_idx:  # Skip the reference course itself
                continue

            course = self.course_data.iloc[idx]
            recommended_courses.append(
                {
                    "title": course["title"],
                    "description": course["description"],
                    "url": course["url"],
                    "similarity": similarities[idx],
                }
            )
            if len(recommended_courses) >= top_n:
                break

        logger.info(
            f"Generated {len(recommended_courses)} recommendations for {course_url}."
        )
        return recommended_courses


if __name__ == "__main__":
    print("--- Recommendation Model Module ---")
    # Example usage (assuming a database is set up and populated)
    from src.data_engineering.db_utils import SessionLocal
    from src.api.v1.crud import create_course, get_course_by_url
    from src.api.v1.schemas import CourseCreate

    # Ensure MLflow tracking URI is set
    # os.environ["MLFLOW_TRACKING_URI"] = "./mlruns" # This is set in __init__ for consistency

    reco_model = RecommendationModel()

    with SessionLocal() as db:
        # Add some dummy courses if the DB is empty
        if not get_courses(db):
            print("Adding dummy courses for testing...")
            dummy_courses = [
                CourseCreate(
                    title="Data Science Fundamentals",
                    description="Introduction to data science concepts.",
                    url="http://example.com/ds-fundamentals",
                ),
                CourseCreate(
                    title="Machine Learning Basics",
                    description="Core machine learning algorithms.",
                    url="http://example.com/ml-basics",
                ),
                CourseCreate(
                    title="Advanced Python Programming",
                    description="Deep dive into Python for advanced users.",
                    url="http://example.com/adv-python",
                ),
                CourseCreate(
                    title="SQL for Data Analysts",
                    description="Essential SQL for data manipulation.",
                    url="http://example.com/sql-analysts",
                ),
                CourseCreate(
                    title="Deep Learning with PyTorch",
                    description="Neural networks and deep learning using PyTorch.",
                    url="http://example.com/dl-pytorch",
                ),
                CourseCreate(
                    title="Introduction to Web Development",
                    description="Basics of front-end and back-end web development.",
                    url="http://example.com/web-dev",
                ),
            ]
            for dc in dummy_courses:
                try:
                    create_course(db, dc)
                except Exception as e:
                    print(f"Skipping adding dummy course {dc.title} due to error: {e}")
            db.commit()
            print("Dummy courses added.")

        # Train the model (or re-train if data changed)
        print("Training recommendation model...")
        reco_model.train(db)
        print("Model training complete.")

        # Example of loading the model
        print("Attempting to load the trained model...")
        try:
            reco_model.load_model(db_session=db)
            print("Model loaded successfully.")

            # Example of getting recommendations
            print("Getting recommendations for 'Data Science Fundamentals'...")
            target_url = "http://example.com/ds-fundamentals"
            recommendations = reco_model.recommend_courses(target_url, db, top_n=3)
            if recommendations:
                for rec in recommendations:
                    print(f"  - {rec['title']} (Similarity: {rec['similarity']:.2f})")
            else:
                print(f"No recommendations found for {target_url}.")

        except Exception as e:
            print(f"Error during model load or recommendation: {e}")

    print("\nRemember to run 'mlflow ui' in your terminal to view MLflow experiments.")
