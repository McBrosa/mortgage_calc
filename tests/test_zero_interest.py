from datetime import datetime

import pytest

from mortgage_calculator import LoanDetails, MortgageCalculator


def test_zero_interest_loan_amortizes_evenly():
    calculator = MortgageCalculator(
        LoanDetails(
            loan_amount=100000.0,
            interest_rate=0.0,
            loan_term_years=30,
            start_date=datetime(2026, 1, 1),
        )
    )

    schedule = calculator.generate_amortization_schedule()

    assert calculator.calculate_monthly_payment() == pytest.approx(100000 / 360)
    assert len(schedule) == 360
    assert schedule["interest_payment"].sum() == 0
    assert schedule.iloc[-1]["ending_balance"] == pytest.approx(0)
