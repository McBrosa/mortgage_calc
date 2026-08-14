"""
Mortgage Calculator Classes
Contains the core logic for mortgage calculations including amortization,
early payoff scenarios, and payment schedule generation.
"""

import dataclasses
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class PaymentFrequency(Enum):
    MONTHLY = "monthly"
    BIWEEKLY = "biweekly"


class ExtraPaymentType(Enum):
    MONTHLY = "monthly"
    BIWEEKLY = "biweekly"
    ONE_TIME = "one_time"


@dataclass
class LoanDetails:
    """Loan details for mortgage calculations"""
    loan_amount: float
    interest_rate: float  # Annual interest rate as percentage
    loan_term_years: int
    start_date: datetime
    annual_taxes: float = 0.0
    home_insurance: float = 0.0
    hoa_dues: float = 0.0
    pmi: float = 0.0


@dataclass
class ExtraPayment:
    """Extra payment configuration"""
    payment_type: ExtraPaymentType
    amount: float
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@dataclass
class PaymentResult:
    """Result of payment calculation"""
    monthly_payment: float
    total_payments: float
    total_interest: float
    payoff_date: datetime
    years_saved: float = 0.0
    interest_saved: float = 0.0


class MortgageCalculator:
    """Core mortgage calculation engine"""
    
    def __init__(self, loan_details: LoanDetails):
        self.loan_details = loan_details
        self.monthly_interest_rate = loan_details.interest_rate / 100 / 12
        self.total_payments = loan_details.loan_term_years * 12
    
    def calculate_monthly_payment(self) -> float:
        """Calculate the basic monthly P&I payment"""
        if self.monthly_interest_rate == 0:
            return self.loan_details.loan_amount / self.total_payments
        
        payment = self.loan_details.loan_amount * (
            self.monthly_interest_rate * (1 + self.monthly_interest_rate) ** self.total_payments
        ) / ((1 + self.monthly_interest_rate) ** self.total_payments - 1)
        
        return payment
    
    def calculate_total_monthly_payment(self) -> float:
        """Calculate total monthly payment including taxes, insurance, etc."""
        base_payment = self.calculate_monthly_payment()
        monthly_taxes = self.loan_details.annual_taxes / 12
        monthly_insurance = self.loan_details.home_insurance / 12
        monthly_hoa = self.loan_details.hoa_dues / 12
        monthly_pmi = self.loan_details.pmi / 12
        
        return base_payment + monthly_taxes + monthly_insurance + monthly_hoa + monthly_pmi
    
    def generate_amortization_schedule(self, extra_payments: List[ExtraPayment] = None) -> pd.DataFrame:
        """Generate complete amortization schedule with optional extra payments"""
        if extra_payments is None:
            extra_payments = []
        
        schedule = []
        current_balance = self.loan_details.loan_amount
        monthly_payment = self.calculate_monthly_payment()
        current_date = self.loan_details.start_date
        payment_number = 0
        
        while current_balance > 0.01 and payment_number < self.total_payments * 2:  # Safety limit
            payment_number += 1
            
            # Calculate interest for this period
            interest_payment = current_balance * self.monthly_interest_rate
            
            # Calculate principal payment
            # Guard: if monthly_payment <= interest_payment the loan cannot amortize normally
            raw_principal = monthly_payment - interest_payment
            if raw_principal <= 0:
                # Cannot amortize; break to avoid infinite loop
                break
            principal_payment = min(raw_principal, current_balance)
            
            # Calculate extra payments for this period
            extra_payment_amount = self._calculate_extra_payment_for_period(
                current_date, extra_payments, payment_number
            )
            
            # Apply extra payment to principal; clamp to remaining balance
            total_principal = min(principal_payment + extra_payment_amount, current_balance)
            applied_extra = max(0.0, total_principal - principal_payment)
            unused_extra = extra_payment_amount - applied_extra

            # Update balance
            current_balance -= total_principal

            # Add to schedule
            schedule.append({
                'payment_number': payment_number,
                'date': current_date,
                'beginning_balance': current_balance + total_principal,
                'monthly_payment': monthly_payment,
                'principal_payment': principal_payment,
                'interest_payment': interest_payment,
                'extra_payment': applied_extra,
                'unused_extra': unused_extra,
                'total_payment': monthly_payment + applied_extra,
                'ending_balance': current_balance
            })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return pd.DataFrame(schedule)
    
    def _calculate_extra_payment_for_period(
        self, 
        current_date: datetime, 
        extra_payments: List[ExtraPayment],
        payment_number: int
    ) -> float:
        """Calculate total extra payment for a specific period"""
        total_extra = 0.0
        
        for extra_payment in extra_payments:
            if extra_payment.payment_type == ExtraPaymentType.MONTHLY:
                # Check if within date range
                if (extra_payment.start_date is None or current_date >= extra_payment.start_date) and \
                   (extra_payment.end_date is None or current_date <= extra_payment.end_date):
                    total_extra += extra_payment.amount
            
            elif extra_payment.payment_type == ExtraPaymentType.BIWEEKLY:
                # Biweekly model: 26 payments/year = 1 extra monthly payment per year.
                # amount is passed as full monthly_payment from app.py; apply amount/12 each month
                # so total extra per year equals exactly one monthly payment.
                if (extra_payment.start_date is None or current_date >= extra_payment.start_date) and \
                   (extra_payment.end_date is None or current_date <= extra_payment.end_date):
                    total_extra += extra_payment.amount / 12
            
            elif extra_payment.payment_type == ExtraPaymentType.ONE_TIME:
                # One-time payment on specific date
                if extra_payment.start_date and \
                   current_date.year == extra_payment.start_date.year and \
                   current_date.month == extra_payment.start_date.month:
                    total_extra += extra_payment.amount
        
        return total_extra
    
    def calculate_payoff_comparison(self, extra_payments: List[ExtraPayment] = None) -> Dict[str, PaymentResult]:
        """Compare original vs extra payment scenarios"""
        # Original scenario
        original_schedule = self.generate_amortization_schedule([])
        original_result = PaymentResult(
            monthly_payment=self.calculate_monthly_payment(),
            total_payments=original_schedule['total_payment'].sum(),
            total_interest=original_schedule['interest_payment'].sum(),
            payoff_date=original_schedule.iloc[-1]['date']
        )
        
        # Extra payment scenario
        if extra_payments:
            extra_schedule = self.generate_amortization_schedule(extra_payments)
            extra_result = PaymentResult(
                monthly_payment=self.calculate_monthly_payment(),
                total_payments=extra_schedule['total_payment'].sum(),
                total_interest=extra_schedule['interest_payment'].sum(),
                payoff_date=extra_schedule.iloc[-1]['date'],
                years_saved=(len(original_schedule) - len(extra_schedule)) / 12,
                interest_saved=original_result.total_interest - extra_schedule['interest_payment'].sum()
            )
        else:
            # Return an independent copy to prevent aliasing/mutation of original_result
            extra_result = dataclasses.replace(original_result)

        return {
            'original': original_result,
            'with_extra': extra_result
        }


class MortgageAnalyzer:
    """Advanced mortgage analysis and reporting"""
    
    def __init__(self, calculator: MortgageCalculator):
        self.calculator = calculator
    
    def analyze_payment_strategies(self, strategies: List[List[ExtraPayment]]) -> pd.DataFrame:
        """Analyze multiple payment strategies"""
        results = []
        
        for i, strategy in enumerate(strategies):
            comparison = self.calculator.calculate_payoff_comparison(strategy)
            result = comparison['with_extra']
            
            # Compute total extra paid by running the schedule so units match _calculate_extra_payment_for_period
            strategy_schedule = self.calculator.generate_amortization_schedule(strategy)
            months_active = len(strategy_schedule)
            total_extra = 0.0
            for ep in strategy:
                if ep.payment_type == ExtraPaymentType.MONTHLY:
                    total_extra += ep.amount * months_active
                elif ep.payment_type == ExtraPaymentType.BIWEEKLY:
                    # amount/12 per month, so total = amount/12 * months_active
                    total_extra += (ep.amount / 12) * months_active
                elif ep.payment_type == ExtraPaymentType.ONE_TIME:
                    total_extra += ep.amount

            results.append({
                'strategy': f'Strategy {i+1}',
                'monthly_payment': result.monthly_payment,
                'total_interest': result.total_interest,
                'payoff_date': result.payoff_date,
                'years_saved': result.years_saved,
                'interest_saved': result.interest_saved,
                'total_extra_payments': total_extra
            })
        
        return pd.DataFrame(results)
    
    def get_balance_over_time(self, extra_payments: List[ExtraPayment] = None) -> pd.DataFrame:
        """Get mortgage balance over time for charting"""
        schedule = self.calculator.generate_amortization_schedule(extra_payments)
        
        return schedule[['date', 'ending_balance']].copy()
    
    def calculate_break_even_analysis(self, extra_payment_amount: float) -> Dict:
        """Calculate break-even point for extra payments vs investing"""
        # This is a simplified analysis - could be expanded
        extra_payment = ExtraPayment(
            payment_type=ExtraPaymentType.MONTHLY,
            amount=extra_payment_amount
        )
        
        extra_schedule = self.calculator.generate_amortization_schedule([extra_payment])
        comparison = self.calculator.calculate_payoff_comparison([extra_payment])

        # total_extra_paid = extra amount * number of months the loan was actually active
        return {
            'years_saved': comparison['with_extra'].years_saved,
            'interest_saved': comparison['with_extra'].interest_saved,
            'total_extra_paid': extra_payment_amount * len(extra_schedule)
        }