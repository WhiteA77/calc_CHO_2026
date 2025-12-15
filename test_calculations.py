#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Набор PyTest-проверок для расчётных функций калькулятора."""

import pytest

from app import (
    calculate_ausn_8,
    calculate_ausn_20,
    calculate_ausn_20_monthly,
    calculate_owner_extra_profit,
    calculate_usn_income,
    calculate_usn_income_minus_expenses,
    calculate_osno,
    calculate_osno_ip,
    format_number,
    DEFAULT_FIXED_CONTRIB,
)


@pytest.fixture(scope="module")
def sample_inputs():
    """Базовый набор данных из описания калькулятора."""
    revenue = 10_000_000
    cost_percent = 40
    cost_of_goods = revenue * cost_percent / 100
    rent = 500_000
    employees = 3
    salary = 50_000
    annual_fot = employees * salary * 12
    insurance_standard = annual_fot * 0.30
    other_percent = 10
    other_expenses = revenue * other_percent / 100
    vat_purchases_percent = 70
    fixed_contrib = DEFAULT_FIXED_CONTRIB
    stock_extra = 0.0

    expenses_without_self_contrib = (
        cost_of_goods
        + rent
        + other_expenses
        + annual_fot
        + insurance_standard
        + stock_extra
    )
    owner_extra_profit, owner_extra_profit_base = calculate_owner_extra_profit(
        revenue,
        expenses_without_self_contrib,
    )
    insurance_total = insurance_standard + owner_extra_profit + fixed_contrib
    total_expenses_common = cost_of_goods + rent + other_expenses + annual_fot + insurance_standard
    total_expenses = total_expenses_common + owner_extra_profit + fixed_contrib
    total_expenses_ausn = total_expenses - insurance_total
    purchases_template = [100.0] * 12

    return {
        "revenue": revenue,
        "employees": employees,
        "vat_purchases_percent": vat_purchases_percent,
        "cost_of_goods": cost_of_goods,
        "rent": rent,
        "other_expenses": other_expenses,
        "annual_fot": annual_fot,
        "purchases_template": purchases_template,
        "insurance_standard": insurance_standard,
        "insurance_total": insurance_total,
        "total_expenses_common": total_expenses_common,
        "total_expenses": total_expenses,
        "total_expenses_ausn": total_expenses_ausn,
        "fixed_contrib": fixed_contrib,
        "has_employees": annual_fot > 0,
        "owner_extra_profit": owner_extra_profit,
        "owner_extra_profit_base": owner_extra_profit_base,
        "stock_extra": stock_extra,
    }


def test_calculate_ausn_8(sample_inputs):
    result = calculate_ausn_8(
        sample_inputs["revenue"],
        sample_inputs["total_expenses_ausn"],
        sample_inputs["employees"],
        fixed_contrib=sample_inputs["fixed_contrib"],
    )
    assert result is not None
    assert result["tax"] == pytest.approx(800_000)
    assert result["total_burden"] == pytest.approx(857_390)
    assert result["net_profit"] == pytest.approx(1_842_610)
    assert result["burden_percent"] == pytest.approx(8.5739)


def test_calculate_ausn_20(sample_inputs):
    result = calculate_ausn_20(
        sample_inputs["revenue"],
        sample_inputs["total_expenses_ausn"],
        sample_inputs["employees"],
        fixed_contrib=sample_inputs["fixed_contrib"],
    )
    assert result is not None
    assert result["tax"] == pytest.approx(540_000)
    assert result["total_burden"] == pytest.approx(597_390)
    assert result["net_profit"] == pytest.approx(2_102_610)
    assert result["burden_percent"] == pytest.approx(5.9739)


def test_calculate_ausn_20_monthly(sample_inputs):
    result = calculate_ausn_20_monthly(
        revenue=sample_inputs["revenue"],
        cost_of_goods=sample_inputs["cost_of_goods"],
        rent=sample_inputs["rent"],
        other_expenses=sample_inputs["other_expenses"],
        annual_fot=sample_inputs["annual_fot"],
        purchases_month_percents=sample_inputs["purchases_template"],
        employees=sample_inputs["employees"],
        fixed_contrib=sample_inputs["fixed_contrib"],
    )
    assert result is not None
    assert result["tax"] == pytest.approx(540_000)
    assert result["total_burden"] == pytest.approx(597_390)
    assert result["net_profit"] == pytest.approx(2_102_610)


def test_calculate_usn_income(sample_inputs):
    result = calculate_usn_income(
        sample_inputs["revenue"],
        sample_inputs["total_expenses"],
        sample_inputs["insurance_total"],
        sample_inputs["insurance_standard"],
        5,
        sample_inputs["vat_purchases_percent"],
        sample_inputs["cost_of_goods"],
        fixed_contrib=sample_inputs["fixed_contrib"],
        has_employees=sample_inputs["has_employees"],
    )
    assert result["tax"] == pytest.approx(300_000)
    assert result["vat"] == pytest.approx(476_190.4761904762)
    assert result["total_burden"] == pytest.approx(1_392_180.4761904762)
    assert result["net_profit"] == pytest.approx(1_307_819.5238095238)


def test_calculate_usn_income_minus_expenses_5(sample_inputs):
    result = calculate_usn_income_minus_expenses(
        sample_inputs["revenue"],
        sample_inputs["total_expenses"],
        sample_inputs["insurance_total"],
        5,
        sample_inputs["vat_purchases_percent"],
        sample_inputs["cost_of_goods"],
        fixed_contrib=sample_inputs["fixed_contrib"],
    )
    assert result["tax"] == pytest.approx(312_601.5)
    assert result["vat"] == pytest.approx(476_190.4761904762)
    assert result["total_burden"] == pytest.approx(1_404_781.9761904762)
    assert result["net_profit"] == pytest.approx(1_295_218.0238095238)


def test_calculate_usn_income_minus_expenses_22(sample_inputs):
    result = calculate_usn_income_minus_expenses(
        sample_inputs["revenue"],
        sample_inputs["total_expenses"],
        sample_inputs["insurance_total"],
        22,
        sample_inputs["vat_purchases_percent"],
        sample_inputs["cost_of_goods"],
        fixed_contrib=sample_inputs["fixed_contrib"],
    )
    assert result["vat"] == pytest.approx(1_298_360.6557377048)
    assert result["total_burden"] == pytest.approx(2_226_952.1557377046)
    assert result["net_profit"] == pytest.approx(473_047.84426229517)


def test_calculate_osno(sample_inputs):
    result = calculate_osno(
        sample_inputs["revenue"],
        sample_inputs["total_expenses"],
        sample_inputs["insurance_total"],
        sample_inputs["vat_purchases_percent"],
        sample_inputs["cost_of_goods"],
        fixed_contrib=sample_inputs["fixed_contrib"],
    )
    assert result["tax"] == pytest.approx(196_412.3360655738)
    assert result["vat"] == pytest.approx(1_298_360.6557377048)
    assert result["total_burden"] == pytest.approx(2_110_762.9918032787)
    assert result["net_profit"] == pytest.approx(589_237.0081967213)


def test_calculate_osno_ip(sample_inputs):
    result = calculate_osno_ip(
        sample_inputs["revenue"],
        sample_inputs["total_expenses_common"],
        sample_inputs["vat_purchases_percent"],
        sample_inputs["cost_of_goods"],
        sample_inputs["rent"],
        sample_inputs["other_expenses"],
        sample_inputs["annual_fot"],
        sample_inputs["insurance_standard"],
        sample_inputs["fixed_contrib"],
        stock_extra=sample_inputs["stock_extra"],
    )
    assert result["tax"] == pytest.approx(103_896.89060655743)
    assert result["vat"] == pytest.approx(1_298_360.6557377048)
    assert result["total_burden"] == pytest.approx(2_004_690.0397868853)
    assert result["net_profit"] == pytest.approx(695_309.960213115)
    assert result["ndfl_base"] == pytest.approx(799_206.8508196725)


def test_format_number(sample_inputs):
    assert format_number(1_234_567) == "1 234 567"
    assert format_number(0) == "0"
    assert format_number(None) == "–"
