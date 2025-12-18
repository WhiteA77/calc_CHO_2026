from __future__ import annotations

from typing import Dict, List, Tuple
from .insurance import (
    calculate_owner_extra_income,
    calculate_owner_extra_profit,
    calculate_standard_insurance,
)
from .models import CalcInput, CalcResult, CalculationContext, CalculationSummary
from .regimes import ausn, osno, usn_income, usn_profit
from .utils import compute_annual_fot, compute_cost_of_goods, compute_other_expenses


def _build_context(data: CalcInput) -> Tuple[CalculationContext, Dict[str, float]]:
    cost_of_goods = compute_cost_of_goods(data)
    other_expenses = compute_other_expenses(data)
    annual_fot = compute_annual_fot(data)
    has_employees = annual_fot > 0
    insurance_standard = calculate_standard_insurance(annual_fot)

    total_expenses_common = cost_of_goods + data.rent + other_expenses + annual_fot + insurance_standard
    stock_extra = data.stock_expense_amount if data.transition_mode == "stock" else 0.0
    vat_credit_to_apply = data.accumulated_vat_credit if data.transition_mode == "vat" else 0.0

    expenses_without_self_contrib = (
        cost_of_goods
        + data.rent
        + other_expenses
        + annual_fot
        + insurance_standard
        + stock_extra
    )

    owner_extra_income, owner_extra_income_base = calculate_owner_extra_income(data.revenue)
    owner_extra_profit, owner_extra_profit_base = calculate_owner_extra_profit(
        data.revenue,
        expenses_without_self_contrib,
    )

    insurance_total_income = insurance_standard + owner_extra_income + data.fixed_contrib
    insurance_total_profit = insurance_standard + owner_extra_profit + data.fixed_contrib

    total_expenses_income_regime = total_expenses_common + owner_extra_income + data.fixed_contrib
    total_expenses_profit_regime = total_expenses_common + owner_extra_profit + data.fixed_contrib
    total_expenses_ausn = cost_of_goods + data.rent + other_expenses + annual_fot

    ctx = CalculationContext(
        cost_of_goods=cost_of_goods,
        other_expenses=other_expenses,
        annual_fot=annual_fot,
        has_employees=has_employees,
        insurance_standard=insurance_standard,
        total_expenses_common=total_expenses_common,
        stock_extra=stock_extra,
        vat_credit_to_apply=vat_credit_to_apply,
        expenses_without_self_contrib=expenses_without_self_contrib,
        owner_extra_income=owner_extra_income,
        owner_extra_income_base=owner_extra_income_base,
        owner_extra_profit=owner_extra_profit,
        owner_extra_profit_base=owner_extra_profit_base,
        insurance_total_income=insurance_total_income,
        insurance_total_profit=insurance_total_profit,
        total_expenses_income_regime=total_expenses_income_regime,
        total_expenses_profit_regime=total_expenses_profit_regime,
        total_expenses_ausn=total_expenses_ausn,
    )

    components = {
        "cost_of_goods": cost_of_goods,
        "revenue": data.revenue,
        "rent": data.rent,
        "other_expenses": other_expenses,
        "annual_fot": annual_fot,
        "has_employees": has_employees,
        "insurance_standard": insurance_standard,
        "fixed_contrib": data.fixed_contrib,
        "owner_extra_income": owner_extra_income,
        "owner_extra_income_base": owner_extra_income_base,
        "owner_extra_profit": owner_extra_profit,
        "owner_extra_profit_base": owner_extra_profit_base,
        "vat_purchases_percent": data.vat_purchases_percent,
        "accumulated_vat_credit": data.accumulated_vat_credit,
        "stock_expense_amount": data.stock_expense_amount,
        "stock_extra": stock_extra,
        "transition_mode": data.transition_mode,
    }

    return ctx, components


def _wrap_result(result: CalcResult) -> Tuple[str, Dict[str, float], bool]:
    payload = result.to_dict()
    payload["regime_id"] = result.regime
    return result.title, payload, result.available


def run_calculation(data: CalcInput) -> CalculationSummary:
    ctx, components = _build_context(data)
    summary = CalculationSummary()

    # АУСН 8%
    ausn_8 = ausn.calculate_ausn_8(data, ctx)
    if ausn_8:
        summary.results.append(_wrap_result(ausn_8))
    else:
        summary.results.append(("АУСН 8% (нельзя применять — превышены лимиты)", None, False))

    # АУСН 20%
    ausn_20 = ausn.calculate_ausn_20_monthly(data, ctx)
    if ausn_20:
        summary.results.append(_wrap_result(ausn_20))
    else:
        summary.results.append(("АУСН 20% (нельзя применять — превышены лимиты)", None, False))

    # УСН Доходы 6% без НДС
    summary.results.append(_wrap_result(usn_income.calculate_usn_income_no_vat(data, ctx)))

    # УСН Доходы 6% + НДС 5%
    summary.results.append(_wrap_result(usn_income.calculate_usn_income_with_vat(data, ctx, 5)))

    # УСН Доходы 6% + НДС 22%
    summary.results.append(_wrap_result(usn_income.calculate_usn_income_with_vat(data, ctx, 22)))

    # УСН Д-Р 15% без НДС
    summary.results.append(_wrap_result(usn_profit.calculate_usn_profit_no_vat(data, ctx)))

    # УСН Д-Р 15% + НДС 5%
    summary.results.append(_wrap_result(usn_profit.calculate_usn_profit_with_vat(data, ctx, 5)))

    # УСН Д-Р 15% + НДС 22%
    summary.results.append(_wrap_result(usn_profit.calculate_usn_profit_with_vat(data, ctx, 22)))

    # ОСНО + НДС 22% (ООО)
    summary.results.append(_wrap_result(osno.calculate_osno_ooo(data, ctx)))

    # ОСНО + НДС 22% (ИП)
    summary.results.append(_wrap_result(osno.calculate_osno_ip(data, ctx)))

    summary.components = components

    available: List[Tuple[str, Dict[str, float]]] = [
        (name, payload) for name, payload, ok in summary.results if ok and payload
    ]
    summary.top_results = sorted(
        available,
        key=lambda item: (item[1]["total_burden"], -item[1]["net_profit"]),
    )[:5]

    return summary
