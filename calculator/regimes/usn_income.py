from __future__ import annotations

from typing import Dict

from ..constants import USN_INCOME_RATE, USN_REDUCTION_LIMIT, VAT_RATE_REDUCED
from ..models import CalcInput, CalcResult, CalculationContext
from ..vat import calc_vat_charged, calc_vat_deductible, calc_vat_to_pay


def _calculate_usn_tax(data: CalcInput, ctx: CalculationContext) -> Dict[str, float]:
    tax_initial = data.revenue * USN_INCOME_RATE
    reduction_base = ctx.insurance_standard
    max_reduction = tax_initial * USN_REDUCTION_LIMIT
    reduction_from_standard = min(reduction_base, max_reduction)

    if ctx.has_employees:
        available_for_fixed = max(max_reduction - reduction_from_standard, 0.0)
        reduction_from_fixed = min(data.fixed_contrib, available_for_fixed)
    else:
        max_without_standard = max(tax_initial - reduction_from_standard, 0.0)
        reduction_from_fixed = min(data.fixed_contrib, max_without_standard)

    tax_reduction = reduction_from_standard + reduction_from_fixed
    usn_tax = max(tax_initial - tax_reduction, 0.0)

    return {
        "tax_initial": tax_initial,
        "tax_reduction": tax_reduction,
        "max_reduction": max_reduction,
        "reduction_base": reduction_base,
        "reduction_from_fixed": reduction_from_fixed,
        "usn_tax": usn_tax,
    }


def _calculate_vat(data: CalcInput, ctx: CalculationContext, vat_rate: float) -> Dict[str, float]:
    vat_charged = calc_vat_charged(data.revenue, vat_rate)

    if vat_rate == VAT_RATE_REDUCED:
        vat_deductible = 0.0
        extra_credit = 0.0
    else:
        vat_deductible = calc_vat_deductible(
            ctx.cost_of_goods,
            data.vat_purchases_percent,
            vat_rate,
        )
        extra_credit = ctx.vat_credit_to_apply

    vat_to_pay = calc_vat_to_pay(vat_charged, vat_deductible, extra_credit)
    return {
        "vat_to_pay": vat_to_pay,
        "vat_charged": vat_charged,
        "vat_deductible": vat_deductible,
        "extra_credit": extra_credit,
    }


def calculate_usn_income_no_vat(data: CalcInput, ctx: CalculationContext) -> CalcResult:
    tax_data = _calculate_usn_tax(data, ctx)
    vat_to_pay = 0.0
    insurance = ctx.insurance_total_income
    usn_tax = tax_data["usn_tax"]

    total_tax_burden = usn_tax + insurance
    net_profit = data.revenue - ctx.total_expenses_income_regime - usn_tax

    extra = {
        "tax_initial": tax_data["tax_initial"],
        "tax_reduction": tax_data["tax_reduction"],
        "tax_reduction_limit": tax_data["max_reduction"],
        "tax_reduction_base": tax_data["reduction_base"],
        "fixed_contrib": data.fixed_contrib,
        "fixed_contrib_reduction": tax_data["reduction_from_fixed"],
        "owner_extra": ctx.owner_extra_income,
        "owner_extra_base": ctx.owner_extra_income_base,
    }

    return CalcResult(
        regime="usn_income_no_vat",
        title="УСН Доходы 6%",
        revenue=data.revenue,
        expenses=ctx.total_expenses_income_regime,
        tax=usn_tax,
        vat=vat_to_pay,
        insurance=insurance,
        total_burden=total_tax_burden,
        burden_percent=(total_tax_burden / data.revenue * 100) if data.revenue > 0 else 0.0,
        net_profit=net_profit,
        extra=extra,
    )


def calculate_usn_income_with_vat(data: CalcInput, ctx: CalculationContext, vat_rate: float) -> CalcResult:
    tax_data = _calculate_usn_tax(data, ctx)
    vat_values = _calculate_vat(data, ctx, vat_rate)
    usn_tax = tax_data["usn_tax"]
    vat_to_pay = vat_values["vat_to_pay"]
    insurance = ctx.insurance_total_income

    total_tax_burden = usn_tax + vat_to_pay + insurance
    net_profit = data.revenue - ctx.total_expenses_income_regime - usn_tax - vat_to_pay

    extra = {
        "tax_initial": tax_data["tax_initial"],
        "tax_reduction": tax_data["tax_reduction"],
        "tax_reduction_limit": tax_data["max_reduction"],
        "tax_reduction_base": tax_data["reduction_base"],
        "fixed_contrib": data.fixed_contrib,
        "fixed_contrib_reduction": tax_data["reduction_from_fixed"],
        "owner_extra": ctx.owner_extra_income,
        "owner_extra_base": ctx.owner_extra_income_base,
    }

    return CalcResult(
        regime=f"usn_income_vat_{vat_rate}",
        title=f"УСН Доходы 6% + НДС {int(vat_rate)}%",
        revenue=data.revenue,
        expenses=ctx.total_expenses_income_regime,
        tax=usn_tax,
        vat=vat_to_pay,
        insurance=insurance,
        total_burden=total_tax_burden,
        burden_percent=(total_tax_burden / data.revenue * 100) if data.revenue > 0 else 0.0,
        net_profit=net_profit,
        extra=extra,
    )
