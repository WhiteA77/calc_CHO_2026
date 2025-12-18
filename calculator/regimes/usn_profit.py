from __future__ import annotations

from typing import Dict

from ..constants import USN_PROFIT_MIN_RATE, USN_PROFIT_RATE, VAT_RATE_REDUCED
from ..models import CalcInput, CalcResult, CalculationContext
from ..vat import calc_vat_charged, calc_vat_deductible, calc_vat_to_pay


def _calc_vat(data: CalcInput, ctx: CalculationContext, vat_rate: float) -> Dict[str, float]:
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


def _calc_usn_profit_tax(data: CalcInput, ctx: CalculationContext) -> Dict[str, float]:
    usn_base = data.revenue - ctx.total_expenses_profit_regime - ctx.stock_extra
    taxable_base = max(usn_base, 0.0)
    tax_regular = taxable_base * USN_PROFIT_RATE
    min_tax = data.revenue * USN_PROFIT_MIN_RATE
    usn_tax = max(tax_regular, min_tax)
    return {
        "tax_regular": tax_regular,
        "min_tax": min_tax,
        "usn_tax": usn_tax,
    }


def calculate_usn_profit_no_vat(data: CalcInput, ctx: CalculationContext) -> CalcResult:
    tax_data = _calc_usn_profit_tax(data, ctx)
    usn_tax = tax_data["usn_tax"]
    vat_to_pay = 0.0
    insurance = ctx.insurance_total_profit
    total_tax_burden = usn_tax + insurance
    net_profit = data.revenue - ctx.total_expenses_profit_regime - usn_tax

    extra = {
        "usn_regular_tax": tax_data["tax_regular"],
        "usn_min_tax": tax_data["min_tax"],
        "fixed_contrib": data.fixed_contrib,
        "owner_extra": ctx.owner_extra_profit,
        "owner_extra_base": ctx.owner_extra_profit_base,
    }

    return CalcResult(
        regime="usn_profit_no_vat",
        title="УСН Д-Р 15%",
        revenue=data.revenue,
        expenses=ctx.total_expenses_profit_regime,
        tax=usn_tax,
        vat=vat_to_pay,
        insurance=insurance,
        total_burden=total_tax_burden,
        burden_percent=(total_tax_burden / data.revenue * 100) if data.revenue > 0 else 0.0,
        net_profit=net_profit,
        extra=extra,
    )


def calculate_usn_profit_with_vat(data: CalcInput, ctx: CalculationContext, vat_rate: float) -> CalcResult:
    tax_data = _calc_usn_profit_tax(data, ctx)
    vat_values = _calc_vat(data, ctx, vat_rate)

    usn_tax = tax_data["usn_tax"]
    vat_to_pay = vat_values["vat_to_pay"]
    insurance = ctx.insurance_total_profit

    total_tax_burden = usn_tax + vat_to_pay + insurance
    net_profit = data.revenue - ctx.total_expenses_profit_regime - usn_tax - vat_to_pay

    extra = {
        "usn_regular_tax": tax_data["tax_regular"],
        "usn_min_tax": tax_data["min_tax"],
        "fixed_contrib": data.fixed_contrib,
        "owner_extra": ctx.owner_extra_profit,
        "owner_extra_base": ctx.owner_extra_profit_base,
        "vat_charged": vat_values["vat_charged"],
        "vat_deductible": vat_values["vat_deductible"],
        "vat_extra_credit": vat_values["extra_credit"],
    }

    return CalcResult(
        regime=f"usn_profit_vat_{vat_rate}",
        title=f"УСН Д-Р 15% + НДС {int(vat_rate)}%",
        revenue=data.revenue,
        expenses=ctx.total_expenses_profit_regime,
        tax=usn_tax,
        vat=vat_to_pay,
        insurance=insurance,
        total_burden=total_tax_burden,
        burden_percent=(total_tax_burden / data.revenue * 100) if data.revenue > 0 else 0.0,
        net_profit=net_profit,
        extra=extra,
    )
