import streamlit as st
import requests
import json
import urllib.parse  # For URL encoding
import os

# --- Configuration ---
# Get backend URL from Render environment variable or use local default
backend_url = os.getenv("BACKEND_URL", "localhost:8000")

# Convert hostport format to full URL
if backend_url.startswith("http://") or backend_url.startswith("https://"):
    FASTAPI_BASE_URL = backend_url
else:
    # For Render deployment, use https for external services
    if "onrender.com" in backend_url:
        FASTAPI_BASE_URL = f"https://{backend_url}"
    else:
        # For local development
        FASTAPI_BASE_URL = f"http://{backend_url}"

API_URL = f"{FASTAPI_BASE_URL}/api/v1"

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
            f"{FASTAPI_BASE_URL}/courses/", params=params, timeout=(10, 10)
        )
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching courses: {e}")
        return []

def post_courses(course_data: list):
    url = f"{FASTAPI_BASE_URL}/courses/"
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
        st.error(
            f"HTTP Error: {e.response.status_code} - {e.response.json().get('detail', 'Unknown error')}"
        )
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during POST: {e}")
        return None

def get_course_by_url(course_url: str):
    # URL-encode the course_url to handle special characters correctly in the path
    encoded_url = urllib.parse.quote(course_url, safe='')
    url = f"{FASTAPI_BASE_URL}/courses/{encoded_url}"
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
            st.error(
                f"HTTP Error: {e.response.status_code} - {e.response.json().get('detail', 'Unknown error')}"
            )
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
            "difficulty", # Changed from difficulty_level to difficulty to match CourseCreate schema based on prior discussions
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

tab1, tab2, tab3 = st.tabs(["📚 Discover Courses", "➕ Add Course", "🎯 Learning Paths"])

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
                if course.get("difficulty"):
                    st.write(f"**Difficulty:** {course['difficulty']}")
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
    
    Learning paths are structured sequences of courses designed to help you achieve specific goals.
    Whether you want to become a data scientist, web developer, or master a new skill, 
    we'll help you create the perfect roadmap.
    """)
    
    # Placeholder for learning path functionality
    st.info("🚧 **Coming Soon!** 🚧")
    
    with st.expander("Preview: What Learning Paths Will Offer"):
        st.markdown("""
        **🎯 Goal-Oriented Paths:**
        - Career transition paths (e.g., "Marketing to Data Science")
        - Skill building paths (e.g., "Complete Python Mastery")
        - Project-based paths (e.g., "Build Your First Web App")
        
        **🧠 AI-Powered Personalization:**
        - Assess your current skill level
        - Recommend optimal learning sequence
        - Adapt difficulty based on your progress
        - Suggest alternative routes when you struggle
        
        **📊 Progress Tracking:**
        - Visual progress indicators
        - Milestone celebrations
        - Time estimates and planning tools
        - Skill portfolio building
        
        **👥 Community Features:**
        - Study groups for path participants
        - Peer progress sharing
        - Mentor connections
        - Success story sharing
        """)
    
    # Sample learning path preview
    st.subheader("Example Learning Path: Data Science Fundamentals")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **Path Overview:**
        Transform from beginner to confident data scientist in 12 weeks
        
        **Prerequisites:** Basic math knowledge
        **Estimated Time:** 8-10 hours/week
        **Difficulty:** Beginner to Intermediate
        """)
        
        # Sample path structure
        path_steps = [
            {"step": 1, "title": "Python Fundamentals", "duration": "2 weeks", "status": "available"},
            {"step": 2, "title": "Data Manipulation with Pandas", "duration": "2 weeks", "status": "locked"},
            {"step": 3, "title": "Data Visualization", "duration": "2 weeks", "status": "locked"},
            {"step": 4, "title": "Statistics for Data Science", "duration": "2 weeks", "status": "locked"},
            {"step": 5, "title": "Machine Learning Basics", "duration": "3 weeks", "status": "locked"},
            {"step": 6, "title": "Capstone Project", "duration": "1 week", "status": "locked"},
        ]
        
        for step in path_steps:
            status_emoji = "✅" if step["status"] == "completed" else "🔓" if step["status"] == "available" else "🔒"
            st.markdown(f"{status_emoji} **Step {step['step']}:** {step['title']} *({step['duration']})*")
    
    with col2:
        st.markdown("""
        **Your Progress**
        
        📊 **0% Complete**
        
        🎯 **Next Up:**
        Python Fundamentals
        
        ⏱️ **Time Investment:**
        8-10 hrs/week
        
        🏆 **On Completion:**
        - Portfolio project
        - Certificate
        - Job-ready skills
        """)
        
        if st.button("Start This Path", type="primary"):
            st.success("🎉 Welcome to your Data Science journey! This feature will be available soon.")
