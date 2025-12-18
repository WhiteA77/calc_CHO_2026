from __future__ import annotations

from ..constants import PROFIT_TAX_RATE, VAT_RATE_STANDARD, THRESHOLD_1_PERCENT
from ..insurance import calculate_progressive_ndfl
from ..models import CalcInput, CalcResult, CalculationContext
from ..vat import calc_vat_charged, calc_vat_deductible, calc_vat_to_pay


def calculate_osno_ooo(data: CalcInput, ctx: CalculationContext) -> CalcResult:
    vat_rate = VAT_RATE_STANDARD
    vat_charged = calc_vat_charged(data.revenue, vat_rate)
    vat_deductible = calc_vat_deductible(ctx.cost_of_goods, data.vat_purchases_percent, vat_rate)
    vat_to_pay = calc_vat_to_pay(vat_charged, vat_deductible, ctx.vat_credit_to_apply)

    profit_tax_base = data.revenue - ctx.total_expenses_profit_regime - ctx.stock_extra - vat_to_pay
    profit_tax = max(profit_tax_base, 0.0) * PROFIT_TAX_RATE

    insurance = ctx.insurance_total_profit
    total_tax_burden = profit_tax + vat_to_pay + insurance
    net_profit = data.revenue - ctx.total_expenses_profit_regime - vat_to_pay - profit_tax

    extra = {
        "fixed_contrib": data.fixed_contrib,
        "owner_extra": ctx.owner_extra_profit,
        "owner_extra_base": ctx.owner_extra_profit_base,
        "vat_charged": vat_charged,
        "vat_deductible": vat_deductible,
        "vat_extra_credit": ctx.vat_credit_to_apply,
    }

    return CalcResult(
        regime="osno_ooo",
        title="ОСНО + НДС 22% (ООО)",
        revenue=data.revenue,
        expenses=ctx.total_expenses_profit_regime,
        tax=profit_tax,
        vat=vat_to_pay,
        insurance=insurance,
        total_burden=total_tax_burden,
        burden_percent=(total_tax_burden / data.revenue * 100) if data.revenue > 0 else 0.0,
        net_profit=net_profit,
        extra=extra,
    )


def calculate_osno_ip(data: CalcInput, ctx: CalculationContext) -> CalcResult:
    vat_rate = VAT_RATE_STANDARD
    vat_charged = calc_vat_charged(data.revenue, vat_rate)
    vat_deductible = calc_vat_deductible(ctx.cost_of_goods, data.vat_purchases_percent, vat_rate)
    vat_to_pay = calc_vat_to_pay(vat_charged, vat_deductible, ctx.vat_credit_to_apply)

    income_without_vat = data.revenue - vat_charged
    stock_part = ctx.stock_extra if ctx.stock_extra > 0 else 0.0

    base_expenses_without_vat = (
        (ctx.cost_of_goods - vat_deductible)
        + data.rent
        + ctx.other_expenses
        + ctx.annual_fot
        + ctx.insurance_standard
        + stock_part
    )

    base_for_one_percent = income_without_vat - base_expenses_without_vat - data.fixed_contrib
    base_for_one_percent = max(base_for_one_percent, 0.0)
    extra_one_percent = max(base_for_one_percent - THRESHOLD_1_PERCENT, 0.0) * 0.01

    ndfl_base = base_for_one_percent - extra_one_percent
    ndfl_base = max(ndfl_base, 0.0)
    ndfl_tax = calculate_progressive_ndfl(ndfl_base)

    insurance_total = ctx.insurance_standard + data.fixed_contrib + extra_one_percent
    total_tax_burden = ndfl_tax + vat_to_pay + insurance_total
    net_profit = (
        income_without_vat
        - base_expenses_without_vat
        - ndfl_tax
        - data.fixed_contrib
        - extra_one_percent
    )

    display_expenses = ctx.total_expenses_common + data.fixed_contrib + extra_one_percent

    extra = {
        "ndfl_base": ndfl_base,
        "income_without_vat": income_without_vat,
        "expenses_without_vat": base_expenses_without_vat,
        "fixed_contrib": data.fixed_contrib,
        "owner_extra": ctx.owner_extra_profit,
        "owner_extra_base": ctx.owner_extra_profit_base,
        "vat_charged": vat_charged,
        "vat_deductible": vat_deductible,
        "vat_extra_credit": ctx.vat_credit_to_apply,
        "ndfl_tax": ndfl_tax,
    }

    return CalcResult(
        regime="osno_ip",
        title="ОСНО + НДС 22% (ИП)",
        revenue=data.revenue,
        expenses=display_expenses,
        tax=ndfl_tax,
        vat=vat_to_pay,
        insurance=insurance_total,
        total_burden=total_tax_burden,
        burden_percent=(total_tax_burden / data.revenue * 100) if data.revenue > 0 else 0.0,
        net_profit=net_profit,
        extra=extra,
    )
