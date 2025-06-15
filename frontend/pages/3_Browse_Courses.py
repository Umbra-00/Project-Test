import streamlit as st
from frontend.utils import get_all_courses, get_course_by_url

# Initialize session state for logged_in if not already set
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.header("Browse All Courses")

# Conditional warning for guests
if not st.session_state.logged_in:
    st.info(
        "Guest mode: Your browsing is temporary. Registered users' insights are saved. Ready to explore?"
    )

if st.button("Fetch All Courses"):
    courses = get_all_courses()
    if courses:
        st.success(f"Found {len(courses)} courses.")
        st.json(courses)
        for i, course in enumerate(courses):
            st.subheader(f"Course {i+1}: {course.get('title', 'N/A')}")
            st.write(f"**Instructor:** {course.get('instructor', 'N/A')}")
            st.write(f"**Difficulty:** {course.get('difficulty', 'N/A')}")
            st.write(f"**Category:** {course.get('category', 'N/A')}")
            st.write(f"**Platform:** {course.get('platform', 'N/A')}")
            st.write(
                f"**Price:** {course.get('price', 'N/A')} {course.get('currency', 'N/A')}"
            )
            st.write(f"**URL:** {course.get('url', 'N/A')}")
            st.write(f"**Description:** {course.get('description', 'N/A')}")
            st.markdown("---")
    else:
        st.info("No courses found in the database.")

st.header("Get Course by URL")
selected_course_url = st.text_input(
    "Enter Course URL", "http://example.com/fastapi-essentials"
)
if st.button("Fetch Course by URL"):
    if selected_course_url:
        course = get_course_by_url(selected_course_url)
        if course:
            st.success(f"Found course: {course.get('title', 'N/A')}")
            st.json(course)
    else:
        st.warning("Please enter a course URL.")

st.header("Get Course Recommendations")
if st.session_state.get("logged_in"):
    user_id = st.session_state.get("user_identifier")
    course_url = st.text_input(
        "Enter a course URL you liked for recommendations",
        "http://example.com/fastapi-essentials",
    )
    num_recs = st.number_input(
        "Number of recommendations", min_value=1, max_value=10, value=3
    )
    if st.button("Get Recommendations"):
        from frontend.utils import get_recommendations

        recs = get_recommendations(
            user_id=user_id,
            course_history_urls=[course_url],
            num_recommendations=num_recs,
        )
        if recs:
            st.success(f"Found {len(recs)} recommendations:")
            for rec in recs:
                st.write(f"**{rec.get('title', 'N/A')}** - {rec.get('url', 'N/A')}")
                st.write(f"Description: {rec.get('description', 'N/A')}")
                st.markdown("---")
        else:
            st.info("No recommendations found for this course.")
else:
    st.info("Login to get personalized recommendations.")
