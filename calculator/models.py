from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class CalcInput:
    revenue: float
    cost_percent: float
    vat_purchases_percent: float
    rent: float
    fixed_contrib: float
    employees: int
    salary: float
    fot_mode: str
    fot_annual: float
    other_mode: str
    other_percent: float
    other_amount: float
    transition_mode: str
    accumulated_vat_credit: float
    stock_expense_amount: float
    purchases_month_percents: List[float] = field(default_factory=list)
    regime: Optional[str] = None


@dataclass
class CalculationContext:
    cost_of_goods: float
    other_expenses: float
    annual_fot: float
    has_employees: bool
    insurance_standard: float
    total_expenses_common: float
    stock_extra: float
    vat_credit_to_apply: float
    expenses_without_self_contrib: float
    owner_extra_income: float
    owner_extra_income_base: float
    owner_extra_profit: float
    owner_extra_profit_base: float
    insurance_total_income: float
    insurance_total_profit: float
    total_expenses_income_regime: float
    total_expenses_profit_regime: float
    total_expenses_ausn: float


@dataclass
class CalcResult:
    regime: str
    title: str
    revenue: float
    expenses: float
    tax: float
    vat: float
    insurance: float
    total_burden: float
    burden_percent: float
    net_profit: float
    available: bool = True
    extra: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, float]:
        payload = {
            "revenue": self.revenue,
            "expenses": self.expenses,
            "tax": self.tax,
            "vat": self.vat,
            "insurance": self.insurance,
            "total_burden": self.total_burden,
            "burden_percent": self.burden_percent,
            "net_profit": self.net_profit,
        }
        payload.update(self.extra)
        return payload


@dataclass
class CalculationSummary:
    results: List[Tuple[str, Dict[str, float], bool]] = field(default_factory=list)
    top_results: List[Tuple[str, Dict[str, float]]] = field(default_factory=list)
    components: Dict[str, float] = field(default_factory=dict)
