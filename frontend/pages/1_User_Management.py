import streamlit as st
from frontend.utils import register_user, login_user
import json

# Initialize session state for active tab if not already set
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Register"

st.title("📚 Umbra Educational Data Platform")
st.markdown("""
Welcome to the Umbra Educational Data Platform frontend. 
Use this application to ingest new course data, browse existing courses, and get recommendations.
""")

st.header("User Management")

# Use st.session_state to control the active tab
tab1, tab2 = st.tabs(["Register", "Login"])

with tab1:
    st.subheader("New Journey: Sign Up")
    with st.form("registration_form"):
        st.markdown("""
        Ready to explore? Create your account. 
        Your data is safe with us, no digital dragons allowed!
        """)
        new_user_identifier = st.text_input("Your Unique Tag (User ID)")
        new_password = st.text_input("Your Secret Code (Password)", type="password")
        confirm_password = st.text_input("Repeat Secret Code", type="password")
        register_button = st.form_submit_button("Join the Adventure!")

        if register_button:
            if new_password != confirm_password:
                st.error("Your secret codes don't match! Double-check your entry.")
            elif len(new_password) < 4:
                st.error("Password too short! Needs at least 4 characters for proper safeguarding.")
            else:
                # Call the backend registration endpoint
                registration_data = {"user_identifier": new_user_identifier, "password": new_password}
                response = register_user(registration_data)

                if response and response.status_code == 200:
                    st.success("Welcome, explorer! Your account is ready. Let the insights flow!")
                    st.balloons()
                    # Set session state to switch to Login tab
                    st.session_state.active_tab = "Login"
                    st.experimental_rerun() # Rerun to apply the tab change
                else:
                    error_detail = "No detailed error message from backend."
                    try:
                        response_json = response.json()
                        if "detail" in response_json:
                            if isinstance(response_json["detail"], list):
                                # Handle Pydantic validation errors which are often lists of dicts
                                error_detail = "; ".join([str(e) for e in response_json["detail"]])
                            else:
                                error_detail = response_json["detail"]
                        elif "message" in response_json:
                            error_detail = response_json["message"]
                        else:
                            error_detail = str(response_json) # Fallback to full JSON if no detail/message
                    except json.JSONDecodeError:
                        error_detail = response.text # If not JSON, show raw text
                    except Exception as e:
                        error_detail = f"Failed to parse error response: {e}"
                    st.error(f"Sign-up Mishap: {response.status_code} - {error_detail}")

with tab2:
    st.subheader("Welcome Back, Voyager!")
    with st.form("login_form"):
        st.markdown("""
        Re-enter the data stream. 
        Only authorized voyagers allowed past this point.
        """)
        login_user_identifier = st.text_input("Your Unique Tag (User ID)")
        login_password = st.text_input("Your Secret Code (Password)", type="password")
        login_submit = st.form_submit_button("Embark!")

        if login_submit:
            if login_user_identifier and login_password:
                with st.spinner("Charting your course..."):
                    token_response = login_user(login_user_identifier, login_password)
                    if token_response:
                        st.success("Course charted! You're back in the data flow. Enjoy your journey.")
                        # Store token in session state for authenticated requests
                        st.session_state["access_token"] = token_response["access_token"]
                        st.session_state["token_type"] = token_response["token_type"]
                        st.session_state["logged_in"] = True # Indicate user is logged in
                        st.session_state["user_identifier"] = login_user_identifier
                        st.switch_page("pages/2_Ingest_Course_Data.py")
            else:
                st.error("Coordinates missing! Please provide both your User ID and Secret Code.")