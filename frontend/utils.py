import streamlit as st
import requests
import json

# --- Configuration ---
BASE_URL = "http://localhost:8000/api/v1"


# --- Helper Functions for API Calls ---
def post_courses(course_data: list):
    url = f"{BASE_URL}/courses/"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(course_data))
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


def get_all_courses():
    url = f"{BASE_URL}/courses/"
    try:
        response = requests.get(url)
        response.raise_for_status()
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
        st.error(f"An unexpected error occurred during GET all courses: {e}")
        return None


def get_course_by_url(course_url: str):
    url = f"{BASE_URL}/courses/{requests.utils.quote(course_url, safe='')}"  # URL-encode the course_url
    try:
        response = requests.get(url)
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

        # Define the expected fields based on CourseCreate schema
        # These are the fields the backend expects for INGESTION
        expected_fields = [
            "title",
            "description",
            "url",
            "instructor",
            "price",
            "currency",
            "difficulty_level",
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
            cleaned_course = {
                key: value
                for key, value in course_obj.items()
                if key in expected_fields
            }
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


# --- Helper Functions for User API Calls ---
def register_user(user_data: dict):
    url = f"{BASE_URL}/register"  # Changed endpoint to /register
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(user_data))
        response.raise_for_status()
        return response  # Return the full response object
    except requests.exceptions.HTTPError as e:
        # Streamlit handles the error display in the calling page
        return e.response
    except requests.exceptions.ConnectionError:
        st.error(
            "Connection Error: Could not connect to the FastAPI backend. Please ensure the backend is running."
        )
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during registration: {e}")
        return None


def login_user(user_identifier: str, password: str):
    url = f"{BASE_URL}/token"
    # FastAPI's /token endpoint typically expects x-www-form-urlencoded
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    # The 'username' field in form data is used for user_identifier by FastAPI's OAuth2PasswordRequestForm
    login_data = f"username={user_identifier}&password={password}"
    try:
        response = requests.post(url, headers=headers, data=login_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(
            f"Login Error: {e.response.status_code} - {e.response.json().get('detail', 'Unknown error')}"
        )
        return None
    except requests.exceptions.ConnectionError:
        st.error(
            "Connection Error: Could not connect to the FastAPI backend. Please ensure the backend is running."
        )
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during login: {e}")
        return None


def get_recommendations(user_id: int, course_history_urls=None, num_recommendations=5):
    """
    Calls the backend recommendations endpoint and returns recommended courses.
    """
    url = f"{BASE_URL}/recommendations/"
    # Always send user_id as int
    params = [("user_id", int(user_id)), ("num_recommendations", num_recommendations)]
    if course_history_urls:
        # Add each course_history_urls as a repeated query param
        params += [("course_history_urls", url) for url in course_history_urls]
    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching recommendations: {e}")
        return None
