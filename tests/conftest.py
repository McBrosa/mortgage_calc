import pytest
import requests
from playwright.sync_api import Page

BASE_URL = "http://localhost:8501"
STREAMLIT_LOAD_WAIT = 3000  # ms — Streamlit needs extra time after networkidle


@pytest.fixture(scope="session", autouse=True)
def ensure_app_running():
    try:
        resp = requests.get(BASE_URL, timeout=5)
        assert resp.status_code == 200, f"App returned {resp.status_code}"
    except requests.exceptions.ConnectionError:
        pytest.fail(
            f"App not running at {BASE_URL}. "
            "Start: .venv/bin/streamlit run app.py --server.port 8501"
        )


@pytest.fixture
def app_page(page: Page):
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(STREAMLIT_LOAD_WAIT)
    yield page
