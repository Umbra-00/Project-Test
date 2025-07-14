import streamlit as st
import requests
import json
import urllib.parse  # For URL encoding
import os
import pandas as pd

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
        "skip": int(skip),
        "limit": int(limit),
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
            courses_df = pd.DataFrame(courses)
            st.dataframe(courses_df, use_container_width=True)
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
    st.header("About the Umbra Learning Platform")
    
    st.markdown("""
    ### Project Purpose
    The Umbra Educational Data Platform is a proof-of-concept showcasing a modern, scalable, and data-driven web application. It's designed to demonstrate proficiency in building robust backend systems, implementing asynchronous task processing, managing the machine learning lifecycle, and deploying a full-stack application using DevOps best practices. 
    
    The core mission is to create a personalized learning experience by analyzing data to adapt to user needs—a common and complex challenge in today's tech landscape.
    """)
    st.divider()

    st.subheader("Technology Rationale")
    st.markdown("""
    The selected technology stack—FastAPI, Pydantic, SQLAlchemy, Streamlit, PostgreSQL, RabbitMQ, Celery, MLflow, Docker, and Render—represents a strategic and modern approach to building a scalable, maintainable, and high-performance application. Each component has been carefully chosen for its specific strengths, ensuring that the application is well-equipped to meet current requirements while remaining flexible for future growth. This report highlights the rationale behind each technology selection and provides a forward-looking perspective on the project's trajectory, ensuring that the project's value is preserved and showcased effectively.

    ### Detailed Analysis
    **Backend & API Layer**

    - **FastAPI**
        FastAPI is chosen for its exceptional speed, intuitive developer experience, and automatic generation of interactive API documentation (OpenAPI/Swagger). Its support for asynchronous programming enables the backend to efficiently handle high-traffic loads and concurrent requests, making it ideal for modern web applications and microservices. This choice ensures that our API is not only performant but also easy to maintain and extend, leveraging its integration with Python's type hints to reduce bugs and enhance developer productivity.
    - **Pydantic**
        Pydantic is integrated for strict data validation and serialization at the API boundaries. This ensures that only well-structured, validated data enters or leaves the system, reducing bugs and preventing data corruption. Pydantic models also serve as the backbone for API documentation and type hints, enhancing maintainability and developer productivity. Its performance, driven by Rust-based validation, makes it a robust choice for ensuring data integrity.
    - **SQLAlchemy/Alembic**
        SQLAlchemy provides a robust Object-Relational Mapping (ORM) layer, allowing for expressive, Pythonic interaction with relational databases. It supports complex queries, relationships, and migrations, which are essential for evolving data schemas. Coupled with Alembic, schema migrations become version-controlled and reproducible, ensuring smooth upgrades and rollbacks. This combination ensures a maintainable and scalable database layer.

    **Frontend**

    - **Streamlit**
        Streamlit is selected for its ability to rapidly build interactive, visually appealing data applications and dashboards using only Python. This minimizes frontend complexity and accelerates prototyping, making it ideal for internal tools, analytics, and data-driven interfaces. Its Python-centric approach ensures that developers can focus on functionality without needing to delve into traditional frontend frameworks, enhancing development speed and accessibility.

    **Data, MLOps, & Asynchronous Processing**

    - **PostgreSQL**
        PostgreSQL is utilized as the primary database for its proven reliability, advanced features, and strong support in the Python ecosystem. It is well-suited for structured, transactional data and scales effectively for enterprise workloads. Its extensibility, including support for JSON and custom data types, makes it a versatile choice for diverse data needs, ensuring robust data management.
    - **RabbitMQ/Celery**
        RabbitMQ and Celery form the backbone of the asynchronous task processing system. By delegating long-running or resource-intensive operations to Celery workers via RabbitMQ message queues, the main API remains responsive and non-blocking, which is crucial for user experience and system scalability. This setup ensures that the application can handle background tasks efficiently without compromising performance, leveraging RabbitMQ's reliable messaging and Celery's distributed task queue capabilities.
    - **MLflow**
        MLflow is integrated to manage the machine learning lifecycle, including experiment tracking, model packaging, and versioning. S3-compatible object storage is used for storing models and artifacts, ensuring durability and scalability in production MLOps workflows. This combination provides a robust framework for managing machine learning operations, supporting reproducibility and scalability.

    **DevOps & Infrastructure**

    - **Docker/Docker Compose**
        Docker and Docker Compose are used to containerize the application, guaranteeing consistency across development, testing, and production environments. This approach eliminates environment drift and simplifies both onboarding and deployment. Docker Compose further streamlines multi-container setups, making it easier to manage complex applications, ensuring portability and collaboration.
    - **Render**
        Render (Platform-as-a-Service) As it is free it is chosen for cloud hosting, automating infrastructure management tasks such as database provisioning, network configuration, and CI/CD deployments. This enables seamless, Git-driven deployments and abstracts away much of the operational overhead, allowing the team to focus on delivering features. Render's simplicity and scalability make it an excellent choice for hosting the application, with built-in security features like TLS certificates and DDoS protection.

    ### Future-Proofing the Stack

    Technology is constantly evolving, and while our current stack is well-suited for the project's needs, we recognize the importance of staying adaptable. As the project grows and new challenges arise, we will periodically review our technology choices to ensure they continue to align with our goals. This proactive approach will allow us to integrate emerging tools and best practices, keeping our application at the forefront of innovation and efficiency, without implying any current deficiencies.
    """)

    st.subheader("Summary Table")
    tech_summary_data = {
        "Layer": [
            "Backend & API", "Backend & API", "Backend & API",
            "Frontend",
            "Data & MLOps", "Data & MLOps", "Data & MLOps",
            "DevOps & Infrastructure", "DevOps & Infrastructure"
        ],
        "Technology": [
            "FastAPI", "Pydantic", "SQLAlchemy/Alembic",
            "Streamlit",
            "PostgreSQL", "RabbitMQ/Celery", "MLflow/S3",
            "Docker/Compose", "Render"
        ],
        "Rationale": [
            "High performance, async support, automatic documentation",
            "Data validation, serialization, type safety, API schema generation",
            "Robust ORM, Pythonic DB access, migrations, maintainable schema evolution",
            "Rapid dashboard/app development, Python-only, minimal frontend complexity",
            "Reliable, scalable, feature-rich relational database",
            "Asynchronous task processing, scalability, non-blocking API",
            "ML lifecycle management, artifact/model storage, production-ready MLOps",
            "Environment consistency, easy deployment, reproducibility",
            "Automated cloud hosting, CI/CD, managed infrastructure"
        ]
    }
    tech_summary_df = pd.DataFrame(tech_summary_data)
    st.table(tech_summary_df)

    st.divider()

    st.subheader("Visual Overview: Architecture & MLOps")
    
    # --- Architecture Diagram ---
    st.markdown("##### Interactive System Architecture")
    graphviz_code = """
    digraph UmbraPlatform {
        graph [rankdir="TB", splines=ortho, bgcolor="white", fontname="sans-serif", label="Umbra Platform: A Modern Microservices Architecture", fontsize=20, fontcolor="#333333", labelloc="t"];
        node [shape=box, style="filled,rounded", fontname="sans-serif", fontcolor="#333333"];
        edge [fontname="sans-serif", fontsize=10, fontcolor="#555555"];

        subgraph cluster_user {
            label = "Presentation Layer";
            bgcolor="#e3f2fd";
            user [label=" End User", shape=circle, style=filled, fillcolor="#fff3e0"];
            frontend [label="Streamlit Frontend\n(Interactive UI & Dashboards)", fillcolor="#bbdefb"];
            user -> frontend [label="Views courses, paths,\nand platform insights"];
        }

        subgraph cluster_backend {
            label = "Core Services & API Gateway";
            bgcolor="#f3e5f5";
            api [label="FastAPI Backend\n(High-Performance API Server)"];
            security [label="Authentication & Authorization\n(JWT, Passlib)", shape=diamond, style=filled, fillcolor="#e1bee7"];
            validation [label="Schema & Data Validation\n(Pydantic)", shape=diamond, style=filled, fillcolor="#e1bee7"];
            api -> security [style=dashed];
            api -> validation [style=dashed];
        }

        subgraph cluster_data {
            label = "Data Persistence Layer";
            bgcolor="#e8f5e9";
            db [label="PostgreSQL Database\n(Relational Data Store)", shape=cylinder, fillcolor="#c8e6c9"];
            orm [label="SQLAlchemy ORM\n(Pythonic DB Interaction)", shape=cds, style=filled, fillcolor="#a5d6a7"];
            migrations [label="Alembic\n(Schema Version Control)", shape=cds, style=filled, fillcolor="#a5d6a7"];
            api -> orm [label="CRUD Operations"];
            orm -> db;
            migrations -> db [label="Evolves Schema"];
        }

        subgraph cluster_async {
            label = "Asynchronous Processing & MLOps";
            bgcolor="#fbe9e7";
            rabbitmq [label="RabbitMQ\n(Task Queue)", fillcolor="#ffccbc"];
            celery [label="Celery Distributed Worker\n(Background Job Processor)", fillcolor="#ffab91"];
            mlflow [label="MLflow Tracking Server\n(Experiment Management)", fillcolor="#ffab91"];
            s3 [label="S3 Object Storage\n(ML Models & Artifacts)", shape=cylinder, fillcolor="#ffccbc"];
            
            api -> rabbitmq [label="Dispatches long-running tasks\n(e.g., new course analysis)"];
            rabbitmq -> celery [label="Delivers task"];
            celery -> db [label="Writes results"];
            celery -> mlflow [label="Logs metrics & params"];
            mlflow -> s3 [label="Manages model lifecycle"];
        }
        
        subgraph cluster_devops {
            label = "Infrastructure & Deployment (DevOps)";
            bgcolor="#eceff1";
            docker [label="Docker & Docker-Compose\n(Containerization)", fillcolor="#cfd8dc"];
            render [label="Render.com\n(PaaS Cloud Hosting)", shape=cloud, fillcolor="#b0bec5"];
            docker -> render [label="Ensures consistent deployment"];
        }

        frontend -> api [label="Secure API Calls (HTTPS/JSON)"];
    }
    """
    st.graphviz_chart(graphviz_code)
    st.caption("This diagram illustrates the microservices-based architecture. Each component is containerized and communicates via well-defined APIs or message queues, ensuring scalability and maintainability with a clear separation of concerns.")

    # --- Platform Snapshots ---
    st.markdown("##### Platform Snapshots")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.image("frontend/assets/backend_docs.png", use_column_width=True)
        st.caption("**Automated API Documentation** powered by FastAPI's OpenAPI integration. This provides a live, interactive 'source of truth' for all endpoints, crucial for efficient development and clear team communication.")
    with col2:
        st.image("frontend/assets/mlFlow.png", use_column_width=True)
        st.caption("**End-to-End MLOps with MLflow** to track experiments, log metrics, and manage model versions. This ensures our recommendation models are reproducible, auditable, and ready for production.")
    with col3:
        st.image("frontend/assets/rabbitmq_ui.png", use_column_width=True)
        st.caption("**Scalable Asynchronous Processing** with RabbitMQ. Decoupling long-running tasks ensures the UI remains responsive under load, a key pattern for building resilient, enterprise-grade systems.")
    
    st.divider()

