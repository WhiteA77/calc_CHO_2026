from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calculator import CalcInput, run_calculation
from calculator.constants import DEFAULT_FIXED_CONTRIB


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
