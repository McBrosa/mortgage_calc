"""
Playwright regression tests for Mortgage Calculator Pro.
App must be running at http://localhost:8501 before running tests.

Default state on load uses neutral sample values and no extra payment.
"""
from playwright.sync_api import Page, expect


def _wait(page: Page, ms: int = 2000) -> None:
    page.wait_for_timeout(ms)


def _set_extra_monthly_payment(page: Page, amount: str) -> None:
    sidebar = page.locator('[data-testid="stSidebar"]')
    extra_input = sidebar.locator('[data-testid="stNumberInput"] input').last
    extra_input.click(click_count=3)
    extra_input.fill(amount)
    extra_input.press("Tab")
    _wait(page)


# ── 1. Page load ─────────────────────────────────────────────────────────────

def test_page_loads_with_title(app_page: Page):
    heading = app_page.locator("h1").first
    expect(heading).to_be_visible()
    assert "Mortgage" in heading.text_content()


# ── 2. Sidebar ───────────────────────────────────────────────────────────────

def test_sidebar_inputs_render(app_page: Page):
    sidebar = app_page.locator('[data-testid="stSidebar"]')
    expect(sidebar).to_be_visible()
    inputs = sidebar.locator('[data-testid="stNumberInput"] input')
    assert inputs.count() >= 3


# ── 3. Default metrics ───────────────────────────────────────────────────────

def test_default_metrics_visible(app_page: Page):
    # Base results render even with no extra payment configured.
    metrics = app_page.locator('[data-testid="stMetric"]')
    assert metrics.count() >= 6  # original (3) + with-extra (3) + savings (2) + payment (3)


# ── 4. Interactivity ─────────────────────────────────────────────────────────

def test_loan_amount_change_updates_metrics(app_page: Page):
    sidebar = app_page.locator('[data-testid="stSidebar"]')
    loan_input = sidebar.locator('[data-testid="stNumberInput"] input').nth(0)

    # app.py renders metrics in column 1: "Monthly P&I Payment" (first), "Total Interest", "Payoff Date"
    # Changing loan amount directly affects the first metric's value.
    initial = app_page.locator('[data-testid="stMetricValue"]').first.text_content()

    loan_input.click(click_count=3)
    loan_input.fill("200000")
    loan_input.press("Tab")
    _wait(app_page)

    updated = app_page.locator('[data-testid="stMetricValue"]').first.text_content()
    assert initial != updated


# ── 5. Extra payments ────────────────────────────────────────────────────────

def test_extra_monthly_payment_saves_interest(app_page: Page):
    _set_extra_monthly_payment(app_page, "500")
    page_text = app_page.locator("body").text_content()
    assert "Interest Saved" in page_text


def test_extra_payment_shows_years_saved(app_page: Page):
    _set_extra_monthly_payment(app_page, "500")
    page_text = app_page.locator("body").text_content()
    assert "Time Saved" in page_text


def test_zero_extra_payment_removes_savings_metrics(app_page: Page):
    page_text = app_page.locator("body").text_content()
    # The fresh default has no extra payment, so no savings metrics are shown.
    assert "Time Saved" not in page_text


# ── 6. Chart ─────────────────────────────────────────────────────────────────

def test_balance_chart_renders(app_page: Page):
    chart = app_page.locator('[data-testid="stPlotlyChart"]').first
    expect(chart).to_be_visible()


# ── 7. Amortization table ────────────────────────────────────────────────────

def test_amortization_table_renders(app_page: Page):
    # Default: first 12 rows shown without toggling
    assert app_page.locator('[data-testid="stDataFrame"]').count() > 0


# ── 8. Edge case ─────────────────────────────────────────────────────────────

def test_high_interest_rate_no_crash(app_page: Page):
    sidebar = app_page.locator('[data-testid="stSidebar"]')
    rate_input = sidebar.locator('[data-testid="stNumberInput"] input').nth(1)

    rate_input.click(click_count=3)
    rate_input.fill("15")
    rate_input.press("Tab")
    _wait(app_page)

    # App still shows metrics — no crash
    assert app_page.locator('[data-testid="stMetric"]').count() >= 3
