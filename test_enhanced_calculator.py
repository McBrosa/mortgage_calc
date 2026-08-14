#!/usr/bin/env python3
"""
Test script for enhanced mortgage calculator with multiple payment strategies
"""

from datetime import datetime, date
from mortgage_calculator import (
    MortgageCalculator, 
    MortgageAnalyzer,
    LoanDetails, 
    ExtraPayment, 
    ExtraPaymentType,
    PaymentFrequency
)

def test_multiple_payment_strategies():
    """Test a generic monthly-extra and one-time-payment scenario."""
    
    # Create loan details
    loan_details = LoanDetails(
        loan_amount=300000.0,
        interest_rate=6.5,
        loan_term_years=30,
        start_date=datetime(2026, 1, 1)
    )
    
    calculator = MortgageCalculator(loan_details)
    analyzer = MortgageAnalyzer(calculator)
    
    # Define payment strategies
    extra_payments = [
        # Monthly extra payment
        ExtraPayment(
            payment_type=ExtraPaymentType.MONTHLY,
            amount=1000.0
        ),
        # One-time payment
        ExtraPayment(
            payment_type=ExtraPaymentType.ONE_TIME,
            amount=10000.0,
            start_date=datetime(2026, 1, 1)  # After 3 months
        )
    ]
    
    # Calculate comparisons
    print("=== Mortgage Calculator Test: Multiple Payment Strategies ===\n")
    
    # Original loan
    original_comparison = calculator.calculate_payoff_comparison([])
    original = original_comparison['original']
    print(f"Original Loan:")
    print(f"  Monthly Payment: ${original.monthly_payment:,.2f}")
    print(f"  Total Interest: ${original.total_interest:,.2f}")
    print(f"  Payoff Date: {original.payoff_date.strftime('%B %Y')}")
    print()
    
    # Monthly extra only
    monthly_only = [ep for ep in extra_payments if ep.payment_type == ExtraPaymentType.MONTHLY]
    monthly_comparison = calculator.calculate_payoff_comparison(monthly_only)
    monthly_result = monthly_comparison['with_extra']
    print(f"With Monthly Extra Payment Only ($1,000/month):")
    print(f"  Total Interest: ${monthly_result.total_interest:,.2f}")
    print(f"  Interest Saved: ${monthly_result.interest_saved:,.2f}")
    print(f"  Time Saved: {monthly_result.years_saved:.1f} years")
    print(f"  New Payoff Date: {monthly_result.payoff_date.strftime('%B %Y')}")
    print()
    
    # One-time payment only
    one_time_only = [ep for ep in extra_payments if ep.payment_type == ExtraPaymentType.ONE_TIME]
    one_time_comparison = calculator.calculate_payoff_comparison(one_time_only)
    one_time_result = one_time_comparison['with_extra']
    print(f"With One-Time Payment Only ($10,000 in Jan 2026):")
    print(f"  Total Interest: ${one_time_result.total_interest:,.2f}")
    print(f"  Interest Saved: ${one_time_result.interest_saved:,.2f}")
    print(f"  Time Saved: {one_time_result.years_saved:.1f} years")
    print(f"  New Payoff Date: {one_time_result.payoff_date.strftime('%B %Y')}")
    print()
    
    # Combined strategy
    combined_comparison = calculator.calculate_payoff_comparison(extra_payments)
    combined_result = combined_comparison['with_extra']
    print(f"Combined Strategy ($1,000/month + $10,000 one-time):")
    print(f"  Total Interest: ${combined_result.total_interest:,.2f}")
    print(f"  Interest Saved: ${combined_result.interest_saved:,.2f}")
    print(f"  Time Saved: {combined_result.years_saved:.1f} years")
    print(f"  New Payoff Date: {combined_result.payoff_date.strftime('%B %Y')}")
    print()
    
    # Analysis
    individual_savings = monthly_result.interest_saved + one_time_result.interest_saved
    combined_savings = combined_result.interest_saved
    synergy = combined_savings - individual_savings
    
    print("=== Strategy Analysis ===")
    print(f"Monthly Extra Savings: ${monthly_result.interest_saved:,.2f}")
    print(f"One-Time Payment Savings: ${one_time_result.interest_saved:,.2f}")
    print(f"Sum of Individual Strategies: ${individual_savings:,.2f}")
    print(f"Combined Strategy Savings: ${combined_savings:,.2f}")
    print(f"Strategy Synergy: ${synergy:,.2f}")
    
    if synergy > 0:
        print("✓ The combined strategy saves MORE than individual strategies!")
    elif synergy < 0:
        print("⚠ The combined strategy saves LESS than individual strategies.")
    else:
        print("→ The combined strategy equals the sum of individual strategies.")
    
    print(f"\nTotal additional payments: ${1000 * 12 + 10000:,.2f} over the life of the loan")
    print(f"Interest saved per dollar of extra payment: ${combined_savings / (1000 * 12 + 10000):.3f}")
    
    return {
        'original': original,
        'monthly_only': monthly_result,
        'one_time_only': one_time_result,
        'combined': combined_result
    }

def test_multiple_one_time_payments():
    """Test multiple one-time payments throughout the loan"""
    
    loan_details = LoanDetails(
        loan_amount=300000.0,
        interest_rate=6.0,
        loan_term_years=30,
        start_date=datetime(2025, 1, 1)
    )
    
    calculator = MortgageCalculator(loan_details)
    
    # Multiple one-time payments over several years
    extra_payments = [
        ExtraPayment(ExtraPaymentType.ONE_TIME, 5000.0, datetime(2025, 12, 31)),  # End of year 1
        ExtraPayment(ExtraPaymentType.ONE_TIME, 7500.0, datetime(2026, 12, 31)),  # End of year 2
        ExtraPayment(ExtraPaymentType.ONE_TIME, 10000.0, datetime(2027, 12, 31)), # End of year 3
        ExtraPayment(ExtraPaymentType.ONE_TIME, 15000.0, datetime(2030, 12, 31)), # End of year 6
    ]
    
    print("\n=== Multiple One-Time Payments Test ===\n")
    
    comparison = calculator.calculate_payoff_comparison(extra_payments)
    original = comparison['original']
    with_extra = comparison['with_extra']
    
    total_extra = sum(ep.amount for ep in extra_payments)
    
    print(f"Loan Amount: ${loan_details.loan_amount:,.2f}")
    print(f"Interest Rate: {loan_details.interest_rate}%")
    print(f"Term: {loan_details.loan_term_years} years")
    print()
    
    print("One-Time Payments Schedule:")
    for i, payment in enumerate(extra_payments, 1):
        print(f"  Payment {i}: ${payment.amount:,.2f} on {payment.start_date.strftime('%B %Y')}")
    print(f"  Total Extra Payments: ${total_extra:,.2f}")
    print()
    
    print("Results:")
    print(f"  Original Total Interest: ${original.total_interest:,.2f}")
    print(f"  With Extra Payments Interest: ${with_extra.total_interest:,.2f}")
    print(f"  Interest Saved: ${with_extra.interest_saved:,.2f}")
    print(f"  Time Saved: {with_extra.years_saved:.1f} years")
    print(f"  Return on Extra Payments: {(with_extra.interest_saved / total_extra) * 100:.1f}%")

if __name__ == "__main__":
    # Test the main scenario
    results = test_multiple_payment_strategies()
    
    # Test multiple one-time payments
    test_multiple_one_time_payments()
