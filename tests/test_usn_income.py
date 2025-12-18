from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calculator.constants import DEFAULT_FIXED_CONTRIB, USN_INCOME_RATE, USN_REDUCTION_LIMIT
from calculator.models import CalcInput, CalculationContext
from calculator.regimes.usn_income import _calculate_usn_tax


def make_calc_input(**overrides) -> CalcInput:
    data = {
        "revenue": 1_000_000,
        "cost_percent": 0.0,
        "vat_purchases_percent": 0.0,
        "rent": 0.0,
        "fixed_contrib": DEFAULT_FIXED_CONTRIB,
        "employees": 0,
        "salary": 0.0,
        "fot_mode": "staff",
        "fot_annual": 0.0,
        "other_mode": "percent",
        "other_percent": 0.0,
        "other_amount": 0.0,
        "transition_mode": "none",
        "accumulated_vat_credit": 0.0,
        "stock_expense_amount": 0.0,
        "purchases_month_percents": [0.0] * 12,
    }
    data.update(overrides)
    return CalcInput(**data)


def make_context(**overrides) -> CalculationContext:
    ctx_data = {
        "cost_of_goods": 0.0,
        "other_expenses": 0.0,
        "annual_fot": 0.0,
        "has_employees": False,
        "insurance_standard": 0.0,
        "total_expenses_common": 0.0,
        "stock_extra": 0.0,
        "vat_credit_to_apply": 0.0,
        "expenses_without_self_contrib": 0.0,
        "owner_extra_income": 0.0,
        "owner_extra_income_base": 0.0,
        "owner_extra_profit": 0.0,
        "owner_extra_profit_base": 0.0,
        "insurance_total_income": 0.0,
        "insurance_total_profit": 0.0,
        "total_expenses_income_regime": 0.0,
        "total_expenses_profit_regime": 0.0,
        "total_expenses_ausn": 0.0,
    }
    ctx_data.update(overrides)
    return CalculationContext(**ctx_data)


def test_usn_income_reduction_limited_with_employees():
    data = make_calc_input(revenue=1_000_000, fixed_contrib=40_000)
    ctx = make_context(
        has_employees=True,
        insurance_standard=25_000,
        owner_extra_income=15_000,
    )

    tax_data = _calculate_usn_tax(data, ctx)
    tax_initial = data.revenue * USN_INCOME_RATE
    expected_limit = tax_initial * USN_REDUCTION_LIMIT

    assert tax_data["reduction_base"] == pytest.approx(40_000)
    assert tax_data["max_reduction"] == pytest.approx(expected_limit)
    assert tax_data["tax_reduction"] == pytest.approx(expected_limit)
    assert tax_data["reduction_from_fixed"] == pytest.approx(0.0)
    assert tax_data["usn_tax"] == pytest.approx(tax_initial - expected_limit)


def test_usn_income_reduction_can_zero_tax_without_employees():
    data = make_calc_input(revenue=500_000, fixed_contrib=50_000)
    ctx = make_context(
        has_employees=False,
        insurance_standard=5_000,
        owner_extra_income=15_000,
    )

    tax_data = _calculate_usn_tax(data, ctx)
    tax_initial = data.revenue * USN_INCOME_RATE

    assert tax_data["reduction_base"] == pytest.approx(20_000)
    assert tax_data["max_reduction"] == pytest.approx(tax_initial)
    assert tax_data["tax_reduction"] == pytest.approx(tax_initial)
    assert tax_data["usn_tax"] == pytest.approx(0.0)
    assert tax_data["reduction_from_fixed"] == pytest.approx(tax_initial - tax_data["reduction_base"])
