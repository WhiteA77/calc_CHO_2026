from __future__ import annotations

from dataclasses import replace
from typing import Callable, Dict, List, Optional, Tuple
from .insurance import (
    calculate_owner_extra_income,
    calculate_owner_extra_profit,
    calculate_standard_insurance,
)
from .models import CalcInput, CalcResult, CalculationContext, CalculationSummary
from .regimes import ausn, osno, patent, usn_income, usn_profit
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
    total_expenses_profit_regime = total_expenses_common + data.fixed_contrib
    usn_profit_expenses_for_base = total_expenses_profit_regime
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
        usn_profit_expenses_for_base=usn_profit_expenses_for_base,
        total_expenses_ausn=total_expenses_ausn,
    )

    components = {
        "cost_of_goods": cost_of_goods,
        "revenue": data.revenue,
        "patent_cost_year": data.patent_cost_year,
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
        "vat_share_cogs": data.vat_share_cogs,
        "vat_share_rent": data.vat_share_rent if data.vat_share_rent is not None else 1.0,
        "vat_share_other": data.vat_share_other if data.vat_share_other is not None else 1.0,
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


RegimeCalculator = Callable[[CalcInput, CalculationContext], Optional[CalcResult]]

REGIME_CALCULATORS: Dict[str, RegimeCalculator] = {
    "ausn_income": ausn.calculate_ausn_8,
    "ausn_profit": ausn.calculate_ausn_20_monthly,
    "usn_income_no_vat": usn_income.calculate_usn_income_no_vat,
    "usn_income_vat_5": lambda d, c: usn_income.calculate_usn_income_with_vat(d, c, 5),
    "usn_income_vat_22": lambda d, c: usn_income.calculate_usn_income_with_vat(d, c, 22),
    "usn_profit_no_vat": usn_profit.calculate_usn_profit_no_vat,
    "usn_profit_vat_5": lambda d, c: usn_profit.calculate_usn_profit_with_vat(d, c, 5),
    "usn_profit_vat_22": lambda d, c: usn_profit.calculate_usn_profit_with_vat(d, c, 22),
    "osno_ooo": osno.calculate_osno_ooo,
    "osno_ip": osno.calculate_osno_ip,
    "patent": patent.calculate_patent,
}


def _clone_input_for_multiplier(data: CalcInput, ctx: CalculationContext, multiplier: float) -> Optional[CalcInput]:
    if multiplier <= 0:
        return None
    revenue = data.revenue * multiplier
    if revenue <= 0:
        return None
    base_cogs = ctx.cost_of_goods
    cost_percent = (base_cogs / revenue * 100.0) if revenue > 0 else 0.0

    return replace(
        data,
        revenue=revenue,
        cost_percent=cost_percent,
        other_mode="absolute",
        other_amount=ctx.other_expenses,
        fot_mode="annual",
        fot_annual=ctx.annual_fot,
    )


def _calculate_regime_profit(
    regime_id: str,
    calc_input: CalcInput,
    ctx: CalculationContext,
    multiplier: float,
) -> Optional[float]:
    calculator = REGIME_CALCULATORS.get(regime_id)
    if not calculator:
        return None
    adjusted_input = _clone_input_for_multiplier(calc_input, ctx, multiplier)
    if not adjusted_input:
        return None
    adjusted_ctx, _components = _build_context(adjusted_input)
    result = calculator(adjusted_input, adjusted_ctx)
    if not result:
        return None
    return result.net_profit


def _find_multiplier_to_target(
    regime_id: str,
    calc_input: CalcInput,
    ctx: CalculationContext,
    target_profit: float,
    base_profit: float,
    max_multiplier: float = 3.0,
) -> Optional[float]:
    tolerance = 1.0
    if base_profit >= target_profit - tolerance:
        return 1.0

    def evaluate(mult: float, cache: Dict[float, Optional[float]]) -> Optional[float]:
        if mult in cache:
            return cache[mult]
        profit = _calculate_regime_profit(regime_id, calc_input, ctx, mult)
        cache[mult] = profit
        return profit

    cache: Dict[float, Optional[float]] = {}
    low = 1.0
    high = max_multiplier
    high_profit = evaluate(high, cache)
    attempts = 0
    while high_profit is None and high - low > 1e-4 and attempts < 20:
        high = (high + low) / 2.0
        high_profit = evaluate(high, cache)
        attempts += 1

    if high_profit is None or high_profit < target_profit - tolerance:
        return None

    for _ in range(60):
        if high - low <= 1e-4:
            break
        mid = (low + high) / 2.0
        profit = evaluate(mid, cache)
        if profit is None:
            high = mid
            high_profit = profit
            continue
        if profit >= target_profit - tolerance:
            high = mid
            high_profit = profit
        else:
            low = mid

    final_profit = evaluate(high, cache)
    if final_profit is None or final_profit < target_profit - tolerance:
        return None
    return high


def _apply_patent_targets(
    calc_input: CalcInput,
    ctx: CalculationContext,
    available_results: Dict[str, CalcResult],
) -> None:
    patent_result = available_results.get("patent")
    if not patent_result:
        return

    target_profit = patent_result.net_profit
    base_revenue = calc_input.revenue
    base_cogs = ctx.cost_of_goods
    if base_revenue <= 0:
        return

    gross_margin_current = (base_revenue - base_cogs) / base_revenue
    has_valid_cogs_share = base_revenue > 0 and base_cogs > 0
    cogs_share_current_percent = (base_cogs / base_revenue * 100.0) if has_valid_cogs_share else None
    patent_metrics = {
        "price_uplift_percent": 0.0,
        "price_uplift_multiplier": 1.0,
        "gross_margin_current_percent": gross_margin_current * 100.0,
        "gross_margin_needed_percent": gross_margin_current * 100.0,
        "gross_margin_delta_pp": 0.0,
        "cogs_share_current_percent": cogs_share_current_percent,
        "cogs_share_after_uplift_percent": cogs_share_current_percent,
        "price_uplift_unattainable": False,
        "target_profit_patent": target_profit,
    }
    patent_result.extra.update(patent_metrics)

    if target_profit is None:
        return

    for regime_id, result in available_results.items():
        if regime_id == "patent":
            continue
        base_profit = result.net_profit
        if base_profit is None:
            continue
        multiplier = _find_multiplier_to_target(regime_id, calc_input, ctx, target_profit, base_profit)
        if multiplier is None:
            result.extra.update(
                {
                    "price_uplift_percent": None,
                    "price_uplift_multiplier": None,
                    "gross_margin_current_percent": gross_margin_current * 100.0,
                    "gross_margin_needed_percent": None,
                    "gross_margin_delta_pp": None,
                    "cogs_share_current_percent": cogs_share_current_percent,
                    "cogs_share_after_uplift_percent": None,
                    "price_uplift_unattainable": True,
                    "target_profit_patent": target_profit,
                }
            )
            continue

        gross_margin_needed = (base_revenue * multiplier - base_cogs) / (base_revenue * multiplier)
        cogs_share_after_percent = (
            (cogs_share_current_percent / multiplier)
            if (cogs_share_current_percent is not None and multiplier > 0)
            else None
        )
        metrics = {
            "price_uplift_percent": (multiplier - 1.0) * 100.0,
            "price_uplift_multiplier": multiplier,
            "gross_margin_current_percent": gross_margin_current * 100.0,
            "gross_margin_needed_percent": gross_margin_needed * 100.0,
            "gross_margin_delta_pp": (gross_margin_needed - gross_margin_current) * 100.0,
            "cogs_share_current_percent": cogs_share_current_percent,
            "cogs_share_after_uplift_percent": cogs_share_after_percent,
            "price_uplift_unattainable": False,
            "target_profit_patent": target_profit,
        }
        result.extra.update(metrics)


def run_calculation(data: CalcInput) -> CalculationSummary:
    ctx, components = _build_context(data)
    summary = CalculationSummary()

    rows: List[Tuple[str, Optional[CalcResult], bool]] = []
    available_results: Dict[str, CalcResult] = {}

    def add_result(result: Optional[CalcResult], title_unavailable: str) -> None:
        if result:
            rows.append((result.title, result, True))
            available_results[result.regime] = result
        else:
            rows.append((title_unavailable, None, False))

    # АУСН 8%
    add_result(ausn.calculate_ausn_8(data, ctx), "АУСН 8% (нельзя применять — превышены лимиты)")

    # АУСН 20%
    add_result(
        ausn.calculate_ausn_20_monthly(data, ctx),
        "АУСН 20% (нельзя применять — превышены лимиты)",
    )

    # УСН Доходы 6% без НДС
    add_result(usn_income.calculate_usn_income_no_vat(data, ctx), "")

    # УСН Доходы 6% + НДС 5%
    add_result(usn_income.calculate_usn_income_with_vat(data, ctx, 5), "")

    # УСН Доходы 6% + НДС 22%
    add_result(usn_income.calculate_usn_income_with_vat(data, ctx, 22), "")

    # УСН Д-Р 15% без НДС
    add_result(usn_profit.calculate_usn_profit_no_vat(data, ctx), "")

    # УСН Д-Р 15% + НДС 5%
    add_result(usn_profit.calculate_usn_profit_with_vat(data, ctx, 5), "")

    # УСН Д-Р 15% + НДС 22%
    add_result(usn_profit.calculate_usn_profit_with_vat(data, ctx, 22), "")

    # ОСНО + НДС 22% (ООО)
    add_result(osno.calculate_osno_ooo(data, ctx), "")

    # ОСНО + НДС 22% (ИП)
    add_result(osno.calculate_osno_ip(data, ctx), "")

    # ПСН (патент)
    add_result(patent.calculate_patent(data, ctx), "")

    _apply_patent_targets(data, ctx, available_results)

    summary.components = components

    for title, result, ok in rows:
        if result and ok:
            summary.results.append(_wrap_result(result))
        else:
            message = title or "Режим недоступен"
            summary.results.append((message, None, False))

    available: List[Tuple[str, Dict[str, float]]] = [
        (name, payload) for name, payload, ok in summary.results if ok and payload
    ]
    summary.top_results = sorted(
        available,
        key=lambda item: (item[1]["total_burden"], -item[1]["net_profit"]),
    )[:5]

    return summary
