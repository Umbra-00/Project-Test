import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Configuration
if os.getenv("RENDER"):
    FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "https://umbra-backend.onrender.com")
elif os.getenv("BACKEND_URL"):
    FASTAPI_BASE_URL = os.getenv("BACKEND_URL")
else:
    FASTAPI_BASE_URL = "http://localhost:8000"

API_URL = f"{FASTAPI_BASE_URL}/api/v1"

# Page configuration
st.set_page_config(
    page_title="Umbra Personalized Learning Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_token' not in st.session_state:
    st.session_state.user_token = None
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = None

# Helper functions
def api_call(endpoint, method="GET", data=None, headers=None):
    """Make API calls with proper error handling"""
    try:
        full_url = f"{API_URL}{endpoint}"
        if headers is None:
            headers = {}
        
        if st.session_state.user_token:
            headers["Authorization"] = f"Bearer {st.session_state.user_token}"
        
        if method == "GET":
            response = requests.get(full_url, headers=headers, timeout=10)
        elif method == "POST":
            headers["Content-Type"] = "application/json"
            response = requests.post(full_url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            headers["Content-Type"] = "application/json"
            response = requests.put(full_url, headers=headers, json=data, timeout=10)
        
        response.raise_for_status()
        return response.json(), True
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None, False
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None, False

def logout():
    """Logout user and clear session state"""
    st.session_state.authenticated = False
    st.session_state.user_token = None
    st.session_state.user_profile = None
    st.rerun()

def register_user(user_data):
    """Register a new user"""
    data, success = api_call("/register", method="POST", data=user_data)
    return data, success

def login_user(username, password):
    """Login user and get token"""
    data = {"username": username, "password": password}
    response, success = api_call("/token", method="POST", data=data)
    
    if success and response:
        st.session_state.user_token = response.get("access_token")
        st.session_state.authenticated = True
        return True
    return False

def get_user_dashboard():
    """Get user dashboard data"""
    data, success = api_call("/businesses/user-analytics")
    return data if success else None

def get_personalized_recommendations():
    """Get personalized course recommendations"""
    data, success = api_call("/businesses/personalized-dataset")
    return data if success else None

def get_learning_insights():
    """Get learning insights for user"""
    data, success = api_call("/businesses/learning-insights")
    return data if success else None

def record_interaction(interaction_type, content_id=None, details=None):
    """Record user interaction"""
    data = {
        "interaction_type": interaction_type,
        "content_id": content_id,
        "details": details
    }
    api_call("/businesses/record-interaction", method="POST", data=data)

# Authentication UI
def show_auth_page():
    """Display authentication page"""
    st.title("🎯 Welcome to Umbra Personalized Learning Platform")
    
    st.markdown("""
    **Discover, Learn, and Grow with Personalized Education**
    
    Transform your learning journey with AI-powered recommendations, 
    adaptive learning paths, and comprehensive progress tracking.
    """)
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        st.header("Login to Your Account")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if username and password:
                    if login_user(username, password):
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please enter both username and password")
    
    with tab2:
        st.header("Create Your Account")
        
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                reg_username = st.text_input("Username", placeholder="Choose a unique username")
                reg_password = st.text_input("Password", type="password", placeholder="Create a secure password")
                learning_goals = st.text_area("Learning Goals", placeholder="What do you want to achieve?")
                
            with col2:
                skill_level = st.selectbox("Current Skill Level", ["beginner", "intermediate", "advanced"])
                learning_style = st.selectbox("Preferred Learning Style", ["visual", "auditory", "kinesthetic", "mixed"])
                time_availability = st.selectbox("Time Availability", ["low", "medium", "high"])
                career_field = st.text_input("Career Field", placeholder="e.g., Software Development, Data Science")
            
            submitted = st.form_submit_button("Register", use_container_width=True)
            
            if submitted:
                if reg_username and reg_password:
                    user_data = {
                        "user_identifier": reg_username,
                        "password": reg_password,
                        "learning_goals": learning_goals,
                        "current_skill_level": skill_level,
                        "preferred_learning_style": learning_style,
                        "time_availability": time_availability,
                        "career_field": career_field
                    }
                    
                    result, success = register_user(user_data)
                    if success:
                        st.success("Registration successful! Please login with your credentials.")
                    else:
                        st.error("Registration failed. Please try again.")
                else:
                    st.error("Please enter both username and password")

# Main dashboard
def show_dashboard():
    """Display main dashboard for authenticated users"""
    
    # Sidebar
    with st.sidebar:
        st.header("🧭 Navigation")
        
        # User profile info
        dashboard_data = get_user_dashboard()
        if dashboard_data and 'dashboard_data' in dashboard_data:
            user_profile = dashboard_data['dashboard_data']['user_profile']
            st.success(f"Welcome, {user_profile['user_identifier']}!")
            
            # Quick stats
            stats = dashboard_data['dashboard_data']['learning_stats']
            st.metric("Courses Enrolled", stats['total_courses'])
            st.metric("Courses Completed", stats['completed_courses'])
            st.metric("Completion Rate", f"{stats['completion_rate']:.1f}%")
            st.metric("Hours Spent", f"{stats['total_time_spent_hours']:.1f}h")
        
        st.divider()
        
        # Navigation
        page = st.selectbox("Choose a page:", [
            "📊 Dashboard",
            "🎯 Personalized Recommendations", 
            "📚 Course Discovery",
            "📈 Learning Analytics",
            "⚙️ Profile Settings"
        ])
        
        st.divider()
        
        if st.button("Logout", use_container_width=True):
            logout()
    
    # Main content area
    if page == "📊 Dashboard":
        show_dashboard_page()
    elif page == "🎯 Personalized Recommendations":
        show_recommendations_page()
    elif page == "📚 Course Discovery":
        show_course_discovery_page()
    elif page == "📈 Learning Analytics":
        show_analytics_page()
    elif page == "⚙️ Profile Settings":
        show_profile_settings_page()

def show_dashboard_page():
    """Display main dashboard page"""
    st.title("📊 Your Learning Dashboard")
    
    record_interaction("dashboard_view")
    
    dashboard_data = get_user_dashboard()
    if not dashboard_data:
        st.error("Unable to load dashboard data")
        return
    
    user_profile = dashboard_data['dashboard_data']['user_profile']
    stats = dashboard_data['dashboard_data']['learning_stats']
    recent_progress = dashboard_data['dashboard_data']['recent_progress']
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Courses", 
            stats['total_courses'],
            help="Total number of courses you've enrolled in"
        )
    
    with col2:
        st.metric(
            "Completed", 
            stats['completed_courses'],
            help="Number of courses you've completed"
        )
    
    with col3:
        st.metric(
            "Completion Rate", 
            f"{stats['completion_rate']:.1f}%",
            help="Percentage of enrolled courses completed"
        )
    
    with col4:
        st.metric(
            "Learning Hours", 
            f"{stats['total_time_spent_hours']:.1f}h",
            help="Total time spent learning"
        )
    
    # Recent progress
    st.subheader("📈 Recent Learning Progress")
    
    if recent_progress:
        progress_df = pd.DataFrame(recent_progress)
        
        # Create progress chart
        fig = px.bar(
            progress_df, 
            x='course_id', 
            y='progress_percentage',
            title="Progress by Course",
            labels={'course_id': 'Course ID', 'progress_percentage': 'Progress (%)'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Recent progress table
        st.dataframe(progress_df, use_container_width=True)
    else:
        st.info("No learning progress data available yet. Start enrolling in courses to see your progress!")
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Discover Courses", use_container_width=True):
            st.session_state.page = "📚 Course Discovery"
            st.rerun()
    
    with col2:
        if st.button("🎯 Get Recommendations", use_container_width=True):
            st.session_state.page = "🎯 Personalized Recommendations"
            st.rerun()
    
    with col3:
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.page = "📈 Learning Analytics"
            st.rerun()

def show_recommendations_page():
    """Display personalized recommendations page"""
    st.title("🎯 Personalized Recommendations")
    
    record_interaction("recommendations_view")
    
    st.markdown("""
    **AI-Powered Learning Recommendations**
    
    Based on your learning history, preferences, and goals, here are personalized recommendations to accelerate your learning journey.
    """)
    
    dashboard_data = get_user_dashboard()
    if not dashboard_data:
        st.error("Unable to load recommendations")
        return
    
    recommendations = dashboard_data.get('recommendations', [])
    
    if not recommendations:
        st.info("No recommendations available yet. Complete your profile and start learning to get personalized suggestions!")
        return
    
    # Display recommendations
    for i, rec in enumerate(recommendations):
        with st.expander(f"📚 {rec['title']}", expanded=i < 3):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Description:** {rec['description']}")
                st.write(f"**Category:** {rec['category']}")
                st.write(f"**Difficulty:** {rec['difficulty_level']}")
                st.write(f"**Why recommended:** {rec['reason']}")
            
            with col2:
                st.metric("Match Score", f"{rec['match_score']:.1f}")
                if st.button(f"View Course", key=f"view_{i}"):
                    record_interaction("course_view", content_id=rec['id'])
                    st.success(f"Viewing course: {rec['title']}")

def show_course_discovery_page():
    """Display course discovery page"""
    st.title("📚 Course Discovery")
    
    record_interaction("course_discovery_view")
    
    st.markdown("**Explore our comprehensive course catalog**")
    
    # Course filters
    with st.expander("🔍 Filter Courses"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            difficulty_filter = st.selectbox("Difficulty Level", ["All", "beginner", "intermediate", "advanced"])
        
        with col2:
            category_filter = st.text_input("Category", placeholder="e.g., Python, Web Development")
        
        with col3:
            sort_by = st.selectbox("Sort By", ["title", "difficulty", "created_date"])
    
    # Fetch courses (simplified for demo)
    courses_data = [
        {
            "id": 1,
            "title": "Python for Beginners",
            "description": "Learn Python programming from scratch",
            "difficulty_level": "beginner",
            "category": "Programming",
            "instructor": "John Doe",
            "url": "https://example.com/python-beginners"
        },
        {
            "id": 2,
            "title": "Advanced Data Science",
            "description": "Master advanced data science techniques",
            "difficulty_level": "advanced",
            "category": "Data Science",
            "instructor": "Jane Smith",
            "url": "https://example.com/advanced-data-science"
        }
    ]
    
    # Display courses
    for course in courses_data:
        with st.container():
            st.subheader(f"📖 {course['title']}")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(course['description'])
                st.write(f"**Instructor:** {course['instructor']}")
            
            with col2:
                st.write(f"**Difficulty:** {course['difficulty_level']}")
                st.write(f"**Category:** {course['category']}")
            
            with col3:
                if st.button("Enroll", key=f"enroll_{course['id']}"):
                    record_interaction("course_enroll", content_id=course['id'])
                    st.success(f"Enrolled in {course['title']}")
            
            st.divider()

def show_analytics_page():
    """Display learning analytics page"""
    st.title("📈 Learning Analytics")
    
    record_interaction("analytics_view")
    
    insights = get_learning_insights()
    if not insights:
        st.error("Unable to load learning insights")
        return
    
    if "message" in insights:
        st.info(insights["message"])
        
        st.subheader("💡 Getting Started Suggestions")
        for suggestion in insights["suggestions"]:
            st.write(f"• {suggestion}")
        return
    
    # Learning summary
    st.subheader("📊 Learning Summary")
    
    summary = insights["learning_summary"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Courses", summary["total_courses_enrolled"])
        st.metric("Completed Courses", summary["courses_completed"])
        st.metric("Completion Rate", f"{summary['completion_rate']:.1f}%")
    
    with col2:
        st.metric("Total Learning Hours", f"{summary['total_time_spent_hours']:.1f}h")
        st.metric("Average Progress", f"{summary['average_progress']:.1f}%")
        st.metric("Learning Velocity", f"{summary['learning_velocity_courses_per_week']:.2f} courses/week")
    
    # Learning patterns
    st.subheader("🎯 Learning Patterns")
    
    patterns = insights["learning_patterns"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Preferred Difficulty:** {patterns['preferred_difficulty']}")
        st.write(f"**Learning Style:** {patterns['learning_style']}")
    
    with col2:
        st.write(f"**Time Availability:** {patterns['time_availability']}")
        st.write(f"**Career Focus:** {patterns['career_focus']}")
    
    # Recommendations
    st.subheader("💡 Personalized Recommendations")
    
    for rec in insights["recommendations"]:
        st.write(f"• {rec}")

def show_profile_settings_page():
    """Display profile settings page"""
    st.title("⚙️ Profile Settings")
    
    record_interaction("profile_settings_view")
    
    dashboard_data = get_user_dashboard()
    if not dashboard_data:
        st.error("Unable to load profile data")
        return
    
    user_profile = dashboard_data['dashboard_data']['user_profile']
    
    st.subheader("👤 Profile Information")
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Username", value=user_profile['user_identifier'], disabled=True)
            learning_goals = st.text_area("Learning Goals", value=user_profile.get('learning_goals', ''))
            skill_level = st.selectbox(
                "Current Skill Level", 
                ["beginner", "intermediate", "advanced"],
                index=["beginner", "intermediate", "advanced"].index(user_profile.get('current_skill_level', 'beginner'))
            )
        
        with col2:
            learning_style = st.selectbox(
                "Preferred Learning Style", 
                ["visual", "auditory", "kinesthetic", "mixed"],
                index=["visual", "auditory", "kinesthetic", "mixed"].index(user_profile.get('preferred_learning_style', 'mixed'))
            )
            time_availability = st.selectbox(
                "Time Availability", 
                ["low", "medium", "high"],
                index=["low", "medium", "high"].index(user_profile.get('time_availability', 'medium'))
            )
            career_field = st.text_input("Career Field", value=user_profile.get('career_field', ''))
        
        if st.form_submit_button("Update Profile", use_container_width=True):
            update_data = {
                "learning_goals": learning_goals,
                "current_skill_level": skill_level,
                "preferred_learning_style": learning_style,
                "time_availability": time_availability,
                "career_field": career_field
            }
            
            result, success = api_call("/update-profile", method="PUT", data=update_data)
            if success:
                st.success("Profile updated successfully!")
                st.rerun()
            else:
                st.error("Failed to update profile")

# Main app
def main():
    if not st.session_state.authenticated:
        show_auth_page()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()
