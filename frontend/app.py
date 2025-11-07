import json
import os
from typing import Any, Dict, Optional

import requests
import streamlit as st

API_BASE = os.getenv("BACKEND_URL", "http://localhost:8000/api")


def api_request(
    method: str,
    path: str,
    token: Optional[str] = None,
    json_payload: Optional[Dict[str, Any]] = None,
) -> requests.Response:
    url = f"{API_BASE}{path}"
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.request(method, url, headers=headers, json=json_payload, timeout=30)
    return response


def ensure_session_state() -> None:
    for key, default in {
        "access_token": None,
        "refresh_token": None,
        "user": None,
        "agents_cache": [],
        "experiments_cache": [],
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default


def handle_login(email: str, password: str) -> bool:
    response = api_request("POST", "/auth/login", json_payload={"email": email, "password": password})
    if response.status_code == 200:
        tokens = response.json()
        st.session_state.access_token = tokens["access_token"]
        st.session_state.refresh_token = tokens["refresh_token"]
        load_current_user()
        st.success("Logged in successfully.")
        return True
    st.error(response.json().get("detail", "Login failed"))
    return False


def handle_register(username: str, email: str, password: str) -> bool:
    response = api_request(
        "POST",
        "/auth/register",
        json_payload={
            "username": username,
            "email": email,
            "password": password,
            "preferences": {},
        },
    )
    if response.status_code == 201:
        st.success("Registration successful. You can now log in.")
        return True
    detail = response.json().get("detail", "Registration failed")
    st.error(detail)
    return False


def refresh_access_token() -> bool:
    if not st.session_state.refresh_token:
        return False
    response = api_request(
        "POST",
        "/auth/refresh",
        json_payload={"refresh_token": st.session_state.refresh_token},
    )
    if response.status_code == 200:
        tokens = response.json()
        st.session_state.access_token = tokens["access_token"]
        st.session_state.refresh_token = tokens["refresh_token"]
        return True
    return False


def authorized_request(method: str, path: str, payload: Optional[Dict[str, Any]] = None):
    response = api_request(method, path, st.session_state.access_token, payload)
    if response.status_code == 401 and refresh_access_token():
        response = api_request(method, path, st.session_state.access_token, payload)
    if response.status_code >= 400:
        detail = response.json().get("detail", response.text)
        st.error(f"Request failed: {detail}")
    return response


def load_current_user() -> None:
    if not st.session_state.access_token:
        return
    response = authorized_request("GET", "/users/me")
    if response and response.status_code == 200:
        st.session_state.user = response.json()


def load_agents() -> None:
    response = authorized_request("GET", "/agents/")
    if response and response.status_code == 200:
        st.session_state.agents_cache = response.json()


def load_experiments() -> None:
    response = authorized_request("GET", "/experiments/")
    if response and response.status_code == 200:
        st.session_state.experiments_cache = response.json()


def render_sidebar():
    st.sidebar.title("PerplexiPlay")
    if st.session_state.user:
        st.sidebar.markdown(f"**{st.session_state.user['username']}**")
        if st.sidebar.button("Logout"):
            authorized_request(
                "POST", "/auth/logout", {"refresh_token": st.session_state.refresh_token}
            )
            st.session_state.access_token = None
            st.session_state.refresh_token = None
            st.session_state.user = None
            st.session_state.agents_cache = []
            st.session_state.experiments_cache = []
            st.experimental_rerun()
    else:
        st.sidebar.info("Sign in to manage agents and experiments.")


def render_auth_forms():
    tabs = st.tabs(["Login", "Register"])
    with tabs[0]:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                handle_login(email, password)
    with tabs[1]:
        with st.form("register_form"):
            username = st.text_input("Username")
            email = st.text_input("Email", key="register_email")
            password = st.text_input("Password", type="password", key="register_password")
            submitted = st.form_submit_button("Register")
            if submitted:
                handle_register(username, email, password)


def render_agent_section():
    st.header("Agent Configurations")
    load_agents()
    if st.session_state.agents_cache:
        for agent in st.session_state.agents_cache:
            with st.expander(agent["name"], expanded=False):
                st.write(f"Framework: `{agent['framework']}`")
                st.write(agent.get("description", ""))
                st.json(agent.get("parameters", {}))
    else:
        st.info("No agents yet.")

    st.subheader("Create Agent")
    with st.form("create_agent_form"):
        name = st.text_input("Agent Name")
        framework = st.selectbox("Framework", ["crewai", "langchain", "openai"])
        description = st.text_area("Description", "")
        params_json = st.text_area("Parameters (JSON)", '{"temperature": 0.5}')
        submitted = st.form_submit_button("Create Agent")
        if submitted:
            try:
                parameters = json.loads(params_json) if params_json else {}
            except json.JSONDecodeError:
                st.error("Parameters must be valid JSON.")
            else:
                response = authorized_request(
                    "POST",
                    "/agents/",
                    {
                        "name": name,
                        "framework": framework,
                        "description": description or None,
                        "parameters": parameters,
                    },
                )
                if response and response.status_code == 201:
                    st.success("Agent created.")
                    load_agents()
                    st.experimental_rerun()


def render_experiment_section():
    st.header("Experiments")
    load_agents()
    load_experiments()

    if st.session_state.experiments_cache:
        for exp in st.session_state.experiments_cache:
            with st.expander(exp["name"], expanded=False):
                st.write(f"Status: `{exp['status']}`")
                if exp.get("result_payload"):
                    st.json(exp["result_payload"])
                if exp.get("error_message"):
                    st.error(exp["error_message"])
    else:
        st.info("No experiments recorded.")

    st.subheader("Run Experiment")
    with st.form("experiment_form"):
        name = st.text_input("Experiment Name")
        agents = st.session_state.agents_cache or []
        agent_options = {a["name"]: a["id"] for a in agents}
        selected_agent = st.selectbox("Agent", list(agent_options.keys())) if agents else None
        input_json = st.text_area("Input Payload (JSON)", '{"prompt": "Hello world"}')
        submitted = st.form_submit_button("Run Experiment")
        if submitted:
            try:
                payload = json.loads(input_json) if input_json else {}
            except json.JSONDecodeError:
                st.error("Input payload must be valid JSON.")
            else:
                response = authorized_request(
                    "POST",
                    "/experiments/",
                    {
                        "name": name,
                        "agent_id": agent_options.get(selected_agent) if selected_agent else None,
                        "input_payload": payload,
                    },
                )
                if response and response.status_code == 201:
                    st.success("Experiment executed.")
                    load_experiments()
                    st.experimental_rerun()


def render_dashboard():
    st.title("PerplexiPlay – Agent Playground & Testing")
    st.caption("Build, evaluate, and benchmark agentic AI workflows.")
    stats = st.columns(3)
    stats[0].metric("Agents", len(st.session_state.agents_cache))
    stats[1].metric(
        "Experiments", len(st.session_state.experiments_cache)
    )
    completed = [
        exp for exp in st.session_state.experiments_cache if exp["status"] == "completed"
    ]
    stats[2].metric("Completed Runs", len(completed))


def main():
    st.set_page_config(page_title="PerplexiPlay", page_icon="🧠", layout="wide")
    ensure_session_state()
    render_sidebar()

    if not st.session_state.user:
        render_auth_forms()
        return

    load_agents()
    load_experiments()

    pages = {
        "Dashboard": render_dashboard,
        "Agents": render_agent_section,
        "Experiments": render_experiment_section,
    }
    selection = st.sidebar.radio("Navigate", list(pages.keys()))
    pages[selection]()


if __name__ == "__main__":
    main()
