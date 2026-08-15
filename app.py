"""Mobile-first Streamlit interface for the mortgage calculator."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from mortgage_calculator import (
    ExtraPayment,
    ExtraPaymentType,
    LoanDetails,
    MortgageCalculator,
)


ONE_TIME_PAYMENT_IDS_KEY = "one_time_payment_ids"
ONE_TIME_PAYMENT_NEXT_ID_KEY = "one_time_payment_next_id"
MAX_ONE_TIME_PAYMENTS = 12


def initialize_one_time_payment_rows() -> list[int]:
    """Create the first stable one-time-payment row for this browser session."""
    if ONE_TIME_PAYMENT_IDS_KEY not in st.session_state:
        st.session_state[ONE_TIME_PAYMENT_IDS_KEY] = [0]
        st.session_state[ONE_TIME_PAYMENT_NEXT_ID_KEY] = 1
    return st.session_state[ONE_TIME_PAYMENT_IDS_KEY]


def add_one_time_payment_row() -> None:
    """Append one stable payment row without disturbing existing widget values."""
    payment_ids = st.session_state[ONE_TIME_PAYMENT_IDS_KEY]
    if len(payment_ids) >= MAX_ONE_TIME_PAYMENTS:
        return
    next_id = st.session_state[ONE_TIME_PAYMENT_NEXT_ID_KEY]
    st.session_state[ONE_TIME_PAYMENT_IDS_KEY] = [*payment_ids, next_id]
    st.session_state[ONE_TIME_PAYMENT_NEXT_ID_KEY] = next_id + 1


def remove_one_time_payment_row(payment_id: int) -> None:
    """Remove a payment row while always leaving one editable row available."""
    payment_ids = st.session_state[ONE_TIME_PAYMENT_IDS_KEY]
    remaining_ids = [existing_id for existing_id in payment_ids if existing_id != payment_id]
    if remaining_ids:
        st.session_state[ONE_TIME_PAYMENT_IDS_KEY] = remaining_ids


@st.cache_data(max_entries=128, show_spinner=False)
def calculate_results(
    loan_details: LoanDetails,
    extra_payments: tuple[ExtraPayment, ...],
) -> dict[str, Any]:
    """Calculate each schedule once and reuse it across all result views."""
    calculator = MortgageCalculator(loan_details)
    original_schedule = calculator.generate_amortization_schedule([])
    selected_schedule = calculator.generate_amortization_schedule(list(extra_payments))

    original_interest = float(original_schedule["interest_payment"].sum())
    selected_interest = float(selected_schedule["interest_payment"].sum())

    return {
        "monthly_pi": calculator.calculate_monthly_payment(),
        "total_monthly": calculator.calculate_total_monthly_payment(),
        "original_schedule": original_schedule,
        "selected_schedule": selected_schedule,
        "original_interest": original_interest,
        "selected_interest": selected_interest,
        "interest_saved": max(0.0, original_interest - selected_interest),
        "months_saved": max(0, len(original_schedule) - len(selected_schedule)),
        "original_payoff": original_schedule.iloc[-1]["date"],
        "selected_payoff": selected_schedule.iloc[-1]["date"],
    }


def apply_styles() -> None:
    """Apply the responsive dashboard visual system."""
    st.markdown(
        """
        <style>
        :root {
            --ink: #122033;
            --muted: #607084;
            --line: #e2e8ee;
            --canvas: #f4f7f8;
            --card: #ffffff;
            --teal: #0b7a70;
            --teal-dark: #075e57;
            --teal-soft: #e7f5f2;
            --mint: #9fe3cf;
        }
        .stApp {
            background:
                radial-gradient(circle at 7% 2%, rgba(159, 227, 207, 0.20), transparent 22rem),
                radial-gradient(circle at 94% 7%, rgba(177, 211, 231, 0.20), transparent 26rem),
                var(--canvas);
            color: var(--ink);
        }
        header[data-testid="stHeader"] { background: transparent; }
        .stMainBlockContainer {
            max-width: 84rem;
            padding-top: 2.25rem;
            padding-bottom: max(3rem, env(safe-area-inset-bottom));
        }
        h1 {
            color: var(--ink);
            font-size: clamp(2.15rem, 4vw, 3.45rem) !important;
            letter-spacing: -0.052em;
            line-height: 1.01 !important;
            margin: 0 0 0.35rem !important;
        }
        h2, h3 {
            color: var(--ink);
            letter-spacing: -0.028em;
        }
        .app-header {
            align-items: flex-end;
            display: flex;
            gap: 1rem;
            justify-content: space-between;
            margin-bottom: 1.65rem;
        }
        .app-heading { max-width: 47rem; }
        .app-kicker {
            align-items: center;
            color: var(--teal);
            display: flex;
            font-size: 0.73rem;
            font-weight: 800;
            gap: 0.45rem;
            letter-spacing: 0.115em;
            margin-bottom: 0.55rem;
            text-transform: uppercase;
        }
        .app-kicker::before {
            background: var(--teal);
            border-radius: 999px;
            content: "";
            height: 0.5rem;
            box-shadow: 0 0 0 0.27rem rgba(11, 122, 112, 0.12);
            width: 0.5rem;
        }
        .app-intro {
            color: var(--muted);
            font-size: 1.04rem;
            line-height: 1.65;
            margin: 0;
            max-width: 44rem;
        }
        .header-note {
            align-items: center;
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(226, 232, 238, 0.92);
            border-radius: 999px;
            color: #425568;
            display: flex;
            flex: 0 0 auto;
            font-size: 0.78rem;
            font-weight: 700;
            gap: 0.45rem;
            margin-bottom: 0.25rem;
            padding: 0.62rem 0.85rem;
        }
        .header-note-icon {
            background: var(--teal-soft);
            border-radius: 999px;
            color: var(--teal);
            display: inline-grid;
            height: 1.35rem;
            place-items: center;
            width: 1.35rem;
        }
        .workspace-left-marker,
        .results-anchor { display: none; }
        [data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.93);
            border: 1px solid var(--line);
            border-radius: 1.4rem;
            box-shadow: 0 1.1rem 3rem rgba(18, 32, 51, 0.07);
            padding: 1.2rem 1.25rem 1.3rem;
        }
        [data-testid="stForm"] h3 {
            font-size: 1.08rem;
            margin-top: 0.3rem;
        }
        [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input,
        [data-testid="stSelectbox"] > div > div {
            background: #f8fafb;
            border-color: #d9e1e7;
            border-radius: 0.7rem;
            min-height: 44px;
            font-size: 0.96rem;
        }
        [data-testid="stNumberInput"] input:focus,
        [data-testid="stDateInput"] input:focus {
            border-color: var(--teal);
            box-shadow: 0 0 0 0.18rem rgba(11, 122, 112, 0.12);
        }
        .stButton button,
        .stDownloadButton button,
        [data-testid="stFormSubmitButton"] button {
            border-radius: 0.75rem;
            min-height: 48px;
            font-weight: 750;
            touch-action: manipulation;
        }
        [data-testid="stFormSubmitButton"] button[kind="primary"] {
            background: linear-gradient(135deg, var(--teal), var(--teal-dark));
            border: 0;
            box-shadow: 0 0.55rem 1.25rem rgba(11, 122, 112, 0.18);
        }
        .one-time-row-title {
            align-items: center;
            color: var(--muted);
            display: flex;
            font-size: 0.72rem;
            font-weight: 800;
            gap: 0.5rem;
            letter-spacing: 0.08em;
            margin: 0.35rem 0 0.15rem;
            text-transform: uppercase;
        }
        .one-time-row-title::after {
            background: var(--line);
            content: "";
            flex: 1;
            height: 1px;
        }
        .st-key-add_one_time_payment button {
            background: var(--teal-soft);
            border: 1px dashed #9acfc4;
            color: var(--teal-dark);
            font-weight: 800;
            margin-top: 0.2rem;
        }
        [class*="st-key-remove_one_time_payment_"] button {
            color: #8a4c4c;
            justify-content: center;
            margin-top: 1.65rem;
            margin-left: auto;
            min-width: 2.75rem;
            padding: 0;
            width: 2.75rem;
        }
        [class*="st-key-remove_one_time_payment_"] [data-testid="stFormSubmitButton"] {
            display: flex;
            justify-content: flex-end;
        }
        [class*="st-key-remove_one_time_payment_"] button p {
            font-size: 0;
            line-height: 0;
            margin: 0;
        }
        [class*="st-key-remove_one_time_payment_"] [data-testid="stIconMaterial"] {
            font-size: 1.15rem;
        }
        [data-testid="stExpander"] summary {
            background: rgba(248, 250, 251, 0.78);
            min-height: 48px;
        }
        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.94);
            border: 1px solid var(--line);
            border-radius: 1rem;
            box-shadow: 0 0.55rem 1.6rem rgba(18, 32, 51, 0.045);
            min-height: 7.1rem;
            padding: 0.9rem 1rem;
        }
        [data-testid="stMetricLabel"] p {
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 700;
        }
        [data-testid="stMetricValue"] {
            color: var(--ink);
            font-size: 1.42rem;
            font-weight: 800;
        }
        .section-eyebrow {
            color: var(--teal);
            font-size: 0.72rem;
            font-weight: 850;
            letter-spacing: 0.105em;
            margin: 0.2rem 0 0.55rem;
            text-transform: uppercase;
        }
        .payment-hero {
            background:
                radial-gradient(circle at 90% 5%, rgba(159, 227, 207, 0.28), transparent 12rem),
                linear-gradient(145deg, #0c8176, #075b55);
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 1.4rem;
            color: white;
            margin: 0 0 0.8rem;
            overflow: hidden;
            padding: 1.25rem 1.35rem 1.15rem;
            position: relative;
            box-shadow: 0 1.15rem 2.8rem rgba(7, 94, 87, 0.20);
        }
        .payment-hero-top {
            align-items: flex-start;
            display: flex;
            gap: 1rem;
            justify-content: space-between;
        }
        .payment-hero-label {
            font-size: 0.78rem;
            font-weight: 750;
            letter-spacing: 0.015em;
            opacity: 0.86;
        }
        .payment-hero-value {
            font-size: clamp(2.4rem, 5vw, 3.35rem);
            font-weight: 850;
            letter-spacing: -0.055em;
            line-height: 1;
            margin: 0.35rem 0 0;
        }
        .payment-hero-value span {
            font-size: 0.9rem;
            font-weight: 700;
            letter-spacing: 0;
            margin-left: 0.3rem;
            opacity: 0.74;
        }
        .hero-plan-badge {
            background: rgba(255, 255, 255, 0.13);
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 999px;
            font-size: 0.73rem;
            font-weight: 750;
            padding: 0.48rem 0.7rem;
            white-space: nowrap;
        }
        .payment-hero-facts {
            border-top: 1px solid rgba(255, 255, 255, 0.16);
            display: grid;
            gap: 0.5rem;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            margin-top: 1.1rem;
            padding-top: 0.9rem;
        }
        .hero-fact-label {
            display: block;
            font-size: 0.68rem;
            opacity: 0.65;
        }
        .hero-fact-value {
            display: block;
            font-size: 0.84rem;
            font-weight: 780;
            margin-top: 0.18rem;
        }
        .strategy-callout {
            align-items: center;
            background: linear-gradient(135deg, #e9f8f3, #f5fbf9);
            border: 1px solid #cdebe2;
            border-radius: 1rem;
            color: #31564f;
            display: flex;
            gap: 0.8rem;
            margin: 0.2rem 0 0.8rem;
            padding: 0.85rem 1rem;
        }
        .strategy-callout-icon {
            background: #d3f0e7;
            border-radius: 0.75rem;
            color: var(--teal);
            display: grid;
            flex: 0 0 2.25rem;
            font-size: 1rem;
            font-weight: 900;
            height: 2.25rem;
            place-items: center;
        }
        .strategy-callout strong {
            color: #163f38;
            display: block;
            font-size: 0.85rem;
        }
        .strategy-callout span {
            display: block;
            font-size: 0.76rem;
            line-height: 1.4;
            margin-top: 0.1rem;
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.90);
            border-color: var(--line) !important;
            border-radius: 1.4rem !important;
            box-shadow: 0 0.85rem 2.4rem rgba(18, 32, 51, 0.055);
        }
        .chart-header {
            align-items: flex-end;
            display: flex;
            gap: 1rem;
            justify-content: space-between;
            margin-bottom: -0.3rem;
        }
        .chart-title {
            color: var(--ink);
            font-size: 1.35rem;
            font-weight: 820;
            letter-spacing: -0.025em;
        }
        .chart-subtitle {
            color: var(--muted);
            font-size: 0.78rem;
            margin-top: 0.15rem;
        }
        .chart-legend-note {
            color: var(--muted);
            font-size: 0.72rem;
            white-space: nowrap;
        }
        div[data-testid="stPlotlyChart"] { overflow: hidden; }

        @media (min-width: 769px) {
            div[data-testid="stHorizontalBlock"]:has(.workspace-left-marker):has(.results-anchor)
            > div[data-testid="stColumn"]:nth-child(2) {
                align-self: flex-start;
                position: sticky;
                top: 1rem;
            }
        }

        @media (max-width: 768px) {
            .stMainBlockContainer {
                padding-left: 0.8rem;
                padding-right: 0.8rem;
                padding-top: 0.85rem;
            }
            .app-header { margin-bottom: 1rem; }
            .header-note { display: none; }
            h1 { font-size: 2.05rem !important; }
            h2 { font-size: 1.4rem !important; }
            h3 { font-size: 1.1rem !important; }
            .app-intro { font-size: 0.92rem; line-height: 1.55; }
            div[data-testid="stHorizontalBlock"]:has(.workspace-left-marker):has(.results-anchor) {
                flex-direction: column !important;
            }
            div[data-testid="stHorizontalBlock"]:has(.workspace-left-marker):has(.results-anchor)
            > div[data-testid="stColumn"]:nth-child(2) {
                order: -1;
            }
            [data-testid="stForm"] {
                border-radius: 1.15rem;
                padding: 0.9rem 0.8rem 1rem;
            }
            div[data-testid="stColumn"]:has(.results-anchor)
            div[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {
                flex-direction: row !important;
                flex-wrap: wrap !important;
                gap: 0.55rem !important;
            }
            div[data-testid="stColumn"]:has(.results-anchor)
            div[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"])
            > div[data-testid="stColumn"] {
                flex: 1 1 calc(50% - 0.3rem) !important;
                min-width: calc(50% - 0.3rem) !important;
                width: auto !important;
            }
            div[data-testid="stColumn"]:has(.results-anchor)
            div[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"])
            > div[data-testid="stColumn"]:last-child {
                flex-basis: 100% !important;
            }
            [data-testid="stMetric"] {
                min-height: 5.55rem;
                padding: 0.65rem 0.75rem;
            }
            [data-testid="stMetricValue"] { font-size: 1.14rem; }
            .section-eyebrow { margin-top: 0; }
            .payment-hero {
                border-radius: 1.15rem;
                padding: 1rem;
            }
            .payment-hero-value { font-size: 2.55rem; }
            .hero-plan-badge { font-size: 0.66rem; }
            .payment-hero-facts { margin-top: 0.85rem; padding-top: 0.75rem; }
            .strategy-callout { margin-bottom: 0.6rem; }
            [class*="st-key-remove_one_time_payment_"] button { margin-top: 0; }
            [data-testid="stVerticalBlockBorderWrapper"] { border-radius: 1.15rem !important; }
            .chart-header { align-items: flex-start; flex-direction: column; gap: 0.25rem; }
            .chart-legend-note { white-space: normal; }
            [data-testid="stDataFrame"] { font-size: 0.85rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def loan_form() -> tuple[LoanDetails, tuple[ExtraPayment, ...]]:
    """Render one mobile-friendly form and return normalized calculator inputs."""
    payment_ids = initialize_one_time_payment_rows()
    one_time_payment_inputs: list[tuple[int, float, date]] = []

    with st.form("mortgage_inputs", border=True):
        st.subheader("Loan details")
        amount_col, rate_col = st.columns(2, gap="medium")
        with amount_col:
            loan_amount = st.number_input(
                "Loan amount",
                min_value=1_000.0,
                max_value=10_000_000.0,
                value=300_000.0,
                step=5_000.0,
                format="%.0f",
                help="Amount borrowed, excluding your down payment.",
            )
        with rate_col:
            interest_rate = st.number_input(
                "Interest rate",
                min_value=0.0,
                max_value=20.0,
                value=6.5,
                step=0.125,
                format="%.3f",
                help="Annual percentage rate for this estimate.",
            )

        term_col, date_col = st.columns(2, gap="medium")
        with term_col:
            loan_term = st.selectbox(
                "Loan term",
                options=[10, 15, 20, 25, 30],
                index=4,
                format_func=lambda years: f"{years} years",
            )
        with date_col:
            start_date = st.date_input(
                "First payment month",
                value=date.today().replace(day=1),
                min_value=date(2020, 1, 1),
                max_value=date(2050, 12, 1),
                format="MM/DD/YYYY",
            )

        st.subheader("Payoff strategy")
        monthly_col, biweekly_col = st.columns(2, gap="medium")
        with monthly_col:
            extra_monthly = st.number_input(
                "Extra principal each month",
                min_value=0.0,
                value=0.0,
                step=50.0,
                format="%.0f",
                help="Added directly to principal every month.",
            )
        with biweekly_col:
            use_biweekly = st.toggle(
                "Use biweekly payments",
                value=False,
                help="Models 26 half-payments yearly, equal to one extra monthly payment per year.",
            )

        with st.expander("One-time payments", expanded=len(payment_ids) > 1):
            for payment_number, payment_id in enumerate(payment_ids, start=1):
                st.markdown(
                    f'<div class="one-time-row-title">Payment {payment_number}</div>',
                    unsafe_allow_html=True,
                )
                amount_col, payment_date_col, remove_col = st.columns(
                    [1, 1, 0.52],
                    gap="small",
                    vertical_alignment="bottom",
                )
                with amount_col:
                    one_time_amount = st.number_input(
                        f"Payment {payment_number} amount",
                        min_value=0.0,
                        value=0.0,
                        step=500.0,
                        format="%.0f",
                        key=f"one_time_amount_{payment_id}",
                    )
                with payment_date_col:
                    one_time_date = st.date_input(
                        f"Payment {payment_number} month",
                        value=date.today().replace(day=1),
                        min_value=date(2020, 1, 1),
                        max_value=date(2050, 12, 1),
                        format="MM/DD/YYYY",
                        key=f"one_time_date_{payment_id}",
                    )
                with remove_col:
                    if len(payment_ids) > 1:
                        st.form_submit_button(
                            "Remove",
                            key=f"remove_one_time_payment_{payment_id}",
                            type="tertiary",
                            icon=":material/delete:",
                            help=f"Remove payment {payment_number}",
                            on_click=remove_one_time_payment_row,
                            args=(payment_id,),
                            width="stretch",
                        )
                one_time_payment_inputs.append(
                    (payment_number, one_time_amount, one_time_date)
                )

            st.form_submit_button(
                "Add another payment",
                key="add_one_time_payment",
                type="secondary",
                icon=":material/add:",
                disabled=len(payment_ids) >= MAX_ONE_TIME_PAYMENTS,
                help=f"Add up to {MAX_ONE_TIME_PAYMENTS} one-time payments.",
                on_click=add_one_time_payment_row,
                width="stretch",
            )

        with st.expander("Taxes, insurance & HOA", expanded=False):
            tax_col, insurance_col = st.columns(2, gap="medium")
            with tax_col:
                annual_taxes = st.number_input(
                    "Annual property taxes",
                    min_value=0.0,
                    value=0.0,
                    step=100.0,
                    format="%.0f",
                )
            with insurance_col:
                home_insurance = st.number_input(
                    "Annual home insurance",
                    min_value=0.0,
                    value=0.0,
                    step=100.0,
                    format="%.0f",
                )
            hoa_col, pmi_col = st.columns(2, gap="medium")
            with hoa_col:
                hoa_dues = st.number_input(
                    "Monthly HOA dues",
                    min_value=0.0,
                    value=0.0,
                    step=10.0,
                    format="%.0f",
                )
            with pmi_col:
                pmi = st.number_input(
                    "Monthly mortgage insurance",
                    min_value=0.0,
                    value=0.0,
                    step=10.0,
                    format="%.0f",
                )

        st.form_submit_button(
            "Calculate payment",
            type="primary",
            width="stretch",
        )
        st.caption("Adjust values, then tap Calculate payment to update estimate.")

    normalized_start = datetime.combine(start_date.replace(day=1), datetime.min.time())
    loan_details = LoanDetails(
        loan_amount=loan_amount,
        interest_rate=interest_rate,
        loan_term_years=loan_term,
        start_date=normalized_start,
        annual_taxes=annual_taxes,
        home_insurance=home_insurance,
        hoa_dues=hoa_dues * 12,
        pmi=pmi * 12,
    )

    payments: list[ExtraPayment] = []
    if extra_monthly > 0:
        payments.append(ExtraPayment(ExtraPaymentType.MONTHLY, extra_monthly))
    if use_biweekly:
        monthly_pi = MortgageCalculator(loan_details).calculate_monthly_payment()
        payments.append(ExtraPayment(ExtraPaymentType.BIWEEKLY, monthly_pi))
    invalid_one_time_payments: list[int] = []
    for payment_number, one_time_amount, one_time_date in one_time_payment_inputs:
        if one_time_amount > 0:
            normalized_one_time = one_time_date.replace(day=1)
            if normalized_one_time < start_date.replace(day=1):
                invalid_one_time_payments.append(payment_number)
            else:
                payments.append(
                    ExtraPayment(
                        ExtraPaymentType.ONE_TIME,
                        one_time_amount,
                        datetime.combine(normalized_one_time, datetime.min.time()),
                    )
                )
    if invalid_one_time_payments:
        payment_labels = ", ".join(str(number) for number in invalid_one_time_payments)
        if len(invalid_one_time_payments) == 1:
            st.warning(
                f"One-time payment {payment_labels} must be on or after the first payment "
                "month; it was not applied."
            )
        else:
            st.warning(
                f"One-time payments {payment_labels} must be on or after the first payment "
                "month; they were not applied."
            )

    return loan_details, tuple(payments)


def render_results(
    loan_details: LoanDetails,
    extra_payments: tuple[ExtraPayment, ...],
) -> dict[str, Any]:
    """Render the dashboard summary and return data for the detail views."""
    results = calculate_results(loan_details, extra_payments)
    recurring_extra = sum(
        payment.amount
        if payment.payment_type is ExtraPaymentType.MONTHLY
        else payment.amount / 12
        if payment.payment_type is ExtraPaymentType.BIWEEKLY
        else 0.0
        for payment in extra_payments
    )
    estimated_monthly = results["total_monthly"] + recurring_extra

    st.markdown('<span class="results-anchor"></span>', unsafe_allow_html=True)
    st.markdown('<div class="section-eyebrow">Your estimate</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="payment-hero">
            <div class="payment-hero-top">
                <div>
                    <div class="payment-hero-label">Estimated monthly payment</div>
                    <div class="payment-hero-value">${estimated_monthly:,.0f}<span>/ month</span></div>
                </div>
                <div class="hero-plan-badge">{loan_details.loan_term_years}-year plan</div>
            </div>
            <div class="payment-hero-facts">
                <div>
                    <span class="hero-fact-label">Loan amount</span>
                    <span class="hero-fact-value">${loan_details.loan_amount:,.0f}</span>
                </div>
                <div>
                    <span class="hero-fact-label">Interest rate</span>
                    <span class="hero-fact-value">{loan_details.interest_rate:g}%</span>
                </div>
                <div>
                    <span class="hero-fact-label">Extra principal</span>
                    <span class="hero-fact-value">${recurring_extra:,.0f}/mo</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_one, metric_two, metric_three = st.columns(3, gap="small")
    with metric_one:
        st.metric("Principal & interest", f"${results['monthly_pi']:,.0f}", border=True)
    with metric_two:
        st.metric("Total interest", f"${results['selected_interest']:,.0f}", border=True)
    with metric_three:
        st.metric("Payoff month", results["selected_payoff"].strftime("%b %Y"), border=True)

    if results["interest_saved"] > 0.01:
        years, remaining_months = divmod(results["months_saved"], 12)
        time_saved = f"{years} yr {remaining_months} mo" if years else f"{remaining_months} mo"
        st.markdown(
            f"""
            <div class="strategy-callout">
                <div class="strategy-callout-icon">&#8593;</div>
                <div>
                    <strong>Your strategy saves ${results['interest_saved']:,.0f}</strong>
                    <span>Mortgage-free {time_saved} earlier &middot;
                    {results['original_payoff'].strftime('%b %Y')} &rarr;
                    {results['selected_payoff'].strftime('%b %Y')}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        save_one, save_two = st.columns(2, gap="small")
        with save_one:
            st.metric("Interest saved", f"${results['interest_saved']:,.0f}", border=True)
        with save_two:
            st.metric("Time saved", time_saved, border=True)
    else:
        st.markdown(
            """
            <div class="strategy-callout">
                <div class="strategy-callout-icon">+</div>
                <div>
                    <strong>See how much sooner you could be mortgage-free</strong>
                    <span>Add monthly, biweekly, or one-time principal to compare payoff strategies.</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("Monthly payment breakdown", expanded=False):
        breakdown = {
            "Principal & interest": results["monthly_pi"],
            "Property taxes": loan_details.annual_taxes / 12,
            "Home insurance": loan_details.home_insurance / 12,
            "HOA dues": loan_details.hoa_dues / 12,
            "Mortgage insurance": loan_details.pmi / 12,
            "Average extra principal": recurring_extra,
        }
        for label, amount in breakdown.items():
            left, right = st.columns([3, 1], gap="small")
            left.write(label)
            right.markdown(f"**${amount:,.0f}**")

    return results


def render_balance_chart(results: dict[str, Any], has_extra_payments: bool) -> None:
    """Render the responsive payoff chart inside a dashboard card."""
    with st.container(border=True):
        legend_note = "Teal: your strategy · Dashed: original plan" if has_extra_payments else "Your projected loan balance"
        st.markdown(
            f"""
            <div class="chart-header">
                <div>
                    <div class="chart-title">Balance over time</div>
                    <div class="chart-subtitle">See how principal payments change your path to $0.</div>
                </div>
                <div class="chart-legend-note">{legend_note}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        original = results["original_schedule"]
        selected = results["selected_schedule"]
        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=original["date"],
                y=original["ending_balance"],
                mode="lines",
                name="Original plan" if has_extra_payments else "Your plan",
                line={
                    "color": "#9aabba" if has_extra_payments else "#0b7a70",
                    "dash": "dash" if has_extra_payments else "solid",
                    "width": 2 if has_extra_payments else 3,
                },
                fill="tozeroy" if not has_extra_payments else None,
                fillcolor="rgba(11, 122, 112, 0.10)" if not has_extra_payments else None,
                hovertemplate="%{x|%b %Y}<br>$%{y:,.0f}<extra></extra>",
            )
        )
        if has_extra_payments:
            figure.add_trace(
                go.Scatter(
                    x=selected["date"],
                    y=selected["ending_balance"],
                    mode="lines",
                    name="Your strategy",
                    line={"color": "#0b7a70", "width": 3},
                    fill="tozeroy",
                    fillcolor="rgba(11, 122, 112, 0.10)",
                    hovertemplate="%{x|%b %Y}<br>$%{y:,.0f}<extra></extra>",
                )
            )
        figure.update_layout(
            height=330,
            margin={"l": 4, "r": 4, "t": 28, "b": 4},
            hovermode="x unified",
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#607084", "size": 12},
            xaxis={
                "title": None,
                "showgrid": False,
                "linecolor": "#e2e8ee",
                "tickfont": {"color": "#718096"},
            },
            yaxis={
                "title": None,
                "tickformat": "$~s",
                "rangemode": "tozero",
                "gridcolor": "#e8edf1",
                "zeroline": False,
                "tickfont": {"color": "#718096"},
            },
        )
        st.plotly_chart(
            figure,
            width="stretch",
            config={"displayModeBar": False, "responsive": True},
        )


def render_schedule(schedule: pd.DataFrame) -> None:
    """Keep dense amortization detail available without dominating mobile UI."""
    with st.expander("Amortization schedule", expanded=False):
        show_full_schedule = st.toggle("Show full schedule", value=False)
        visible_schedule = schedule if show_full_schedule else schedule.head(12)
        display = visible_schedule[
            ["date", "principal_payment", "interest_payment", "extra_payment", "ending_balance"]
        ].copy()
        display.columns = ["Month", "Principal", "Interest", "Extra", "Balance"]
        st.dataframe(
            display,
            width="stretch",
            hide_index=True,
            height=420 if show_full_schedule else "auto",
            column_config={
                "Month": st.column_config.DateColumn("Month", format="MMM YYYY"),
                "Principal": st.column_config.NumberColumn("Principal", format="dollar"),
                "Interest": st.column_config.NumberColumn("Interest", format="dollar"),
                "Extra": st.column_config.NumberColumn("Extra", format="dollar"),
                "Balance": st.column_config.NumberColumn("Balance", format="dollar"),
            },
        )
        if not show_full_schedule:
            st.caption(f"First 12 of {len(schedule):,} payments shown.")

        csv_data = schedule.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download complete schedule (CSV)",
            data=csv_data,
            file_name="mortgage-amortization.csv",
            mime="text/csv",
            width="stretch",
        )


def main() -> None:
    st.set_page_config(
        page_title="Easy Mortgage Calculator",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    apply_styles()
    st.markdown(
        """
        <div class="app-header">
            <div class="app-heading">
                <div class="app-kicker">Plan with confidence</div>
                <h1>Easy Mortgage Calculator</h1>
                <p class="app-intro">Estimate your payment, compare payoff strategies, and see the long-term impact in one clear view.</p>
            </div>
            <div class="header-note">
                <span class="header-note-icon">&#10003;</span>
                Instant payoff scenarios
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    input_col, results_col = st.columns([0.86, 1.14], gap="large", vertical_alignment="top")
    with input_col:
        st.markdown('<span class="workspace-left-marker"></span>', unsafe_allow_html=True)
        loan_details, extra_payments = loan_form()
    with results_col:
        results = render_results(loan_details, extra_payments)

    st.markdown("<div style='height: 0.7rem'></div>", unsafe_allow_html=True)
    render_balance_chart(results, bool(extra_payments))
    render_schedule(results["selected_schedule"])
    st.caption(
        "Estimate only—not financial advice. Actual payments may include costs not entered here. "
        "Confirm loan terms with your lender."
    )


if __name__ == "__main__":
    main()
