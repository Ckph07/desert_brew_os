"""
Balance Calculator — Consolidated income vs expenses with breakdowns.
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from collections import defaultdict

from models.income import Income
from models.expense import Expense


class BalanceCalculator:
    """
    Calculates financial balance and cashflow from Income and Expense records.
    """

    @staticmethod
    def get_balance(db: Session, days: int = 30) -> dict:
        """
        Get consolidated balance for a period.

        Returns income vs expenses with breakdowns by category and profit center.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        now = datetime.utcnow()

        # Query incomes
        incomes = db.query(Income).filter(Income.received_date >= cutoff).all()
        expenses = db.query(Expense).filter(Expense.paid_date >= cutoff).all()

        # Aggregate income
        total_income = 0.0
        income_by_category = defaultdict(float)
        income_by_pc = defaultdict(float)

        for i in incomes:
            amt = float(i.amount)
            total_income += amt
            income_by_category[i.category] += amt
            income_by_pc[i.profit_center] += amt

        # Aggregate expenses
        total_expenses = 0.0
        expenses_by_category = defaultdict(float)
        expenses_by_pc = defaultdict(float)

        for e in expenses:
            amt = float(e.amount)
            total_expenses += amt
            expenses_by_category[e.category] += amt
            expenses_by_pc[e.profit_center] += amt

        net_profit = total_income - total_expenses
        margin = (net_profit / total_income * 100) if total_income > 0 else 0.0

        return {
            "period_start": cutoff,
            "period_end": now,
            "total_income": round(total_income, 2),
            "total_expenses": round(total_expenses, 2),
            "net_profit": round(net_profit, 2),
            "profit_margin_percentage": round(margin, 2),
            "income_by_category": {k: round(v, 2) for k, v in income_by_category.items()},
            "expenses_by_category": {k: round(v, 2) for k, v in expenses_by_category.items()},
            "income_by_profit_center": {k: round(v, 2) for k, v in income_by_pc.items()},
            "expenses_by_profit_center": {k: round(v, 2) for k, v in expenses_by_pc.items()},
        }

    @staticmethod
    def get_cashflow(db: Session, months: int = 6) -> dict:
        """
        Get monthly cashflow for the last N months.

        Returns income, expenses, and net by month.
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(days=months * 31)  # approximate

        incomes = db.query(Income).filter(Income.received_date >= cutoff).all()
        expenses = db.query(Expense).filter(Expense.paid_date >= cutoff).all()

        # Group by month
        monthly_income = defaultdict(float)
        monthly_expense = defaultdict(float)

        for i in incomes:
            key = i.received_date.strftime("%Y-%m")
            monthly_income[key] += float(i.amount)

        for e in expenses:
            key = e.paid_date.strftime("%Y-%m")
            monthly_expense[key] += float(e.amount)

        # Build all months in range
        all_months = sorted(set(list(monthly_income.keys()) + list(monthly_expense.keys())))
        entries = []
        total_income = 0.0
        total_expense = 0.0

        for m in all_months:
            inc = monthly_income.get(m, 0.0)
            exp = monthly_expense.get(m, 0.0)
            total_income += inc
            total_expense += exp
            entries.append({
                "month": m,
                "income": round(inc, 2),
                "expenses": round(exp, 2),
                "net": round(inc - exp, 2),
            })

        return {
            "period_start": cutoff,
            "period_end": now,
            "months": entries,
            "total_income": round(total_income, 2),
            "total_expenses": round(total_expense, 2),
            "total_net": round(total_income - total_expense, 2),
        }
