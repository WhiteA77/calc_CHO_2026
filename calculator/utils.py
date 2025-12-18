from __future__ import annotations

from typing import Optional

from .models import CalcInput


def money_round(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return round(float(value), 2)


def clamp(value: float, min_value: Optional[float] = None, max_value: Optional[float] = None) -> float:
    if min_value is not None:
        value = max(value, min_value)
    if max_value is not None:
        value = min(value, max_value)
    return value


def percent_of(base: float, percent: float) -> float:
    return base * percent / 100.0


def compute_cost_of_goods(data: CalcInput) -> float:
    return percent_of(data.revenue, data.cost_percent)


def compute_other_expenses(data: CalcInput) -> float:
    if data.other_mode == "percent":
        return percent_of(data.revenue, data.other_percent)
    return data.other_amount


def compute_annual_fot(data: CalcInput) -> float:
    if data.fot_mode == "annual":
        return data.fot_annual
    return data.employees * data.salary * 12


def format_number(num):
    """Форматирует число с разделителями тысяч."""
    if num is None:
        return "–"
    return f"{num:,.0f}".replace(",", " ")
