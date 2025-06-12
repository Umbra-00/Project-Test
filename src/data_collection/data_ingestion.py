# Copyright (c) 2024 Umbra. All rights reserved.
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd

from src.data_engineering.db_utils import SessionLocal
from src.data_engineering.database_models import Base, User, Course, Content, LearningProgress, Assessment, AssessmentResult, Interaction
from src.data_collection.web_scraper import fetch_html_content, parse_html_content
from src.utils.logging_utils import setup_logging
from src.api.v1.crud import create_course
from src.api.v1.schemas import CourseCreate

# Setup logging
logger = setup_logging(__name__)

def validate_scraped_data(data: dict) -> bool:
    """Basic validation for scraped data. Expand this as needed."""
    if not isinstance(data, dict):
        logger.warning("Data is not a dictionary.")
        return False
    # Example validation: check for 'title' and 'url'
    if "title" not in data or not data["title"]:
        logger.warning("Data missing 'title' or title is empty.")
        return False
    if "url" not in data or not data["url"]:
        logger.warning("Data missing 'url' or url is empty.")
        return False
    return True

def ingest_course_data_batch(course_data_list: list[dict], session: Session) -> None:
    """Ingests a list of scraped course data into the database within a given session."""
    courses_to_add = []
    for course_data in course_data_list:
        if not validate_scraped_data(course_data):
            logger.error(f"Invalid course data provided for ingestion: {course_data}. Skipping.")
            continue

        # Check if course already exists to prevent duplicates. This check remains
        # here as it's part of the ingestion *logic*, not just CRUD.
        existing_course = session.query(Course).filter_by(url=course_data["url"]).first()
        if existing_course:
            logger.info(f"Course with URL {course_data['url']} already exists. Skipping.")
            continue

        # Use Pydantic model for validation before passing to CRUD
        try:
            course_create = CourseCreate(title=course_data.get("title"), description=course_data.get("description"), url=course_data.get("url"))
            courses_to_add.append(course_create)
            logger.info(f"Prepared to ingest course: {course_data.get('title')}")
        except Exception as e:
            logger.error(f"Error validating course data with Pydantic: {e}. Skipping {course_data.get('title')}")
            continue
    
    if courses_to_add:
        for course_create in courses_to_add:
            create_course(session, course_create) # create_course now raises custom exceptions
        logger.info(f"Successfully processed {len(courses_to_add)} new courses for ingestion.")
    else:
        logger.info("No new valid courses to ingest.")


if __name__ == "__main__":
    logger.info("--- Data Ingestion Module ---")

    # Example of how web_scraper might integrate with data_ingestion
    # For demonstration, let's ingest a few dummy courses
    sample_courses = [
        {
            "title": "Introduction to Python Programming",
            "description": "Learn the basics of Python programming, including data types, control structures, and functions.",
            "url": "https://example.com/python-intro"
        },
        {
            "title": "Advanced SQL for Data Analysis",
            "description": "Master complex SQL queries, window functions, and database optimization techniques for data analysis.",
            "url": "https://example.com/advanced-sql"
        },
        {
            "title": "Machine Learning with Scikit-learn",
            "description": "Explore supervised and unsupervised machine learning algorithms using the Scikit-learn library.",
            "url": "https://example.com/ml-sklearn"
        },
        {
            "title": "Deep Learning with TensorFlow",
            "description": "Dive into neural networks, Keras, and building deep learning models for various applications.",
            "url": "https://example.com/dl-tensorflow"
        },
        {
            "title": "Web Scraping for Data Science",
            "description": "Learn how to extract data from websites using Python, BeautifulSoup, and Requests.",
            "url": "https://example.com/web-scraping"
        }
    ]

    with SessionLocal() as session:
        logger.info(f"Ingesting {len(sample_courses)} sample courses...")
        # The exceptions raised by create_course will propagate here if not caught
        # For a script like this, it might be acceptable to let it fail or add a try/except
        # around the entire ingest_course_data_batch call if granular error reporting per item isn't needed.
        try:
            ingest_course_data_batch(sample_courses, session)
        except Exception as e:
            logger.error(f"Error during batch ingestion in main: {e}")

    # Original Coursera example (will be skipped if URL already exists)
    # sample_url = "https://www.coursera.org/" # Placeholder, replace with a real course URL
    # logger.info(f"Attempting to scrape and ingest data from: {sample_url}")
    # html_content = fetch_html_content(sample_url)
    # if html_content:
    #     soup = parse_html_content(html_content)
    #     page_title = soup.title.string if soup.title else "No Title Found"
    #     dummy_course_data = {
    #         "title": f"Scraped Course: {page_title}",
    #         "description": "Description parsed from web content.",
    #         "url": sample_url,
    #     }
    #     with SessionLocal() as session:
    #         ingest_course_data_batch([dummy_course_data], session)
    # else:
    #     logger.error(f"Failed to fetch HTML content from {sample_url}. Cannot ingest data.") 