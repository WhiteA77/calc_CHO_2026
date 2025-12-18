from __future__ import annotations

from typing import Optional, Tuple

from ..constants import PROFIT_TAX_RATE, VAT_RATE_STANDARD, THRESHOLD_1_PERCENT
from ..insurance import calculate_progressive_ndfl
from ..models import CalcInput, CalcResult, CalculationContext
from ..vat import calc_vat_charged, calc_vat_to_pay


def _normalize_share(value: Optional[float], default: float) -> float:
    """Ensure VAT share stays within 0..1 bounds."""
    if value is None:
        share = default
    else:
        share = value
    if share > 1.0:
        share = share / 100.0
    if share < 0.0:
        return 0.0
    return min(share, 1.0)


def _split_amount_with_vat(amount: float, share_with_vat: float, vat_rate: float) -> Tuple[float, float]:
    """Return VAT portion and net (без НДС) amount for an expense."""
    if amount <= 0.0 or vat_rate <= 0.0 or share_with_vat <= 0.0:
        return 0.0, max(amount, 0.0)
    taxable_amount = amount * share_with_vat
    vat_amount = calc_vat_charged(taxable_amount, vat_rate)
    net_amount = amount - vat_amount
    return vat_amount, max(net_amount, 0.0)


def _build_expense_breakdown(data: CalcInput, ctx: CalculationContext, vat_rate: float):
    stock_part = ctx.stock_extra if ctx.stock_extra > 0 else 0.0
    payroll = ctx.annual_fot
    insurance = ctx.insurance_standard

    cogs_share = _normalize_share(getattr(data, "vat_share_cogs", None), data.vat_purchases_percent)
    rent_share = _normalize_share(getattr(data, "vat_share_rent", None), 1.0)
    other_share = _normalize_share(getattr(data, "vat_share_other", None), 1.0)

    cogs_vat, cogs_net = _split_amount_with_vat(ctx.cost_of_goods, cogs_share, vat_rate)
    rent_vat, rent_net = _split_amount_with_vat(data.rent, rent_share, vat_rate)
    other_vat, other_net = _split_amount_with_vat(ctx.other_expenses, other_share, vat_rate)

    expenses_without_vat = cogs_net + rent_net + other_net + payroll + insurance + stock_part
    vat_deductible_total = cogs_vat + rent_vat + other_vat

    return {
        "stock_part": stock_part,
        "payroll": payroll,
        "insurance": insurance,
        "cogs_net": cogs_net,
        "rent_net": rent_net,
        "other_net": other_net,
        "cogs_vat": cogs_vat,
        "rent_vat": rent_vat,
        "other_vat": other_vat,
        "expenses_without_vat": expenses_without_vat,
        "vat_deductible_total": vat_deductible_total,
    }


def calculate_osno_ooo(data: CalcInput, ctx: CalculationContext) -> CalcResult:
    vat_rate = VAT_RATE_STANDARD
    vat_charged = calc_vat_charged(data.revenue, vat_rate)
    expenses_info = _build_expense_breakdown(data, ctx, vat_rate)
    vat_deductible = expenses_info["vat_deductible_total"]

    vat_payable_balance = vat_charged - vat_deductible - ctx.vat_credit_to_apply
    vat_to_pay = calc_vat_to_pay(vat_charged, vat_deductible, ctx.vat_credit_to_apply)

    revenue_without_vat = data.revenue - vat_charged
    expenses_without_vat = expenses_info["expenses_without_vat"]

    profit_tax_base = revenue_without_vat - expenses_without_vat
    profit_tax = max(profit_tax_base, 0.0) * PROFIT_TAX_RATE
    net_profit_accounting = profit_tax_base - profit_tax
    net_profit_cash = net_profit_accounting - vat_payable_balance

    insurance = expenses_info["insurance"]
    total_payments = profit_tax + vat_to_pay + insurance

    extra = {
        "income_without_vat": revenue_without_vat,
        "expenses_without_vat": expenses_without_vat,
        "profit_tax_base": profit_tax_base,
        "vat_charged": vat_charged,
        "vat_deductible": vat_deductible,
        "vat_extra_credit": ctx.vat_credit_to_apply,
        "vat_payable": vat_payable_balance,
        "vat_refund": max(-vat_payable_balance, 0.0),
        "cogs_no_vat": expenses_info["cogs_net"],
        "rent_no_vat": expenses_info["rent_net"],
        "other_no_vat": expenses_info["other_net"],
        "vat_deductible_cogs": expenses_info["cogs_vat"],
        "vat_deductible_rent": expenses_info["rent_vat"],
        "vat_deductible_other": expenses_info["other_vat"],
        "net_profit_accounting": net_profit_accounting,
        "net_profit_cash": net_profit_cash,
        "total_payments": total_payments,
    }

    return CalcResult(
        regime="osno_ooo",
        title="ОСНО + НДС 22% (ООО)",
        revenue=data.revenue,
        expenses=expenses_without_vat,
        tax=profit_tax,
        vat=vat_to_pay,
        insurance=insurance,
        total_burden=total_payments,
        burden_percent=(total_payments / data.revenue * 100) if data.revenue > 0 else 0.0,
        net_profit=net_profit_cash,
        extra=extra,
    )


def calculate_osno_ip(data: CalcInput, ctx: CalculationContext) -> CalcResult:
    vat_rate = VAT_RATE_STANDARD
    vat_charged = calc_vat_charged(data.revenue, vat_rate)
    expenses_info = _build_expense_breakdown(data, ctx, vat_rate)
    vat_deductible = expenses_info["vat_deductible_total"]
    vat_payable_balance = vat_charged - vat_deductible - ctx.vat_credit_to_apply
    vat_to_pay = calc_vat_to_pay(vat_charged, vat_deductible, ctx.vat_credit_to_apply)

    income_without_vat = data.revenue - vat_charged
    business_expenses_without_vat = expenses_info["expenses_without_vat"]

    base_for_one_percent = income_without_vat - business_expenses_without_vat - data.fixed_contrib
    base_for_one_percent = max(base_for_one_percent, 0.0)
    extra_one_percent = max(base_for_one_percent - THRESHOLD_1_PERCENT, 0.0) * 0.01

    ndfl_base = base_for_one_percent - extra_one_percent
    ndfl_base = max(ndfl_base, 0.0)
    ndfl_tax = calculate_progressive_ndfl(ndfl_base)

    insurance_total = expenses_info["insurance"] + data.fixed_contrib + extra_one_percent
    total_tax_burden = ndfl_tax + vat_to_pay + insurance_total

    net_profit_accounting = income_without_vat - business_expenses_without_vat - ndfl_tax
    net_profit_cash = net_profit_accounting - vat_payable_balance

    extra = {
        "ndfl_base": ndfl_base,
        "income_without_vat": income_without_vat,
        "expenses_without_vat": business_expenses_without_vat,
        "fixed_contrib": data.fixed_contrib,
        "owner_extra": extra_one_percent,
        "owner_extra_base": base_for_one_percent,
        "vat_charged": vat_charged,
        "vat_deductible": vat_deductible,
        "vat_extra_credit": ctx.vat_credit_to_apply,
        "ndfl_tax": ndfl_tax,
        "vat_payable": vat_payable_balance,
        "vat_refund": max(-vat_payable_balance, 0.0),
        "cogs_no_vat": expenses_info["cogs_net"],
        "rent_no_vat": expenses_info["rent_net"],
        "other_no_vat": expenses_info["other_net"],
        "vat_deductible_cogs": expenses_info["cogs_vat"],
        "vat_deductible_rent": expenses_info["rent_vat"],
        "vat_deductible_other": expenses_info["other_vat"],
        "net_profit_accounting": net_profit_accounting,
        "net_profit_cash": net_profit_cash,
        "total_payments": total_tax_burden,
    }

    return CalcResult(
        regime="osno_ip",
        title="ОСНО + НДС 22% (ИП)",
        revenue=data.revenue,
        expenses=business_expenses_without_vat,
        tax=ndfl_tax,
        vat=vat_to_pay,
        insurance=insurance_total,
        total_burden=total_tax_burden,
        burden_percent=(total_tax_burden / data.revenue * 100) if data.revenue > 0 else 0.0,
        net_profit=net_profit_cash,
        extra=extra,
    )
