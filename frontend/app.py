import streamlit as st
import sys
import os

# Add the project root to sys.path to allow absolute imports from 'frontend'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

st.set_page_config(page_title="Umbra Educational Data Platform", layout="wide")

st.title("📚 Umbra Educational Data Platform")
st.markdown("""
Welcome to the Umbra Educational Data Platform. Please use the sidebar to navigate to different sections of the application:

*   **User Management:** Register or log in to your account.
*   **Ingest Course Data:** Add new course information to the platform.
*   **Browse Courses:** View existing courses and search for specific ones.
""")

st.info("To get started, please select a page from the sidebar.") 

