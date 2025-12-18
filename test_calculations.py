#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pytest checks verifying calculator outputs stay stable."""

import pytest

from calculator import CalcInput, run_calculation
from calculator.constants import DEFAULT_FIXED_CONTRIB
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


@pytest.fixture(scope="module")
def results_map(summary):
    mapping = {}
    for name, data, ok in summary.results:
        if ok and data:
            mapping[name] = data
    return mapping


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
    assert result["tax"] == pytest.approx(201_062.3360655738)
    assert result["vat"] == pytest.approx(1_298_360.6557377048)
    assert result["total_burden"] == pytest.approx(2_115_412.9918032787)
    assert result["net_profit"] == pytest.approx(603_187.0081967213)


def test_osno_ip(results_map):
    result = results_map["ОСНО + НДС 22% (ИП)"]
    assert result["tax"] == pytest.approx(103_896.89060655743)
    assert result["vat"] == pytest.approx(1_298_360.6557377048)
    assert result["total_burden"] == pytest.approx(2_004_690.0397868853)
    assert result["net_profit"] == pytest.approx(695_309.960213115)
    assert result["ndfl_base"] == pytest.approx(799_206.8508196725)


def test_format_number():
    assert format_number(1_234_567) == "1 234 567"
    assert format_number(0) == "0"
    assert format_number(None) == "–"
