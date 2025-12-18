import pytest

from calculator import CalcInput, run_calculation
from calculator.constants import DEFAULT_FIXED_CONTRIB


def build_input(**overrides):
    data = {
        "revenue": 8_000_000,
        "cost_percent": 35,
        "vat_purchases_percent": 60,
        "rent": 400_000,
        "fixed_contrib": DEFAULT_FIXED_CONTRIB,
        "employees": 4,
        "salary": 45_000,
        "fot_mode": "staff",
        "fot_annual": 0.0,
        "other_mode": "percent",
        "other_percent": 12,
        "other_amount": 0.0,
        "transition_mode": "none",
        "accumulated_vat_credit": 0.0,
        "stock_expense_amount": 0.0,
        "purchases_month_percents": [100.0] * 12,
    }
    data.update(overrides)
    return CalcInput(**data)


def test_run_calculation_smoke():
    input_data = build_input()
    summary = run_calculation(input_data)

    assert len(summary.results) >= 8
    assert summary.top_results
    assert summary.components["fixed_contrib"] == DEFAULT_FIXED_CONTRIB

    usn_income = next(
        data for name, data, ok in summary.results if name == "УСН Доходы 6%" and ok and data
    )
    assert usn_income["revenue"] == pytest.approx(input_data.revenue)
    assert usn_income["tax"] >= 0
    assert usn_income["total_burden"] >= usn_income["tax"]


def test_run_calculation_different_input():
    input_data = build_input(
        revenue=3_500_000,
        cost_percent=20,
        other_mode="amount",
        other_amount=200_000,
        employees=0,
        salary=0.0,
    )
    summary = run_calculation(input_data)
    assert summary.results

    top_names = [name for name, _data in summary.top_results]
    assert any("УСН" in name for name in top_names)

    ausn_result = next(
        (
            data
            for name, data, ok in summary.results
            if name.startswith("АУСН") and ok and data
        ),
        None,
    )
    if ausn_result:
        assert ausn_result["revenue"] == pytest.approx(input_data.revenue)
