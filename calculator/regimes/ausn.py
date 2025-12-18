from __future__ import annotations

from typing import Optional

from ..constants import (
    AUSN_EMPLOYEE_LIMIT,
    AUSN_INCOME_RATE,
    AUSN_PROFIT_MIN_RATE,
    AUSN_PROFIT_RATE,
    AUSN_REVENUE_LIMIT,
)
from ..models import CalcInput, CalcResult, CalculationContext


def _check_limits(data: CalcInput) -> bool:
    return data.revenue <= AUSN_REVENUE_LIMIT and data.employees <= AUSN_EMPLOYEE_LIMIT


def calculate_ausn_8(data: CalcInput, ctx: CalculationContext) -> Optional[CalcResult]:
    if not _check_limits(data):
        return None

    tax = data.revenue * AUSN_INCOME_RATE
    vat = 0.0
    insurance = data.fixed_contrib
    total_tax_burden = tax + insurance
    net_profit = data.revenue - ctx.total_expenses_ausn - tax - data.fixed_contrib

    return CalcResult(
        regime="ausn_income",
        title="АУСН 8%",
        revenue=data.revenue,
        expenses=ctx.total_expenses_ausn,
        tax=tax,
        vat=vat,
        insurance=insurance,
        total_burden=total_tax_burden,
        burden_percent=(total_tax_burden / data.revenue * 100) if data.revenue > 0 else 0.0,
        net_profit=net_profit,
        extra={"fixed_contrib": data.fixed_contrib},
    )


def _calc_ausn_20_base(data: CalcInput, expenses: float) -> float:
    base = data.revenue - expenses
    return max(base, 0.0)


def calculate_ausn_20(data: CalcInput, ctx: CalculationContext) -> Optional[CalcResult]:
    if not _check_limits(data):
        return None

    base_for_tax = _calc_ausn_20_base(data, ctx.total_expenses_ausn)
    tax_by_base = base_for_tax * AUSN_PROFIT_RATE
    min_tax = data.revenue * AUSN_PROFIT_MIN_RATE
    tax = max(tax_by_base, min_tax)
    vat = 0.0
    insurance = data.fixed_contrib
    total_tax_burden = tax + insurance
    net_profit = data.revenue - ctx.total_expenses_ausn - tax - data.fixed_contrib

    return CalcResult(
        regime="ausn_profit",
        title="АУСН 20%",
        revenue=data.revenue,
        expenses=ctx.total_expenses_ausn,
        tax=tax,
        vat=vat,
        insurance=insurance,
        total_burden=total_tax_burden,
        burden_percent=(total_tax_burden / data.revenue * 100) if data.revenue > 0 else 0.0,
        net_profit=net_profit,
        extra={"ausn_tax_base": base_for_tax, "fixed_contrib": data.fixed_contrib},
    )


def calculate_ausn_20_monthly(data: CalcInput, ctx: CalculationContext) -> Optional[CalcResult]:
    # В текущей версии параметр покупки по месяцам не влияет на расчёты,
    # но оставлен для совместимости с UI.
    return calculate_ausn_20(data, ctx)
