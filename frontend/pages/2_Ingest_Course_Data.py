import streamlit as st
from frontend.utils import post_courses, validate_json_input

# Initialize session state for logged_in if not already set
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.header("Ingest New Course Data")
with st.expander("Instructions for Ingesting Data"):
    st.markdown(
        """
Enter a JSON array of course objects below. Each course object should match the `CourseCreate` schema:
```json
[
  {
    "title": "Example Course 1",
    "description": "Description for example course 1.",
    "instructor": "Dr. John Doe",
    "url": "http://example.com/course1",
    "price": 100.00,
    "currency": "USD",
    "difficulty": "Beginner",
    "category": "Programming",
    "platform": "Example Platform"
  },
  {
    "title": "Example Course 2",
    "description": "Description for example course 2.",
    "instructor": "Prof. Jane Smith",
    "url": "http://example.com/course2",
    "price": 150.00,
    "currency": "USD",
    "difficulty": "Intermediate",
    "category": "Data Science",
    "platform": "Another Platform"
  }
]
```    """
    )

input_data = st.text_area(
    "Enter Course Data (JSON Array)",
    height=200,
    value="""[
  {
    "title": "FastAPI Essentials",
    "description": "Learn the basics of FastAPI for building web APIs.",
    "instructor": "AI Assistant",
    "url": "http://example.com/fastapi-essentials",
    "price": 49.99,
    "currency": "USD",
    "difficulty": "Beginner",
    "category": "Web Development",
    "platform": "Umbra Academy"
  }
]""",
)

# Conditional warning and button
if not st.session_state.logged_in:
    st.info(
        "Heads up, guest! Data added here is temporary. Registered users' contributions are saved. Proceed anyway?"
    )
    proceed_button = st.button("Proceed Anyway")
else:
    proceed_button = st.button("Ingest Data")

if proceed_button:
    courses_to_ingest, error_message = validate_json_input(input_data)

    if error_message:
        st.error(error_message)
    elif courses_to_ingest:
        result = post_courses(courses_to_ingest)
        if result:
            st.success(f"Successfully ingested {len(result)} courses.")
