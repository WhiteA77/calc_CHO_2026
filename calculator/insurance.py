"""Insurance and personal contribution helpers."""

from typing import Iterable, Optional, Tuple

from .constants import INSURANCE_RATE_ON_FOT, NDFL_BRACKETS_2026, THRESHOLD_1_PERCENT


def calculate_standard_insurance(annual_fot: float) -> float:
    return annual_fot * INSURANCE_RATE_ON_FOT


def calculate_owner_extra_income(revenue: float) -> Tuple[float, float]:
    base_before_threshold = revenue
    taxable = max(0.0, base_before_threshold - THRESHOLD_1_PERCENT)
    return taxable * 0.01, base_before_threshold


def calculate_owner_extra_profit(revenue: float, expenses_without_self_contrib: float) -> Tuple[float, float]:
    base_before_threshold = revenue - expenses_without_self_contrib
    taxable = max(0.0, base_before_threshold - THRESHOLD_1_PERCENT)
    return taxable * 0.01, base_before_threshold


def calculate_progressive_ndfl(
    base: float,
    brackets: Iterable[Tuple[Optional[float], float]] = NDFL_BRACKETS_2026,
) -> float:
    taxable = max(float(base or 0), 0.0)
    tax = 0.0
    prev_limit = 0.0

    for limit, rate in brackets:
        if taxable <= prev_limit:
            break
        upper_bound = taxable if limit is None else min(taxable, float(limit))
        portion = upper_bound - prev_limit
        if portion <= 0:
            break
        tax += portion * rate
        prev_limit = upper_bound

    return tax
