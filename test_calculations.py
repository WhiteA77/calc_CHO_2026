#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pytest checks verifying calculator outputs stay stable."""

from dataclasses import replace

import pytest

from calculator import CalcInput, run_calculation
from calculator.constants import DEFAULT_FIXED_CONTRIB, VAT_RATE_STANDARD
from calculator.utils import format_number


@pytest.fixture(scope="module")
def calc_input():
    purchases_template = [100.0] * 12
    return CalcInput(
        revenue=10_000_000,
        cost_percent=40,
        vat_purchases_percent=70,
        rent=500_000,
        fixed_contrib=DEFAULT_FIXED_CONTRIB,
        employees=3,
        salary=50_000,
        fot_mode="staff",
        fot_annual=0.0,
        other_mode="percent",
        other_percent=10,
        other_amount=0.0,
        transition_mode="none",
        accumulated_vat_credit=0.0,
        stock_expense_amount=0.0,
        purchases_month_percents=purchases_template,
    )


@pytest.fixture(scope="module")
def summary(calc_input):
    return run_calculation(calc_input)


def _build_results_map(summary):
    mapping = {}
    for name, data, ok in summary.results:
        if ok and data:
            mapping[name] = data
    return mapping


@pytest.fixture(scope="module")
def results_map(summary):
    return _build_results_map(summary)


def test_ausn_income(results_map):
    result = results_map["АУСН 8%"]
    assert result["tax"] == pytest.approx(800_000)
    assert result["total_burden"] == pytest.approx(857_390)
    assert result["net_profit"] == pytest.approx(1_842_610)
    assert result["burden_percent"] == pytest.approx(8.5739)


def test_ausn_profit(results_map):
    result = results_map["АУСН 20%"]
    assert result["tax"] == pytest.approx(540_000)
    assert result["total_burden"] == pytest.approx(597_390)
    assert result["net_profit"] == pytest.approx(2_102_610)


def test_usn_income_vat5(results_map):
    result = results_map["УСН Доходы 6% + НДС 5%"]
    assert result["tax"] == pytest.approx(300_000)
    assert result["vat"] == pytest.approx(476_190.4761904762)
    assert result["total_burden"] == pytest.approx(1_470_580.4761904762)
    assert result["net_profit"] == pytest.approx(1_229_419.5238095238)


def test_usn_profit_vat5(results_map):
    result = results_map["УСН Д-Р 15% + НДС 5%"]
    assert result["tax"] == pytest.approx(315_391.5)
    assert result["vat"] == pytest.approx(476_190.4761904762)
    assert result["total_burden"] == pytest.approx(1_407_571.9761904762)
    assert result["net_profit"] == pytest.approx(1_311_028.0238095238)


def test_usn_profit_vat22(results_map):
    result = results_map["УСН Д-Р 15% + НДС 22%"]
    assert result["vat"] == pytest.approx(1_298_360.6557377048)
    assert result["total_burden"] == pytest.approx(2_229_742.1557377046)
    assert result["net_profit"] == pytest.approx(488_857.84426229517)


def test_osno_ooo(results_map):
    result = results_map["ОСНО + НДС 22% (ООО)"]
    assert result["tax"] == pytest.approx(283_032.78688524594)
    assert result["vat"] == pytest.approx(1_027_868.8524590164)
    assert result["total_burden"] == pytest.approx(1_850_901.6393442624)
    assert result["net_profit"] == pytest.approx(-178_770.49180327856)


def test_osno_ip(results_map):
    result = results_map["ОСНО + НДС 22% (ИП)"]
    assert result["tax"] == pytest.approx(138_709.18568852462)
    assert result["vat"] == pytest.approx(1_027_868.8524590164)
    assert result["total_burden"] == pytest.approx(1_771_715.449622951)
    assert result["net_profit"] == pytest.approx(-34_446.89060655725)
    assert result["ndfl_base"] == pytest.approx(1_066_993.736065574)


def test_format_number():
    assert format_number(1_234_567) == "1 234 567"
    assert format_number(0) == "0"
    assert format_number(None) == "–"


def test_osno_revenue_net_less_than_gross(results_map):
    result = results_map["ОСНО + НДС 22% (ООО)"]
    assert result["income_without_vat"] < result["revenue"]


def test_osno_profit_base_uses_net_revenue(results_map):
    result = results_map["ОСНО + НДС 22% (ООО)"]
    expected_base = result["income_without_vat"] - result["expenses_without_vat"]
    assert result["profit_tax_base"] == pytest.approx(expected_base)


def test_osno_net_profit_independent_of_vat(calc_input):
    data_with_credit = replace(
        calc_input,
        transition_mode="vat",
        accumulated_vat_credit=1_000_000,
    )
    data_without_credit = replace(
        calc_input,
        transition_mode="none",
        accumulated_vat_credit=0.0,
    )
    summary_with_credit = run_calculation(data_with_credit)
    summary_without_credit = run_calculation(data_without_credit)

    with_credit = _build_results_map(summary_with_credit)["ОСНО + НДС 22% (ООО)"]
    without_credit = _build_results_map(summary_without_credit)["ОСНО + НДС 22% (ООО)"]

    assert with_credit["vat"] != pytest.approx(without_credit["vat"])
    diff = with_credit["net_profit"] - without_credit["net_profit"]
    assert diff == pytest.approx(data_with_credit.accumulated_vat_credit)
    assert with_credit["net_profit_accounting"] == pytest.approx(without_credit["net_profit_accounting"])
    assert with_credit["tax"] == pytest.approx(without_credit["tax"])
    assert with_credit["profit_tax_base"] == pytest.approx(without_credit["profit_tax_base"])


def test_osno_vat_output_formula(results_map):
    result = results_map["ОСНО + НДС 22% (ООО)"]
    expected_vat = result["revenue"] * VAT_RATE_STANDARD / (100 + VAT_RATE_STANDARD)
    assert result["vat_charged"] == pytest.approx(expected_vat)


def test_osno_insurance_counted_once(summary, results_map):
    result = results_map["ОСНО + НДС 22% (ООО)"]
    components = summary.components
    insurance_standard = components["insurance_standard"]
    stock_part = components["stock_extra"] if components["stock_extra"] > 0 else 0.0
    cost_of_goods_net = max(components["cost_of_goods"] - result["vat_deductible"], 0.0)
    expected_expenses = (
        cost_of_goods_net
        + components["rent"]
        + components["other_expenses"]
        + components["annual_fot"]
        + insurance_standard
        + stock_part
    )

    assert result["insurance"] == pytest.approx(insurance_standard)
    assert result["expenses_without_vat"] == pytest.approx(expected_expenses)


def test_osno_revenue_without_vat_matches_division(results_map):
    result = results_map["ОСНО + НДС 22% (ООО)"]
    divisor = 1 + VAT_RATE_STANDARD / 100
    expected_revenue_net = result["revenue"] / divisor
    assert result["income_without_vat"] == pytest.approx(expected_revenue_net)


def test_osno_cogs_without_vat_matches_division(calc_input):
    data = replace(calc_input, vat_purchases_percent=100)
    summary = run_calculation(data)
    result = _build_results_map(summary)["ОСНО + НДС 22% (ООО)"]
    cost_of_goods = summary.components["cost_of_goods"]
    divisor = 1 + VAT_RATE_STANDARD / 100
    assert result["cogs_no_vat"] == pytest.approx(cost_of_goods / divisor)


def test_osno_cash_profit_matches_accounting_minus_vat(results_map):
    result = results_map["ОСНО + НДС 22% (ООО)"]
    expected_cash = result["net_profit_accounting"] - result["vat_payable"]
    assert result["net_profit"] == pytest.approx(expected_cash)


def test_osno_total_payments_breakdown(results_map):
    result = results_map["ОСНО + НДС 22% (ООО)"]
    expected_payments = result["tax"] + max(result["vat_payable"], 0) + result["insurance"]
    assert result["total_payments"] == pytest.approx(expected_payments)
    assert result["total_burden"] == pytest.approx(result["total_payments"])
