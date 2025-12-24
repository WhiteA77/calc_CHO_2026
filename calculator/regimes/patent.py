from __future__ import annotations

from ..constants import THRESHOLD_1_PERCENT
from ..models import CalcInput, CalcResult, CalculationContext

PATENT_RATE = 0.06


def calculate_patent(data: CalcInput, ctx: CalculationContext) -> CalcResult:
    revenue = data.revenue
    expenses_total = ctx.cost_of_goods + data.rent + ctx.other_expenses + ctx.annual_fot

    tax_before_deduction = max(data.patent_cost_year, 0.0)
    manual_pvd = max(data.patent_pvd_period, 0.0)
    auto_pvd = tax_before_deduction / PATENT_RATE if tax_before_deduction > 0 else 0.0
    pvd_used = manual_pvd if manual_pvd > 0 else auto_pvd

    contrib_workers = ctx.insurance_standard
    owner_extra_base = pvd_used
    owner_extra = max(owner_extra_base - THRESHOLD_1_PERCENT, 0.0) * 0.01
    contrib_self = data.fixed_contrib + owner_extra

    deductible_contrib = contrib_self + contrib_workers
    has_employees_limit = ctx.annual_fot > 0.0 and data.employees > 0
    deduction_limit_ratio = 0.5 if has_employees_limit else 1.0
    deduction_limit = tax_before_deduction * deduction_limit_ratio
    tax_deduction = min(deductible_contrib, deduction_limit)
    tax_payable = max(tax_before_deduction - tax_deduction, 0.0)

    net_profit_accounting = revenue - expenses_total - tax_payable
    net_profit_cash = net_profit_accounting - contrib_self - contrib_workers

    total_burden = tax_payable + contrib_self + contrib_workers
    burden_percent = (total_burden / revenue * 100) if revenue > 0 else 0.0

    pvd_source = "input" if manual_pvd > 0 else "auto"

    extra = {
        "income_without_vat": revenue,
        "expenses_without_vat": expenses_total,
        "net_profit_accounting": net_profit_accounting,
        "net_profit_cash": net_profit_cash,
        "tax_before_deduction": tax_before_deduction,
        "tax_deduction": tax_deduction,
        "tax_deduction_limit": deduction_limit,
        "tax_payable": tax_payable,
        "deductible_contrib": deductible_contrib,
        "contrib_self": contrib_self,
        "contrib_workers": contrib_workers,
        "contrib_self_extra": owner_extra,
        "contrib_self_extra_base": owner_extra_base,
        "owner_extra": owner_extra,
        "owner_extra_base": owner_extra_base,
        "fixed_contrib": data.fixed_contrib,
        "has_employees_patent_limit": 1 if has_employees_limit else 0,
        "total_payments": total_burden,
        "patent_cost_year": data.patent_cost_year,
        "patent_pvd_period": manual_pvd,
        "patent_pvd_used": pvd_used,
        "patent_pvd_auto": 0 if manual_pvd > 0 else 1,
        "patent_pvd_source": pvd_source,
    }

    return CalcResult(
        regime="patent",
        title="ПСН (патент)",
        revenue=revenue,
        expenses=expenses_total,
        tax=tax_payable,
        vat=0.0,
        insurance=contrib_self + contrib_workers,
        total_burden=total_burden,
        burden_percent=burden_percent,
        net_profit=net_profit_cash,
        extra=extra,
    )
