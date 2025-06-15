import sys
import os
import streamlit as st
from frontend.utils import register_user, login_user

# Add the project root to sys.path to allow absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

st.title("🔐 Login to Umbra Platform")
tab1, tab2 = st.tabs(["Register", "Login"])

with tab1:
    st.subheader("Sign Up")
    with st.form("registration_form"):
        new_user_identifier = st.text_input("User ID")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        register_button = st.form_submit_button("Register")

        if register_button:
            if new_password != confirm_password:
                st.error("Passwords do not match.")
            elif len(new_password) < 4:
                st.error("Password must be at least 4 characters.")
            else:
                registration_data = {
                    "user_identifier": new_user_identifier,
                    "password": new_password,
                }
                response = register_user(registration_data)
                if response and response.status_code == 200:
                    st.success("Registration successful! Please log in.")
                    st.balloons()
                else:
                    error_detail = "No detailed error message from backend."
                    try:
                        response_json = response.json()
                        if "detail" in response_json:
                            if isinstance(response_json["detail"], list):
                                error_detail = "; ".join(
                                    [str(e) for e in response_json["detail"]]
                                )
                            else:
                                error_detail = response_json["detail"]
                        elif "message" in response_json:
                            error_detail = response_json["message"]
                        else:
                            error_detail = str(response_json)
                    except Exception:
                        error_detail = getattr(response, "text", str(response))
                    st.error(f"Registration failed: {error_detail}")

with tab2:
    st.subheader("Login")
    with st.form("login_form"):
        login_user_identifier = st.text_input("User ID", key="login_user_id")
        login_password = st.text_input("Password", type="password", key="login_pwd")
        login_submit = st.form_submit_button("Login")

        if login_submit:
            if login_user_identifier and login_password:
                with st.spinner("Logging in..."):
                    token_response = login_user(login_user_identifier, login_password)
                    if token_response:
                        st.success("Login successful!")
                        st.session_state["access_token"] = token_response[
                            "access_token"
                        ]
                        st.session_state["token_type"] = token_response["token_type"]
                        st.session_state["logged_in"] = True
                        st.session_state["user_identifier"] = login_user_identifier
                        st.switch_page("pages/2_Ingest_Course_Data.py")
                    else:
                        st.error("Login failed. Check your credentials.")
            else:
                st.error("Please enter both User ID and Password.")
