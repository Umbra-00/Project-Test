import streamlit as st
import requests
import json

# --- Configuration ---
FASTAPI_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(layout="wide", page_title="Umbra Educational Data Platform")

# --- Helper Functions ---
def fetch_courses(skip: int = 0, limit: int = 100, sort_by: str = None, sort_order: str = "asc", filter_criteria: dict = None):
    params = {
        "skip": skip,
        "limit": limit,
    }
    if sort_by:
        params["sort_by"] = sort_by
        params["sort_order"] = sort_order
    if filter_criteria:
        params["filter_criteria"] = json.dumps(filter_criteria)

    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/courses/", params=params)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching courses: {e}")
        return []

def post_course(course_data: dict):
    try:
        response = requests.post(f"{FASTAPI_BASE_URL}/courses/", json=[course_data])
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error ingesting course: {e}")
        return None

# --- Streamlit UI ---
st.title("🎓 Umbra Educational Data Platform")
st.markdown("Browse and manage educational course data.")

tab1, tab2 = st.tabs(["Browse Courses", "Ingest New Course"])

with tab1:
    st.header("Available Courses")

    # Filters and Sorting
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.subheader("Filtering")
        filter_title = st.text_input("Filter by Title (contains)") # Implement partial match later
        filter_difficulty = st.selectbox("Filter by Difficulty", [None, "Beginner", "Intermediate", "Advanced"]) # Example
        filter_category = st.text_input("Filter by Category") # Example

    with col2:
        st.subheader("Sorting")
        sort_by_options = {"None": None, "Title": "title", "Difficulty": "difficulty"}
        selected_sort_by_display = st.selectbox("Sort By", list(sort_by_options.keys()))
        selected_sort_by = sort_by_options[selected_sort_by_display]
        sort_order = st.radio("Sort Order", ["asc", "desc"], horizontal=True, index=0)

    # Dynamic filter criteria construction
    current_filter_criteria = {}
    if filter_title:
        # Note: Backend currently supports exact match. For partial match,
        # the backend get_courses function would need to be enhanced.
        current_filter_criteria["title"] = filter_title
    if filter_difficulty:
        current_filter_criteria["difficulty"] = filter_difficulty
    if filter_category:
        current_filter_criteria["category"] = filter_category

    # Fetch and display courses
    courses = fetch_courses(
        sort_by=selected_sort_by,
        sort_order=sort_order,
        filter_criteria=current_filter_criteria if current_filter_criteria else None
    )

    if courses:
        st.subheader(f"Total Courses: {len(courses)}")
        for course in courses:
            st.markdown(f"### {course['title']}")
            st.write(f"**URL:** {course['url']}")
            if course.get('description'):
                st.write(f"**Description:** {course['description']}")
            if course.get('difficulty'):
                st.write(f"**Difficulty:** {course['difficulty']}")
            if course.get('category'):
                st.write(f"**Category:** {course['category']}")
            st.markdown("--- ")
    else:
        st.info("No courses found with the current filters and sorting.")

with tab2:
    st.header("Ingest New Course Data")
    with st.form("course_ingestion_form"):
        title = st.text_input("Course Title", max_chars=255)
        description = st.text_area("Course Description")
        url = st.text_input("Course URL", max_chars=255)
        difficulty = st.selectbox("Difficulty", [None, "Beginner", "Intermediate", "Advanced"])
        category = st.text_input("Category", max_chars=255)

        submitted = st.form_submit_button("Ingest Course")

        if submitted:
            if not title or not url:
                st.error("Course Title and URL are required.")
            else:
                course_data = {
                    "title": title,
                    "description": description,
                    "url": url,
                    "difficulty": difficulty,
                    "category": category,
                }
                response_data = post_course(course_data)
                if response_data:
                    st.success("Course ingested successfully!")
                    st.json(response_data)
                else:
                    st.error("Failed to ingest course.") 