import streamlit as st
import requests
import json
import urllib.parse  # For URL encoding
import os

# --- Configuration ---
# Determine backend URL based on environment
if os.getenv("RENDER"):
    # When on Render, use the URL provided by Render's environment variables
    FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "https://umbra-backend.onrender.com")
elif os.getenv("BACKEND_URL"):
    # When in Docker Compose, use the service URL from the BACKEND_URL env var
    FASTAPI_BASE_URL = os.getenv("BACKEND_URL")
else:
    # For local development outside of Docker, fall back to localhost
    FASTAPI_BASE_URL = "http://localhost:8000"

API_URL = f"{FASTAPI_BASE_URL}/api/v1"
APP_HOST = os.getenv("APP_HOST", "localhost")


st.set_page_config(layout="wide", page_title="Umbra Personalized Learning Platform")


# --- Helper Functions for API Calls ---
def fetch_courses(
    skip: int = 0,
    limit: int = 100,
    sort_by: str = "",
    sort_order: str = "asc",
    filter_criteria: dict = {},
):
    params = {
        "skip": skip,
        "limit": limit,
    }
    if sort_by and isinstance(sort_by, str) and sort_by != "None":
        params["sort_by"] = sort_by
        params["sort_order"] = sort_order
    if filter_criteria:
        params["filter_criteria"] = json.dumps(filter_criteria)

    try:
        response = requests.get(
            f"{API_URL}/courses/", params=params, timeout=(10, 10)
        )
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching courses: {e}")
        return []

def post_courses(course_data: list):
    url = f"{API_URL}/courses/"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(course_data), timeout=(10, 10))
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(
            "Connection Error: Could not connect to the FastAPI backend. Please ensure the backend is running."
        )
        return None
    except requests.exceptions.HTTPError as e:
        try:
            error_detail = e.response.json().get('detail', 'Unknown error')
        except ValueError:
            error_detail = e.response.text if hasattr(e.response, 'text') else 'Unknown error'
        st.error(f"HTTP Error: {e.response.status_code} - {error_detail}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during POST: {e}")
        return None

def get_course_by_url(course_url: str):
    # URL-encode the course_url to handle special characters correctly in the path
    encoded_url = urllib.parse.quote(course_url, safe='')
    url = f"{API_URL}/courses/{encoded_url}"
    try:
        response = requests.get(url, timeout=(10, 10))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(
            "Connection Error: Could not connect to the FastAPI backend. Please ensure the backend is running."
        )
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            st.warning(f"Course not found: {course_url}")
        else:
            try:
                error_detail = e.response.json().get('detail', 'Unknown error')
            except ValueError:
                error_detail = e.response.text if hasattr(e.response, 'text') else 'Unknown error'
            st.error(f"HTTP Error: {e.response.status_code} - {error_detail}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during GET course by URL: {e}")
        return None

def validate_json_input(json_string: str):
    """
    Validates and parses a JSON string, ensuring it's a list of course objects.
    Filters out unexpected fields from each course object based on the CourseCreate schema.
    Returns a tuple (parsed_data, error_message).
    If valid, parsed_data is the filtered list and error_message is None.
    If invalid, parsed_data is None and error_message contains the details.
    """
    if not json_string.strip():
        return None, "Input cannot be empty. Please enter course data."

    try:
        parsed_data = json.loads(json_string)
        if not isinstance(parsed_data, list):
            return None, "Input must be a JSON array of course objects (e.g., `[...]`)."

        # Define the expected fields based on CourseCreate schema (simplified for ingestion)
        # These fields should match what your FastAPI /courses/ endpoint expects for CourseCreate
        expected_fields = [
            "title",
            "description",
            "url",
            "instructor",
            "price",
            "currency",
            "difficulty_level",  # Aligned with database model and API schema
            "category",
            "platform",
        ]

        cleaned_courses = []
        for course_obj in parsed_data:
            if not isinstance(course_obj, dict):
                return (
                    None,
                    f"Each item in the JSON array must be a JSON object, but found: {type(course_obj).__name__}.",
                )

            # Create a new dictionary with only the expected fields
            cleaned_course = {}
            for key, value in course_obj.items():
                if key in expected_fields:
                    cleaned_course[key] = value
                else:
                    st.warning(f"Field '{key}' is not expected and will be ignored for course: {course_obj.get('title', 'N/A')}")
            cleaned_courses.append(cleaned_course)

        return cleaned_courses, None
    except json.JSONDecodeError as e:
        return (
            None,
            f"Invalid JSON format. Please check syntax (e.g., missing commas, brackets, or quotes). Error: {e}",
        )
    except Exception as e:
        return (
            None,
            f"An unexpected error occurred during JSON parsing or cleaning: {e}",
        )


# --- Streamlit UI ---
st.title("🎯 Umbra Personalized Learning Platform")
st.markdown("""
**Your Journey, Your Way** 🚀

Welcome to a learning platform that adapts to YOU. Discover courses, build personalized learning paths, 
and achieve your goals at your own pace. Every learner is unique - let's find your perfect learning structure.
""")

# Add a sidebar for user info (placeholder for now)
with st.sidebar:
    st.header("🧭 Your Learning Journey")
    st.info("""
    **Coming Soon:**
    - Personal skill assessment
    - Custom learning paths
    - Progress tracking
    - AI-powered recommendations
    """)

tab1, tab2, tab3, tab4 = st.tabs(["📚 Discover Courses", "➕ Add Course", "🎯 Learning Paths", "ℹ️ About"])

with tab1:
    st.header("Available Courses")

    # Filters and Sorting (simplified)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Filtering")
        filter_title = st.text_input("Filter by Title (exact match)")
        filter_difficulty = st.selectbox(
            "Filter by Difficulty", [None, "Beginner", "Intermediate", "Advanced"], index=0
        )

    with col2:
        st.subheader("Sorting")
        sort_by_options = {"None": None, "Title": "title", "Difficulty": "difficulty"}
        selected_sort_by_display = st.selectbox("Sort By", list(sort_by_options.keys()), index=0)
        selected_sort_by = sort_by_options[selected_sort_by_display]
        sort_order = st.radio("Sort Order", ["asc", "desc"], horizontal=True, index=0)

    # Dynamic filter criteria construction
    current_filter_criteria = {}
    if filter_title:
        current_filter_criteria["title"] = filter_title
    if filter_difficulty:
        current_filter_criteria["difficulty"] = filter_difficulty

    if st.button("Fetch Courses"):
        # Fetch and display courses
        courses = fetch_courses(
            sort_by=selected_sort_by or "",
            sort_order=sort_order,
            filter_criteria=current_filter_criteria,
        )

        if courses:
            st.subheader(f"Total Courses: {len(courses)}")
            for course in courses:
                st.markdown(f"### {course.get('title', 'N/A')}")
                st.write(f"**URL:** {course.get('url', 'N/A')}")
                if course.get("description"):
                    st.write(f"**Description:** {course['description']}")
                if course.get("difficulty_level"):
                    st.write(f"**Difficulty:** {course['difficulty_level']}")
                if course.get("category"):
                    st.write(f"**Category:** {course['category']}")
                st.markdown("---")
        else:
            st.info("No courses found with the current filters and sorting.")

with tab2:
    st.header("Ingest New Course Data")
    with st.expander("Instructions for Ingesting Data"):
        st.markdown(
            """
Enter a JSON array of course objects below. Each course object should match the expected schema (e.g., `title`, `description`, `url`, `difficulty`, `category`).

Example:
```json
[
  {
    "title": "Example Course 1",
    "description": "Description for example course 1.",
    "url": "http://example.com/course1",
    "difficulty": "Beginner",
    "category": "Programming"
  }
]
```
"""
        )

    input_data = st.text_area(
        "Enter Course Data (JSON Array)",
        height=200,
        value="""[
  {
    "title": "FastAPI Essentials (New)",
    "description": "Learn the basics of FastAPI for building web APIs (updated).",
    "url": "http://example.com/fastapi-essentials-new",
    "difficulty": "Intermediate",
    "category": "Web Development"
  }
]""",
    )

    if st.button("Ingest Data"):
        courses_to_ingest, error_message = validate_json_input(input_data)

        if error_message:
            st.error(error_message)
        elif courses_to_ingest:
            result = post_courses(courses_to_ingest)
            if result:
                st.success(f"Successfully ingested {len(result)} courses.")
                st.json(result)
            else:
                st.error("Failed to ingest course.")

with tab3:
    st.header("🎯 Personalized Learning Paths")
    
    st.markdown("""
    **Create Your Learning Journey**
    
    Learning paths help you organize courses in a way that makes sense for YOUR learning style and goals.
    Instead of random course browsing, get a structured approach that adapts to how you learn best.
    """)
    
    # Current functionality
    st.markdown("""
    **🎯 What Learning Paths Offer:**
    - **Personalized Sequences**: Courses arranged based on your skill level and learning preferences
    - **Adaptive Learning**: System learns from your progress and adjusts recommendations
    - **Multiple Learning Styles**: Visual, hands-on, theoretical - choose what works for you
    - **Flexible Pacing**: Learn at your own speed, pause and resume anytime
    - **Smart Recommendations**: AI suggests next courses based on your interests and progress
    """)
    
    # Simple example
    st.subheader("Example: Python Learning Path")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("""
        **Beginner → Intermediate → Advanced**
        
        This path adapts based on:
        - Your current Python knowledge
        - Whether you prefer theory or practice
        - How much time you have available
        - Your specific interests (web dev, data science, etc.)
        """)
        
        # Sample path structure
        path_steps = [
            "🔓 Python Basics (Start here)",
            "🔒 Data Structures (Unlocks after basics)", 
            "🔒 Web Development OR Data Analysis (Choose your path)",
            "🔒 Advanced Projects (Based on your choice)"
        ]
        
        for step in path_steps:
            st.markdown(f"- {step}")
    
    with col2:
        st.markdown("""
        **Your Style**
        
        📊 **Progress**: Tracked
        🎯 **Goals**: Set by you
        ⏱️ **Pace**: Your choice
        🧭 **Direction**: AI-guided
        """)
    
    st.info("💡 **Note**: This platform focuses on personalized learning experiences, not certifications or job guarantees. It's about finding the learning approach that works best for YOU.")


with tab4:
    st.header("About the Umbra Learning Platform: A Technical Deep-Dive")

    st.markdown("""
    This platform is engineered from the ground up using a modern, scalable, and maintainable technology stack. Our architecture is built on the principle of **microservices**, where different parts of the application are independent, communicating over a network. This approach allows for greater flexibility, targeted scaling, and easier maintenance.
    """)

    st.subheader("Backend Deep-Dive (The Engine Room)")
    st.markdown("The backend is a high-performance REST API built with Python.")
    with st.expander("FastAPI Framework"):
        st.markdown(f"""
        - **What it is:** A modern, high-performance web framework for building APIs.
        - **Why we use it:**
            - **Speed:** It's one of the fastest Python frameworks available.
            - **Automatic Interactive Documentation:** It automatically generates interactive API documentation. You can explore this at [http://{APP_HOST}:8000/docs](http://{APP_HOST}:8000/docs).
            - **Asynchronous Support:** It's built to handle many concurrent requests efficiently.
        """)
    with st.expander("Data Persistence & Validation (SQLAlchemy & Pydantic)"):
        st.markdown("""
        - **What they are:** SQLAlchemy is an Object-Relational Mapper (ORM) that translates Python objects into database queries. Pydantic is a data validation library.
        - **Why we use them:** They ensure data integrity and make database interactions safer and more intuitive.
        """)
    with st.expander("Database Migrations (Alembic)"):
        st.markdown("""
        - **What it is:** A database migration tool for SQLAlchemy.
        - **Why we use it:** It allows us to manage database schema changes in a systematic, version-controlled way.
        """)
    with st.expander("Security (JWT & Passlib)"):
        st.markdown("""
        - **What they are:** Libraries for authentication and secure password hashing.
        - **Why we use them:** They ensure that only authenticated users can access sensitive data.
        """)

    st.subheader("Frontend Deep-Dive (The User Experience)")
    with st.expander("Streamlit Framework"):
        st.markdown("""
        - **What it is:** An open-source Python library for creating custom web apps.
        - **Why we use it:** It allows for rapid development of interactive user interfaces directly in Python.
        """)

    st.subheader("Infrastructure & Core Services")
    st.markdown("These are the foundational services that support the entire platform.")
    with st.expander("PostgreSQL Database"):
        st.markdown("""
        - **What it is:** A powerful, open-source object-relational database system.
        - **Why we use it:** It provides a reliable and robust foundation for storing our application's data.
        """)
    with st.expander("RabbitMQ (Message Broker)"):
        st.markdown(f"""
        - **What it is:** A message broker for asynchronous communication.
        - **Why we use it:** It makes our platform more scalable and responsive by offloading long-running tasks. You can view the management UI at [http://{APP_HOST}:15672](http://{APP_HOST}:15672) (credentials: `guest`/`guest`).
        """)
    with st.expander("MLflow (Machine Learning Operations)"):
        st.markdown(f"""
        - **What it is:** A platform to manage the machine learning lifecycle.
        - **Why we use it:** It helps us track experiments and manage our recommendation models. You can view the UI at [http://{APP_HOST}:5000](http://{APP_HOST}:5000).
        """)
    
    st.subheader("Deployment & Operations (DevOps)")
    with st.expander("Docker & Docker Compose"):
        st.markdown("""
        - **What they are:** Tools for containerization and orchestration.
        - **Why we use them:** They ensure our application runs consistently across different environments.
        """)
    with st.expander("Render (Cloud Platform)"):
        st.markdown("""
        - **What it is:** Our cloud provider for hosting the live application.
        - **Why we use it:** It provides a seamless deployment experience and manages our production database. You can visit the live application at [https://umbra-frontend.onrender.com](https://umbra-frontend.onrender.com).
        """)
