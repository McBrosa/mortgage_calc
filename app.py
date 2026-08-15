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
    """Add focused responsive polish while retaining native Streamlit widgets."""
    st.markdown(
        """
        <style>
        .stMainBlockContainer {
            max-width: 72rem;
            padding-top: 1.35rem;
            padding-bottom: max(3rem, env(safe-area-inset-bottom));
        }
        h1 {
            letter-spacing: -0.035em;
            line-height: 1.08 !important;
            margin-bottom: 0.15rem !important;
        }
        h2, h3 { letter-spacing: -0.018em; }
        .app-kicker {
            color: #0f766e;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.1em;
            margin-bottom: 0.25rem;
            text-transform: uppercase;
        }
        .app-intro {
            color: #475569;
            font-size: 1rem;
            margin: 0 0 1.2rem;
            max-width: 44rem;
        }
        [data-testid="stForm"] {
            background: #ffffff;
            border: 1px solid #dbe3ea;
            border-radius: 1rem;
            box-shadow: 0 0.4rem 1.4rem rgba(15, 23, 42, 0.055);
            padding: 1.15rem 1.2rem 1.25rem;
        }
        [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input,
        [data-testid="stSelectbox"] > div > div {
            min-height: 44px;
            font-size: 1rem;
        }
        .stButton button,
        .stDownloadButton button,
        [data-testid="stFormSubmitButton"] button {
            min-height: 48px;
            font-weight: 750;
            touch-action: manipulation;
        }
        [data-testid="stExpander"] summary {
            min-height: 48px;
        }
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #dbe3ea;
            border-radius: 0.85rem;
            padding: 0.8rem 0.9rem;
        }
        [data-testid="stMetricLabel"] p { color: #475569; }
        [data-testid="stMetricValue"] {
            color: #0f172a;
            font-size: 1.5rem;
            font-weight: 780;
        }
        .payment-hero {
            background: linear-gradient(135deg, #0f766e, #115e59);
            border-radius: 1rem;
            color: white;
            margin: 0.25rem 0 1rem;
            padding: 1.15rem 1.25rem;
            box-shadow: 0 0.55rem 1.5rem rgba(15, 118, 110, 0.18);
        }
        .payment-hero-label {
            font-size: 0.85rem;
            font-weight: 650;
            opacity: 0.88;
        }
        .payment-hero-value {
            font-size: clamp(2rem, 8vw, 3rem);
            font-weight: 820;
            letter-spacing: -0.04em;
            line-height: 1.08;
            margin: 0.2rem 0;
        }
        .payment-hero-note {
            font-size: 0.82rem;
            opacity: 0.82;
        }
        div[data-testid="stPlotlyChart"] { overflow: hidden; }

        @media (max-width: 640px) {
            .stMainBlockContainer {
                padding-left: 0.85rem;
                padding-right: 0.85rem;
                padding-top: 0.75rem;
            }
            h1 { font-size: 2rem !important; }
            h2 { font-size: 1.4rem !important; }
            h3 { font-size: 1.1rem !important; }
            .app-intro { font-size: 0.94rem; margin-bottom: 0.9rem; }
            [data-testid="stForm"] {
                border-radius: 0.85rem;
                padding: 0.85rem 0.8rem 1rem;
            }
            [data-testid="stMetric"] { padding: 0.7rem 0.8rem; }
            [data-testid="stMetricValue"] { font-size: 1.3rem; }
            .payment-hero { padding: 1rem; }
            [data-testid="stDataFrame"] { font-size: 0.85rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def loan_form() -> tuple[LoanDetails, tuple[ExtraPayment, ...]]:
    """Render one mobile-friendly form and return normalized calculator inputs."""
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

        with st.expander("One-time payment", expanded=False):
            one_time_col, one_time_date_col = st.columns(2, gap="medium")
            with one_time_col:
                one_time_amount = st.number_input(
                    "One-time principal payment",
                    min_value=0.0,
                    value=0.0,
                    step=500.0,
                    format="%.0f",
                )
            with one_time_date_col:
                one_time_date = st.date_input(
                    "Payment month",
                    value=date.today().replace(day=1),
                    min_value=date(2020, 1, 1),
                    max_value=date(2050, 12, 1),
                    format="MM/DD/YYYY",
                    key="one_time_date",
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
    if one_time_amount > 0:
        normalized_one_time = one_time_date.replace(day=1)
        if normalized_one_time < start_date.replace(day=1):
            st.warning("One-time payment must be on or after first payment month; it was not applied.")
        else:
            payments.append(
                ExtraPayment(
                    ExtraPaymentType.ONE_TIME,
                    one_time_amount,
                    datetime.combine(normalized_one_time, datetime.min.time()),
                )
            )

    return loan_details, tuple(payments)


def render_results(
    loan_details: LoanDetails,
    extra_payments: tuple[ExtraPayment, ...],
) -> None:
    """Render concise results first, details second."""
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

    st.subheader("Your estimate")
    st.markdown(
        f"""
        <div class="payment-hero">
            <div class="payment-hero-label">Estimated monthly payment</div>
            <div class="payment-hero-value">${estimated_monthly:,.0f}</div>
            <div class="payment-hero-note">Includes principal, interest, entered housing costs, and monthly extra principal.</div>
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
        st.success(
            f"This strategy saves **${results['interest_saved']:,.0f}** in interest "
            f"and pays off the loan **{time_saved} earlier**."
        )
        save_one, save_two = st.columns(2, gap="small")
        with save_one:
            st.metric("Interest saved", f"${results['interest_saved']:,.0f}", border=True)
        with save_two:
            st.metric("Time saved", time_saved, border=True)

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

    render_balance_chart(results, bool(extra_payments))
    render_schedule(results["selected_schedule"])


def render_balance_chart(results: dict[str, Any], has_extra_payments: bool) -> None:
    """Render a compact responsive payoff chart."""
    st.subheader("Balance over time")
    original = results["original_schedule"]
    selected = results["selected_schedule"]
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=original["date"],
            y=original["ending_balance"],
            mode="lines",
            name="Original",
            line={"color": "#94a3b8", "dash": "dash", "width": 2},
            hovertemplate="%{x|%b %Y}<br>$%{y:,.0f}<extra>Original</extra>",
        )
    )
    if has_extra_payments:
        figure.add_trace(
            go.Scatter(
                x=selected["date"],
                y=selected["ending_balance"],
                mode="lines",
                name="Your strategy",
                line={"color": "#0f766e", "width": 3},
                hovertemplate="%{x|%b %Y}<br>$%{y:,.0f}<extra>Your strategy</extra>",
            )
        )
    figure.update_layout(
        height=330,
        margin={"l": 8, "r": 8, "t": 18, "b": 8},
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.08, "x": 0},
        xaxis={"title": None, "showgrid": False},
        yaxis={"title": None, "tickformat": "$~s", "rangemode": "tozero"},
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
    st.markdown('<div class="app-kicker">Plan with confidence</div>', unsafe_allow_html=True)
    st.title("Easy Mortgage Calculator")
    st.markdown(
        '<p class="app-intro">Estimate your monthly payment and see how extra principal changes your payoff date.</p>',
        unsafe_allow_html=True,
    )

    loan_details, extra_payments = loan_form()
    render_results(loan_details, extra_payments)
    st.caption(
        "Estimate only—not financial advice. Actual payments may include costs not entered here. "
        "Confirm loan terms with your lender."
    )


if __name__ == "__main__":
    main()
