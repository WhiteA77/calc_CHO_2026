from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calculator import CalcInput
from calculator.constants import DEFAULT_FIXED_CONTRIB, DEFAULT_PATENT_COST, THRESHOLD_1_PERCENT
from calculator.engine import _build_context
from calculator.regimes import usn_profit


def make_input(**overrides):
    data = {
        "revenue": 2_000_000,
        "cost_percent": 30,
        "vat_purchases_percent": 0,
        "rent": 200_000,
        "fixed_contrib": DEFAULT_FIXED_CONTRIB,
        "employees": 2,
        "salary": 40_000,
        "fot_mode": "staff",
        "fot_annual": 0.0,
        "other_mode": "percent",
        "other_percent": 5,
        "other_amount": 0.0,
        "transition_mode": "none",
        "accumulated_vat_credit": 0.0,
        "stock_expense_amount": 0.0,
        "patent_cost_year": DEFAULT_PATENT_COST,
        "purchases_month_percents": [100.0] * 12,
    }
    data.update(overrides)
    return CalcInput(**data)


def run_regime(calc_input):
    ctx, _ = _build_context(calc_input)
    result = usn_profit.calculate_usn_profit_no_vat(calc_input, ctx)
    return result, ctx


def test_fixed_contribution_decreases_usn_base():
    data = make_input(
        revenue=1_000_000,
        cost_percent=0,
        rent=0,
        other_percent=0,
        employees=0,
        salary=0.0,
        fixed_contrib=100_000,
    )
    result, ctx = run_regime(data)

    expected_base = data.revenue - ctx.usn_profit_expenses_for_base - ctx.stock_extra
    expected_regular_tax = max(expected_base, 0.0) * 0.15

    assert ctx.usn_profit_expenses_for_base == pytest.approx(ctx.total_expenses_common + data.fixed_contrib)
    assert result.extra["usn_regular_tax"] == pytest.approx(expected_regular_tax)


def test_owner_extra_base_excludes_fixed_contribution():
    data = make_input(
        revenue=1_500_000,
        cost_percent=10,
        rent=150_000,
        other_percent=5,
        employees=1,
        salary=30_000,
        fixed_contrib=80_000,
    )
    _result, ctx = run_regime(data)

    expenses_without_self = (
        ctx.cost_of_goods
        + data.rent
        + ctx.other_expenses
        + ctx.annual_fot
        + ctx.insurance_standard
        + ctx.stock_extra
    )
    expected_base = data.revenue - expenses_without_self
    expected_owner_extra = max(expected_base - THRESHOLD_1_PERCENT, 0.0) * 0.01

    assert ctx.owner_extra_profit_base == pytest.approx(expected_base)
    assert ctx.owner_extra_profit == pytest.approx(expected_owner_extra)


def test_min_tax_applies_when_regular_tax_lower():
    data = make_input(
        revenue=400_000,
        cost_percent=80,
        rent=100_000,
        other_percent=5,
        employees=0,
        salary=0.0,
    )
    result, _ctx = run_regime(data)

    min_tax = data.revenue * 0.01
    assert result.extra["usn_regular_tax"] < min_tax
    assert result.extra["usn_min_tax"] == pytest.approx(min_tax)
    assert result.tax == pytest.approx(min_tax)


def test_one_percent_not_in_expenses_but_in_burden():
    data = make_input(
        revenue=3_000_000,
        cost_percent=20,
        rent=150_000,
        other_percent=5,
        employees=2,
        salary=35_000,
    )
    result, ctx = run_regime(data)

    owner_extra = ctx.owner_extra_profit
    assert owner_extra > 0

    # Expenses reported in the regime match the USN base expenses (без 1%).
    assert result.expenses == pytest.approx(ctx.usn_profit_expenses_for_base)
    assert result.expenses == pytest.approx(ctx.total_expenses_profit_regime)

    # Net profit uses only the USN base expenses and tax (1% is not subtracted twice).
    expected_net = data.revenue - result.expenses - result.tax
    assert result.net_profit == pytest.approx(expected_net)

    # Total burden includes the 1% payment.
    assert ctx.insurance_total_profit == pytest.approx(
        ctx.insurance_standard + owner_extra + data.fixed_contrib
    )
    assert result.total_burden == pytest.approx(result.tax + ctx.insurance_total_profit)
