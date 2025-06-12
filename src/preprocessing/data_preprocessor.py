import pandas as pd
from sqlalchemy.orm import sessionmaker

from src.data_engineering.db_utils import SessionLocal
from src.data_engineering.database_models import Course
from src.utils.logging_utils import setup_logging

# Setup logging
logger = setup_logging(__name__)

def fetch_courses_from_db() -> pd.DataFrame | None:
    """Fetches course data from the database and returns it as a pandas DataFrame."""
    logger.info("Fetching course data from the database...")
    Session = SessionLocal
    with Session() as session:
        try:
            courses = session.query(Course).all()
            if not courses:
                logger.warning("No courses found in the database.")
                return None

            # Convert SQLAlchemy objects to dictionaries for DataFrame creation
            course_data = [
                {
                    "id": course.id,
                    "title": course.title,
                    "description": course.description,
                    "url": course.url,
                    "created_by_user_id": course.created_by_user_id,
                    "creation_date": course.creation_date,
                    "difficulty_level": course.difficulty_level,
                    "ai_generated_version": course.ai_generated_version
                } for course in courses
            ]
            df = pd.DataFrame(course_data)
            logger.info(f"Successfully fetched {len(df)} courses from the database.")
            return df
        except Exception as e:
            logger.error(f"Error fetching courses from DB: {e}")
            return None

def clean_course_data(df: pd.DataFrame) -> pd.DataFrame:
    """Performs basic cleaning on course data.

    - Fills missing descriptions with empty strings.
    - Converts text to lowercase.
    - Handles potential duplicates (though ingestion should prevent them).
    """
    logger.info("Cleaning course data...")
    # Fill missing descriptions
    df['description'] = df['description'].fillna('')

    # Convert title and description to lowercase for consistency
    df['title'] = df['title'].str.lower()
    df['description'] = df['description'].str.lower()

    # Basic duplicate handling (though URL unique constraint should handle most)
    df.drop_duplicates(subset=['url'], inplace=True)

    logger.info("Course data cleaning complete.")
    return df

def feature_engineer_course_data(df: pd.DataFrame) -> pd.DataFrame:
    """Adds simple features to the course data.

    - Example: text length of description.
    """
    logger.info("Engineering features for course data...")
    df['description_length'] = df['description'].apply(len)

    logger.info("Feature engineering complete.")
    return df

if __name__ == "__main__":
    logger.info("--- Data Preprocessor Module ---")
    courses_df = fetch_courses_from_db()

    if courses_df is not None and not courses_df.empty:
        logger.info(f"Original DataFrame shape: {courses_df.shape}")
        cleaned_df = clean_course_data(courses_df)
        featured_df = feature_engineer_course_data(cleaned_df)

        logger.info(f"Processed DataFrame head:\n{featured_df.head()}")
        logger.info(f"Processed DataFrame shape: {featured_df.shape}")
    else:
        logger.warning("No data to process or an error occurred during fetch.") 