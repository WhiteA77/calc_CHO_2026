from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calculator import CalcInput
from calculator.constants import DEFAULT_FIXED_CONTRIB, DEFAULT_PATENT_COST, THRESHOLD_1_PERCENT
from calculator.engine import _build_context
from calculator.regimes import patent


def make_input(**overrides) -> CalcInput:
    data = {
        "revenue": 2_000_000,
        "cost_percent": 30,
        "vat_purchases_percent": 0,
        "rent": 150_000,
        "fixed_contrib": DEFAULT_FIXED_CONTRIB,
        "employees": 0,
        "salary": 0.0,
        "fot_mode": "staff",
        "fot_annual": 0.0,
        "other_mode": "percent",
        "other_percent": 5,
        "other_amount": 0.0,
        "transition_mode": "none",
        "accumulated_vat_credit": 0.0,
        "stock_expense_amount": 0.0,
        "patent_cost_year": DEFAULT_PATENT_COST,
        "patent_pvd_period": 0.0,
        "purchases_month_percents": [100.0] * 12,
    }
    data.update(overrides)
    return CalcInput(**data)


def run_patent(calc_input: CalcInput):
    ctx, _ = _build_context(calc_input)
    result = patent.calculate_patent(calc_input, ctx)
    return result, ctx


def test_patent_manual_pvd_used_for_owner_extra():
    manual_pvd = 800_000
    data = make_input(
        patent_cost_year=150_000,
        patent_pvd_period=manual_pvd,
        fixed_contrib=DEFAULT_FIXED_CONTRIB,
    )
    result, _ = run_patent(data)

    expected_base = manual_pvd
    expected_owner_extra = max(expected_base - THRESHOLD_1_PERCENT, 0) * 0.01

    assert result.extra["patent_pvd_used"] == pytest.approx(expected_base)
    assert result.extra["owner_extra"] == pytest.approx(expected_owner_extra)
    assert result.extra["contrib_self"] == pytest.approx(data.fixed_contrib + expected_owner_extra)


def test_patent_auto_pvd_used_when_not_provided():
    patent_cost = 180_000
    data = make_input(
        patent_cost_year=patent_cost,
        patent_pvd_period=0.0,
    )
    result, _ = run_patent(data)

    expected_pvd = patent_cost / 0.06
    expected_owner_extra = max(expected_pvd - THRESHOLD_1_PERCENT, 0) * 0.01

    assert result.extra["patent_pvd_auto"] == 1
    assert result.extra["patent_pvd_used"] == pytest.approx(expected_pvd)
    assert result.extra["owner_extra"] == pytest.approx(expected_owner_extra)


def test_patent_full_deduction_without_employees():
    data = make_input(
        revenue=1_200_000,
        cost_percent=20,
        patent_cost_year=120_000,
        fixed_contrib=200_000,
    )
    result, ctx = run_patent(data)

    assert ctx.annual_fot == pytest.approx(0.0)
    assert not ctx.has_employees
    assert result.extra["tax_deduction_limit"] == pytest.approx(result.extra["tax_before_deduction"])
    assert result.extra["tax_deduction"] == pytest.approx(result.extra["tax_before_deduction"])
    assert result.tax == pytest.approx(0.0)


def test_patent_deduction_capped_with_employees():
    data = make_input(
        patent_cost_year=200_000,
        fixed_contrib=200_000,
        employees=2,
        salary=50_000,
    )
    result, ctx = run_patent(data)

    assert ctx.has_employees
    expected_limit = data.patent_cost_year * 0.5
    assert result.extra["tax_deduction_limit"] == pytest.approx(expected_limit)
    assert result.extra["tax_deduction"] == pytest.approx(expected_limit)
    assert result.tax == pytest.approx(data.patent_cost_year - expected_limit)


def test_patent_net_profit_matches_formula():
    data = make_input(
        revenue=5_000_000,
        cost_percent=40,
        rent=300_000,
        other_percent=10,
        employees=1,
        salary=60_000,
        patent_cost_year=150_000,
    )
    result, ctx = run_patent(data)

    expenses = ctx.cost_of_goods + data.rent + ctx.other_expenses + ctx.annual_fot
    contrib_workers = ctx.insurance_standard
    contrib_self = result.extra["contrib_self"]
    expected_net = data.revenue - expenses - result.tax - contrib_workers - contrib_self

    assert result.net_profit == pytest.approx(expected_net)
    assert result.extra["net_profit_cash"] == pytest.approx(expected_net)
