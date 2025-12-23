from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calculator import CalcInput, run_calculation
from calculator.constants import DEFAULT_FIXED_CONTRIB, DEFAULT_PATENT_COST, THRESHOLD_1_PERCENT


def build_input(**overrides):
    data = {
        "revenue": 12_000_000,
        "cost_percent": 45,
        "vat_purchases_percent": 65,
        "rent": 600_000,
        "fixed_contrib": DEFAULT_FIXED_CONTRIB,
        "employees": 4,
        "salary": 55_000,
        "fot_mode": "staff",
        "fot_annual": 0.0,
        "other_mode": "percent",
        "other_percent": 12,
        "other_amount": 0.0,
        "transition_mode": "none",
        "accumulated_vat_credit": 0.0,
        "stock_expense_amount": 0.0,
        "patent_cost_year": DEFAULT_PATENT_COST,
        "purchases_month_percents": [100.0] * 12,
    }
    data.update(overrides)
    return CalcInput(**data)


def extract_results(calc_input):
    summary = run_calculation(calc_input)
    mapping = {}
    for name, payload, ok in summary.results:
        if ok and payload:
            mapping[name] = payload
    return mapping


def test_osno_ip_matches_ooo_business_expenses():
    input_data = build_input()
    results = extract_results(input_data)

    ip = results["ОСНО + НДС 22% (ИП)"]
    ooo = results["ОСНО + НДС 22% (ООО)"]

    assert ip["vat"] == pytest.approx(ooo["vat"])
    assert ip["expenses"] == pytest.approx(ooo["expenses"])
    assert ip["insurance"] > ooo["insurance"]

    ndfl_base = ip["ndfl_base"]
    assert ndfl_base < 5_000_000
    if ndfl_base > 0:
        assert ip["tax"] < 0.25 * ndfl_base
    else:
        assert ip["tax"] == pytest.approx(0.0)


def test_osno_ip_owner_contrib_affects_base_and_cash_profit():
    input_data = build_input(
        revenue=1_000_000,
        cost_percent=0,
        vat_purchases_percent=0,
        rent=0,
        employees=0,
        salary=0,
        other_percent=0,
        fixed_contrib=50_000,
    )
    results = extract_results(input_data)
    ip = results["ОСНО + НДС 22% (ИП)"]

    income_without_vat = ip["income_without_vat"]
    expenses_without_vat = ip["expenses_without_vat"]
    profit_before_owner = income_without_vat - expenses_without_vat
    owner_extra = max(profit_before_owner - THRESHOLD_1_PERCENT, 0) * 0.01
    owner_contrib_total = ip["fixed_contrib"] + ip["owner_extra"]

    # База для 1% не уменьшается на фиксированный взнос
    assert ip["owner_extra_base"] == pytest.approx(profit_before_owner)
    assert ip["owner_extra"] == pytest.approx(owner_extra)

    # Чистая прибыль учитывает взносы ИП
    expected_net_profit_cash = (
        income_without_vat
        - expenses_without_vat
        - owner_contrib_total
        - ip["ndfl_tax"]
        - ip["vat_payable"]
    )
    assert owner_contrib_total > 0
    assert ip["net_profit_cash"] == pytest.approx(expected_net_profit_cash)


def test_osno_ooo_cash_profit_uses_vat_to_pay():
    input_data = build_input(
        transition_mode="vat",
        accumulated_vat_credit=10_000_000,
    )
    results = extract_results(input_data)
    ooo = results["ОСНО + НДС 22% (ООО)"]

    assert ooo["vat_payable"] < 0
    assert ooo["vat"] == pytest.approx(0.0)
    assert ooo["net_profit_cash"] == pytest.approx(ooo["net_profit_accounting"] - ooo["vat"])
