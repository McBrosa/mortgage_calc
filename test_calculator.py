"""
Test the mortgage calculator functionality
"""

from datetime import datetime
from mortgage_calculator import (
    MortgageCalculator, 
    MortgageAnalyzer,
    LoanDetails, 
    ExtraPayment, 
    ExtraPaymentType
)

def test_basic_calculation():
    """Test basic mortgage calculation"""
    print("Testing Basic Mortgage Calculation...")
    
    # Use generic sample loan details
    loan_details = LoanDetails(
        loan_amount=300000.0,
        interest_rate=6.5,
        loan_term_years=30,
        start_date=datetime(2026, 1, 1)
    )
    
    calculator = MortgageCalculator(loan_details)
    
    # Calculate basic payment
    monthly_payment = calculator.calculate_monthly_payment()
    print(f"Monthly P&I Payment: ${monthly_payment:.2f}")
    
    # Test with extra payment
    extra_payment = ExtraPayment(
        payment_type=ExtraPaymentType.MONTHLY,
        amount=500.0
    )
    
    comparison = calculator.calculate_payoff_comparison([extra_payment])
    original = comparison['original']
    with_extra = comparison['with_extra']
    
    print(f"\nOriginal Scenario:")
    print(f"  Monthly Payment: ${original.monthly_payment:.2f}")
    print(f"  Total Interest: ${original.total_interest:,.2f}")
    print(f"  Payoff Date: {original.payoff_date.strftime('%b %Y')}")
    
    print(f"\nWith Extra $500/month:")
    print(f"  Monthly Payment: ${with_extra.monthly_payment:.2f}")
    print(f"  Total Interest: ${with_extra.total_interest:,.2f}")
    print(f"  New Payoff Date: {with_extra.payoff_date.strftime('%b %Y')}")
    print(f"  Time Saved: {with_extra.years_saved:.1f} years")
    print(f"  Interest Saved: ${with_extra.interest_saved:,.2f}")
    
    return calculator

def test_amortization_schedule():
    """Test amortization schedule generation"""
    print("\n" + "="*50)
    print("Testing Amortization Schedule...")
    
    loan_details = LoanDetails(
        loan_amount=300000.0,
        interest_rate=6.5,
        loan_term_years=30,
        start_date=datetime(2026, 1, 1)
    )
    
    calculator = MortgageCalculator(loan_details)
    
    # Generate schedule with extra payment
    extra_payment = ExtraPayment(
        payment_type=ExtraPaymentType.MONTHLY,
        amount=500.0
    )
    
    schedule = calculator.generate_amortization_schedule([extra_payment])
    
    print(f"Generated {len(schedule)} payments")
    print(f"Final payment date: {schedule.iloc[-1]['date'].strftime('%b %Y')}")
    print(f"Total interest paid: ${schedule['interest_payment'].sum():,.2f}")
    
    # Show first few payments
    print("\nFirst 5 payments:")
    print(schedule[['payment_number', 'date', 'monthly_payment', 'extra_payment', 
                  'principal_payment', 'interest_payment', 'ending_balance']].head().to_string())

def test_multiple_strategies():
    """Test combining multiple payment strategies"""
    print("\n" + "="*50)
    print("Testing Multiple Payment Strategies...")
    
    loan_details = LoanDetails(
        loan_amount=300000.0,
        interest_rate=6.5,
        loan_term_years=30,
        start_date=datetime(2026, 1, 1)
    )
    
    calculator = MortgageCalculator(loan_details)
    
    # Multiple strategies
    strategies = [
        # Strategy 1: Extra monthly payment only
        [ExtraPayment(ExtraPaymentType.MONTHLY, 500.0)],
        
        # Strategy 2: Smaller monthly + one-time payment
        [
            ExtraPayment(ExtraPaymentType.MONTHLY, 800.0),
            ExtraPayment(ExtraPaymentType.ONE_TIME, 10000.0, datetime(2026, 1, 1))
        ],
        
        # Strategy 3: Multiple one-time payments
        [
            ExtraPayment(ExtraPaymentType.ONE_TIME, 5000.0, datetime(2026, 1, 1)),
            ExtraPayment(ExtraPaymentType.ONE_TIME, 5000.0, datetime(2027, 1, 1)),
            ExtraPayment(ExtraPaymentType.ONE_TIME, 5000.0, datetime(2028, 1, 1))
        ]
    ]
    
    analyzer = MortgageAnalyzer(calculator)
    results = analyzer.analyze_payment_strategies(strategies)
    
    print("Strategy Comparison:")
    print(results[['strategy', 'years_saved', 'interest_saved', 'total_extra_payments']].to_string())

if __name__ == "__main__":
    test_basic_calculation()
    test_amortization_schedule()
    test_multiple_strategies()
    print("\n" + "="*50)
    print("All tests completed successfully!")
