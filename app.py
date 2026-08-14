"""
Juniper-based Mortgage Calculator Application
Main application interface using Juniper for interactive mortgage calculations
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
from typing import List, Dict, Any

from mortgage_calculator import (
    MortgageCalculator,
    MortgageAnalyzer,
    LoanDetails,
    ExtraPayment,
    ExtraPaymentType,
    PaymentFrequency
)

# Module-level constants mapping display labels to payment types
PAYMENT_TYPE_MONTHLY = "Extra Monthly Payment"
PAYMENT_TYPE_BIWEEKLY = "Pay Bi-Weekly"
PAYMENT_TYPE_ONE_TIME = "One Time Payment"

PAYMENT_TYPE_MAP = {
    PAYMENT_TYPE_MONTHLY: ExtraPaymentType.MONTHLY,
    PAYMENT_TYPE_BIWEEKLY: ExtraPaymentType.BIWEEKLY,
    PAYMENT_TYPE_ONE_TIME: ExtraPaymentType.ONE_TIME,
}


class MortgageApp:
    """Main Juniper application for mortgage calculations"""
    
    def __init__(self):
        self.calculator = None
        self.analyzer = None
        self.loan_details = None
        self.extra_payments = []
    
    def create_loan_input_form(self):
        """Create loan details input form"""
        st.header("📊 Mortgage Information")

        # Primary loan inputs rendered full-width to prevent value truncation in narrow sidebar
        loan_amount = st.number_input(
            "Loan Amount ($)",
            min_value=1000.0,
            max_value=10000000.0,
            value=100000.0,
            step=1000.0,
            help="The total amount of the mortgage loan",
            label_visibility="visible",
            key="loan_amount"
        )

        interest_rate = st.number_input(
            "Interest Rate (%)",
            min_value=0.0,
            max_value=20.0,
            value=0.0,
            step=0.01,
            help="Annual interest rate as a percentage",
            label_visibility="visible",
            key="interest_rate"
        )

        loan_term = st.selectbox(
            "Loan Term (years)",
            options=[10, 15, 20, 25, 30],
            index=4,  # Default to 30 years
            help="The length of the loan in years",
            label_visibility="visible",
            key="loan_term"
        )

        col1, col2 = st.columns(2)

        with col1:
            start_month = st.selectbox(
                "Start Month",
                options=list(range(1, 13)),
                index=0,  # January
                format_func=lambda x: datetime(2000, x, 1).strftime("%B"),
                label_visibility="visible",
                key="start_month"
            )

        with col2:
            start_year = st.number_input(
                "Start Year",
                min_value=2020,
                max_value=2050,
                value=2026,
                step=1,
                label_visibility="visible",
                key="start_year"
            )

        # Optional fields
        st.subheader("Optional Monthly Costs")
        annual_taxes = st.number_input("Annual Property Taxes ($)", min_value=0.0, value=0.0, step=100.0, label_visibility="visible", key="annual_taxes")
        home_insurance = st.number_input("Annual Home Insurance ($)", min_value=0.0, value=0.0, step=100.0, label_visibility="visible", key="home_insurance")
        hoa_dues = st.number_input("Monthly HOA Dues ($)", min_value=0.0, value=0.0, step=10.0, label_visibility="visible", key="hoa_dues")
        pmi = st.number_input("Monthly PMI ($)", min_value=0.0, value=0.0, step=10.0, label_visibility="visible", key="pmi")
        
        start_date = datetime(start_year, start_month, 1)

        # Defensive interest rate check (widget bounds already enforce 0–20)
        if not (0 <= interest_rate <= 20):
            st.error("Interest rate must be between 0% and 20%, inclusive.")
            return None

        self.loan_details = LoanDetails(
            loan_amount=loan_amount,
            interest_rate=interest_rate,
            loan_term_years=loan_term,
            start_date=start_date,
            annual_taxes=annual_taxes,
            home_insurance=home_insurance,
            hoa_dues=hoa_dues * 12,  # Convert to annual
            pmi=pmi * 12  # Convert to annual
        )
        
        return self.loan_details
    
    def create_extra_payment_form(self):
        """Create extra payment configuration form"""
        st.header("💰 Extra Payment Information")
        
        # Payment type selection
        payment_type = st.selectbox(
            "Extra Payment Type",
            options=["Extra Monthly Payment", "Pay Bi-Weekly", "One Time Payment"],
            help="Choose how you want to make extra payments",
            label_visibility="visible",
            key="payment_type"
        )

        extra_payments = []

        if payment_type == PAYMENT_TYPE_MONTHLY:
            amount = st.number_input(
                "Extra Monthly Amount ($)",
                min_value=0.0,
                value=0.0,
                step=50.0,
                label_visibility="visible",
                key="extra_monthly"
            )
            if amount > 0:
                extra_payments.append(ExtraPayment(
                    payment_type=ExtraPaymentType.MONTHLY,
                    amount=amount
                ))

        elif payment_type == PAYMENT_TYPE_BIWEEKLY:
            st.info("Bi-weekly payments: Pay half your monthly payment every two weeks (26 payments/year)")
            enable_biweekly = st.checkbox("Enable bi-weekly payments", key="enable_biweekly")
            if enable_biweekly and self.loan_details:
                monthly_payment = MortgageCalculator(self.loan_details).calculate_monthly_payment()
                biweekly_amount = monthly_payment
                st.write(f"Bi-weekly equivalent extra per month: ${biweekly_amount / 12:.2f}")
                extra_payments.append(ExtraPayment(
                    payment_type=ExtraPaymentType.BIWEEKLY,
                    amount=biweekly_amount
                ))

        elif payment_type == PAYMENT_TYPE_ONE_TIME:
            amount = st.number_input(
                "One-time Payment Amount ($)",
                min_value=0.0,
                value=0.0,
                step=100.0,
                label_visibility="visible",
                key="one_time_amount"
            )
            payment_date = st.date_input(
                "Payment Date",
                value=date.today(),
                key="one_time_date",
                label_visibility="visible"
            )
            # Normalize to first of the month (schedule is monthly)
            payment_date_normalized = payment_date.replace(day=1)
            st.caption("Applied on the 1st of the selected month")

            if amount > 0:
                # Guard: one-time date must be on/after loan start
                loan_start = self.loan_details.start_date.date() if self.loan_details else None
                if loan_start and payment_date_normalized < loan_start.replace(day=1):
                    st.error("One-time payment date must be on or after the loan start date.")
                else:
                    extra_payments.append(ExtraPayment(
                        payment_type=ExtraPaymentType.ONE_TIME,
                        amount=amount,
                        start_date=datetime.combine(payment_date_normalized, datetime.min.time())
                    ))

        # Allow multiple extra payment types
        st.subheader("Combine Multiple Payment Strategies")
        combine_payments = st.checkbox("Add additional extra payment strategy", key="combine_payments")

        if combine_payments:
            col1, col2 = st.columns(2)
            with col1:
                extra_monthly = st.number_input(
                    "Additional Monthly Extra ($)",
                    min_value=0.0,
                    value=0.0,
                    step=50.0,
                    label_visibility="visible",
                    key="combine_extra_monthly"
                )
                if extra_monthly > 0:
                    extra_payments.append(ExtraPayment(
                        payment_type=ExtraPaymentType.MONTHLY,
                        amount=extra_monthly
                    ))

            with col2:
                one_time_extra = st.number_input(
                    "Additional One-time Payment ($)",
                    min_value=0.0,
                    value=0.0,
                    step=100.0,
                    label_visibility="visible",
                    key="combine_one_time_amount"
                )
                if one_time_extra > 0:
                    one_time_date = st.date_input(
                        "Additional Payment Date",
                        value=date.today(),
                        key="extra_date",
                        label_visibility="visible"
                    )
                    one_time_date_normalized = one_time_date.replace(day=1)
                    st.caption("Applied on the 1st of the selected month")
                    loan_start = self.loan_details.start_date.date() if self.loan_details else None
                    if loan_start and one_time_date_normalized < loan_start.replace(day=1):
                        st.error("Additional payment date must be on or after the loan start date.")
                    else:
                        extra_payments.append(ExtraPayment(
                            payment_type=ExtraPaymentType.ONE_TIME,
                            amount=one_time_extra,
                            start_date=datetime.combine(one_time_date_normalized, datetime.min.time())
                        ))
        
        self.extra_payments = extra_payments
        return extra_payments
    
    def display_results(self):
        """Display calculation results"""
        if not self.loan_details:
            return
        
        self.calculator = MortgageCalculator(self.loan_details)
        self.analyzer = MortgageAnalyzer(self.calculator)
        
        # Calculate results
        comparison = self.calculator.calculate_payoff_comparison(self.extra_payments)
        original = comparison['original']
        with_extra = comparison['with_extra']
        
        st.header("📈 Results")

        if with_extra.interest_saved > 0:
            st.success(
                f"💰 Extra payments save **${with_extra.interest_saved:,.0f}** in interest "
                f"and pay off the loan **{with_extra.years_saved:.1f} years** early!"
            )

        # Results summary
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Original Loan")
            st.metric("Monthly P&I Payment", f"${original.monthly_payment:.2f}")
            st.metric("Total Interest", f"${original.total_interest:,.2f}")
            st.metric("Payoff Date", original.payoff_date.strftime("%b %Y"))
        
        with col2:
            st.subheader("With Extra Payments")
            st.metric("Monthly P&I Payment", f"${with_extra.monthly_payment:.2f}")
            st.metric("Total Interest", f"${with_extra.total_interest:,.2f}")
            st.metric("New Payoff Date", with_extra.payoff_date.strftime("%b %Y"))
            
            if with_extra.years_saved > 0:
                st.metric("Time Saved", f"{with_extra.years_saved:.1f} years", delta=f"-{with_extra.years_saved:.1f}")
                st.metric("Interest Saved", f"${with_extra.interest_saved:,.2f}", delta=f"-{with_extra.interest_saved:,.2f}")
        
        # Check for overpayment truncation in the extra-payment scenario
        if self.extra_payments:
            extra_schedule = self.calculator.generate_amortization_schedule(self.extra_payments)
            if 'unused_extra' in extra_schedule.columns:
                total_unused = extra_schedule['unused_extra'].sum()
                if total_unused > 0.01:
                    st.info(
                        f"Note: Your extra payment exceeded the remaining balance in the payoff month. "
                        f"${total_unused:,.2f} of the extra payment was not applied."
                    )

        # Additional payment info
        total_monthly = self.calculator.calculate_total_monthly_payment()
        extra_amount = sum(ep.amount for ep in self.extra_payments if ep.payment_type == ExtraPaymentType.MONTHLY)

        st.subheader("Payment Details")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Base Monthly Payment", f"${original.monthly_payment:.2f}")
        with col2:
            st.metric("Extra Monthly Payment", f"${extra_amount:.2f}")
        with col3:
            st.metric("Total Monthly Payment", f"${total_monthly + extra_amount:.2f}")
    
    def create_balance_chart(self):
        """Create mortgage balance over time chart"""
        if not self.calculator:
            return
        
        st.header("📊 Mortgage Balance Over Time")
        
        # Get balance data for both scenarios
        original_balance = self.analyzer.get_balance_over_time([])
        extra_balance = self.analyzer.get_balance_over_time(self.extra_payments)
        
        # Create plotly chart
        fig = go.Figure()
        
        # Original scenario
        fig.add_trace(go.Scatter(
            x=original_balance['date'],
            y=original_balance['ending_balance'],
            mode='lines',
            name='Original',
            line=dict(color='blue', dash='dash', width=2),
            hovertemplate='<b>Original</b><br>Date: %{x}<br>Balance: $%{y:,.2f}<extra></extra>'
        ))
        
        # Extra payment scenario
        if self.extra_payments:
            fig.add_trace(go.Scatter(
                x=extra_balance['date'],
                y=extra_balance['ending_balance'],
                mode='lines',
                name='With Extra Payments',
                line=dict(color='green', width=3),
                hovertemplate='<b>With Extra Payments</b><br>Date: %{x}<br>Balance: $%{y:,.2f}<extra></extra>'
            ))
        
        # Update layout
        fig.update_layout(
            title='Mortgage Balance Over Time',
            xaxis_title='Date',
            yaxis_title='Mortgage Balance ($)',
            hovermode='x unified',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            height=500
        )
        
        # Format y-axis as currency
        fig.update_yaxes(tickformat='$,.0f')
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_amortization_table(self):
        """Create detailed amortization table"""
        if not self.calculator:
            return
        
        st.header("📋 Amortization Schedule")
        
        # Generate schedule
        schedule = self.calculator.generate_amortization_schedule(self.extra_payments)
        
        # Format for display
        display_schedule = schedule.copy()
        display_schedule['date'] = display_schedule['date'].dt.strftime('%Y-%m')
        display_schedule['beginning_balance'] = display_schedule['beginning_balance'].apply(lambda x: f"${x:,.2f}")
        display_schedule['monthly_payment'] = display_schedule['monthly_payment'].apply(lambda x: f"${x:,.2f}")
        display_schedule['principal_payment'] = display_schedule['principal_payment'].apply(lambda x: f"${x:,.2f}")
        display_schedule['interest_payment'] = display_schedule['interest_payment'].apply(lambda x: f"${x:,.2f}")
        display_schedule['extra_payment'] = display_schedule['extra_payment'].apply(lambda x: f"${x:,.2f}")
        display_schedule['total_payment'] = display_schedule['total_payment'].apply(lambda x: f"${x:,.2f}")
        display_schedule['ending_balance'] = display_schedule['ending_balance'].apply(lambda x: f"${x:,.2f}")
        
        # Rename columns for display
        display_schedule = display_schedule.rename(columns={
            'payment_number': 'Payment #',
            'date': 'Date',
            'beginning_balance': 'Beginning Balance',
            'monthly_payment': 'Monthly Payment',
            'principal_payment': 'Principal',
            'interest_payment': 'Interest',
            'extra_payment': 'Extra Payment',
            'total_payment': 'Total Payment',
            'ending_balance': 'Ending Balance'
        })
        
        # Show first 12 months by default, with option to show all
        show_all = st.checkbox("Show complete schedule", value=False)
        
        if show_all:
            st.dataframe(display_schedule, use_container_width=True)
        else:
            st.dataframe(display_schedule.head(12), use_container_width=True)
            st.info(f"Showing first 12 payments. Total payments: {len(display_schedule)}")
    
    def run(self):
        """Run the main application"""
        st.set_page_config(
            page_title="Mortgage Calculator Pro",
            page_icon="🏠",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        st.markdown("""
        <style>
        [data-testid="stMetric"] {
            background-color: #f8f9fa;
            color: #1a1a1a;
            border-radius: 8px;
            padding: 12px;
            border-left: 4px solid #0066cc;
        }
        [data-testid="stMetricLabel"],
        [data-testid="stMetricLabel"] p {
            color: #333 !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.4rem !important;
            font-weight: 700 !important;
            color: #0a0a0a !important;
        }
        [data-testid="stMetricDelta"] {
            color: #0a7d33 !important;
        }
        .stSuccess { border-radius: 8px; }
        </style>
        """, unsafe_allow_html=True)

        st.title("🏠 Mortgage Calculator Pro")
        st.markdown("**Early Payoff Calculator & Amortization Schedule Generator**")
        
        # Sidebar for inputs
        with st.sidebar:
            st.header("Loan Configuration")
            self.create_loan_input_form()
            st.divider()
            self.create_extra_payment_form()
        
        # Main content area
        if self.loan_details:
            # Results display
            self.display_results()
            st.divider()
            
            # Chart
            self.create_balance_chart()
            st.divider()
            
            # Amortization table
            self.create_amortization_table()
        
        else:
            st.info("👈 Please configure your loan details in the sidebar to get started.")


def main():
    """Main application entry point"""
    app = MortgageApp()
    app.run()


if __name__ == "__main__":
    main()
