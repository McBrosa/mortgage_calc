"""
Playwright regression tests for Mortgage Calculator Pro.
App must be running at http://localhost:8501 before running tests.

Default state on load uses neutral sample values and no extra payment.
"""
from playwright.sync_api import Page, expect


def _wait(page: Page, ms: int = 2000) -> None:
    page.wait_for_timeout(ms)


def _set_extra_monthly_payment(page: Page, amount: str) -> None:
    extra_input = page.get_by_role("spinbutton", name="Extra principal each month")
    extra_input.click(click_count=3)
    extra_input.fill(amount)
    page.get_by_role("button", name="Calculate payment").click()
    _wait(page)


# ── 1. Page load ─────────────────────────────────────────────────────────────

def test_page_loads_with_title(app_page: Page):
    heading = app_page.locator("h1").first
    expect(heading).to_be_visible()
    assert "Mortgage" in heading.text_content()


# ── 2. Input form ────────────────────────────────────────────────────────────

def test_primary_inputs_render_without_opening_sidebar(app_page: Page):
    expect(app_page.get_by_role("spinbutton", name="Loan amount")).to_be_visible()
    expect(app_page.get_by_role("spinbutton", name="Interest rate")).to_be_visible()
    expect(app_page.get_by_role("button", name="Calculate payment")).to_be_visible()


# ── 3. Default metrics ───────────────────────────────────────────────────────

def test_default_metrics_visible(app_page: Page):
    # Base results render even with no extra payment configured.
    metrics = app_page.locator('[data-testid="stMetric"]')
    assert metrics.count() >= 3  # concise payment, interest, and payoff summary


# ── 4. Interactivity ─────────────────────────────────────────────────────────

def test_loan_amount_change_updates_metrics(app_page: Page):
    loan_input = app_page.get_by_role("spinbutton", name="Loan amount")

    # app.py renders metrics in column 1: "Monthly P&I Payment" (first), "Total Interest", "Payoff Date"
    # Changing loan amount directly affects the first metric's value.
    initial = app_page.locator('[data-testid="stMetricValue"]').first.text_content()

    loan_input.click(click_count=3)
    loan_input.fill("200000")
    app_page.get_by_role("button", name="Calculate payment").click()
    _wait(app_page)

    updated = app_page.locator('[data-testid="stMetricValue"]').first.text_content()
    assert initial != updated


# ── 5. Extra payments ────────────────────────────────────────────────────────

def test_extra_monthly_payment_saves_interest(app_page: Page):
    _set_extra_monthly_payment(app_page, "500")
    page_text = app_page.locator("body").text_content()
    assert "Interest saved" in page_text


def test_extra_payment_shows_years_saved(app_page: Page):
    _set_extra_monthly_payment(app_page, "500")
    page_text = app_page.locator("body").text_content()
    assert "Time saved" in page_text


def test_zero_extra_payment_removes_savings_metrics(app_page: Page):
    page_text = app_page.locator("body").text_content()
    # The fresh default has no extra payment, so no savings metrics are shown.
    assert "Time Saved" not in page_text


def test_multiple_one_time_payments_can_be_added_and_removed(app_page: Page):
    app_page.get_by_text("One-time payments", exact=True).click()
    first_payment = app_page.get_by_role("spinbutton", name="Payment 1 amount")
    first_payment.fill("5500")

    app_page.get_by_role("button", name="Add another payment").click()
    _wait(app_page)

    second_payment = app_page.get_by_role("spinbutton", name="Payment 2 amount")
    expect(second_payment).to_be_visible()
    assert first_payment.input_value() == "5500"

    second_payment.fill("2500")
    app_page.get_by_role("button", name="Calculate payment").click()
    _wait(app_page)
    assert "Interest saved" in app_page.locator("body").text_content()

    app_page.get_by_role("button", name="Remove").nth(1).click()
    _wait(app_page)
    expect(app_page.get_by_role("spinbutton", name="Payment 2 amount")).to_have_count(0)


# ── 6. Chart ─────────────────────────────────────────────────────────────────

def test_balance_chart_renders(app_page: Page):
    chart = app_page.locator('[data-testid="stPlotlyChart"]').first
    expect(chart).to_be_visible()


# ── 7. Amortization table ────────────────────────────────────────────────────

def test_amortization_table_renders(app_page: Page):
    app_page.get_by_text("Amortization schedule", exact=True).click()
    _wait(app_page, 500)
    assert app_page.locator('[data-testid="stDataFrame"]').count() > 0


# ── 8. Edge case ─────────────────────────────────────────────────────────────

def test_high_interest_rate_no_crash(app_page: Page):
    rate_input = app_page.get_by_role("spinbutton", name="Interest rate")

    rate_input.click(click_count=3)
    rate_input.fill("15")
    app_page.get_by_role("button", name="Calculate payment").click()
    _wait(app_page)

    # App still shows metrics — no crash
    assert app_page.locator('[data-testid="stMetric"]').count() >= 3


# ── 9. Mobile layout ─────────────────────────────────────────────────────────

def test_mobile_layout_has_no_horizontal_page_scroll(app_page: Page):
    app_page.set_viewport_size({"width": 390, "height": 844})
    app_page.reload()
    app_page.wait_for_load_state("networkidle")
    _wait(app_page)

    expect(app_page.get_by_role("spinbutton", name="Loan amount")).to_be_visible()
    submit = app_page.get_by_role("button", name="Calculate payment")
    expect(submit).to_be_visible()
    assert submit.bounding_box()["height"] >= 44

    estimate = app_page.locator(".section-eyebrow", has_text="Your estimate")
    loan_details = app_page.get_by_role("heading", name="Loan details")
    expect(estimate).to_be_visible()
    expect(loan_details).to_be_visible()
    assert estimate.bounding_box()["y"] < loan_details.bounding_box()["y"]

    widths = app_page.evaluate(
        "() => ({viewport: window.innerWidth, document: document.documentElement.scrollWidth})"
    )
    assert widths["document"] <= widths["viewport"] + 1
