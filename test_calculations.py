#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Набор PyTest-проверок для расчётных функций калькулятора."""

import pytest

from app import (
    calculate_ausn_8,
    calculate_ausn_20,
    calculate_usn_income,
    calculate_usn_income_minus_expenses,
    calculate_osno,
    format_number,
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

    total_expenses = cost_of_goods + rent + other_expenses + annual_fot + insurance_standard
    total_expenses_ausn = total_expenses - insurance_standard

    return {
        "revenue": revenue,
        "employees": employees,
        "vat_purchases_percent": vat_purchases_percent,
        "cost_of_goods": cost_of_goods,
        "insurance": insurance_standard,
        "total_expenses": total_expenses,
        "total_expenses_ausn": total_expenses_ausn,
    }


def test_calculate_ausn_8(sample_inputs):
    result = calculate_ausn_8(
        sample_inputs["revenue"],
        sample_inputs["total_expenses_ausn"],
        sample_inputs["employees"],
    )
    assert result is not None
    assert result["tax"] == pytest.approx(800_000)
    assert result["total_burden"] == pytest.approx(800_000)
    assert result["net_profit"] == pytest.approx(1_900_000)
    assert result["burden_percent"] == pytest.approx(8.0)


def test_calculate_ausn_20(sample_inputs):
    result = calculate_ausn_20(
        sample_inputs["revenue"],
        sample_inputs["total_expenses_ausn"],
        sample_inputs["employees"],
    )
    assert result is not None
    assert result["tax"] == pytest.approx(540_000)
    assert result["total_burden"] == pytest.approx(540_000)
    assert result["net_profit"] == pytest.approx(2_160_000)
    assert result["burden_percent"] == pytest.approx(5.4)


def test_calculate_usn_income(sample_inputs):
    result = calculate_usn_income(
        sample_inputs["revenue"],
        sample_inputs["total_expenses"],
        sample_inputs["insurance"],
        5,
        sample_inputs["vat_purchases_percent"],
        sample_inputs["cost_of_goods"],
    )
    assert result["tax"] == pytest.approx(600_000)
    assert result["vat"] == pytest.approx(476_190.4761904762)
    assert result["total_burden"] == pytest.approx(1_616_190.4761904762)
    assert result["net_profit"] == pytest.approx(1_083_809.5238095238)


def test_calculate_usn_income_minus_expenses_5(sample_inputs):
    result = calculate_usn_income_minus_expenses(
        sample_inputs["revenue"],
        sample_inputs["total_expenses"],
        sample_inputs["insurance"],
        5,
        sample_inputs["vat_purchases_percent"],
        sample_inputs["cost_of_goods"],
    )
    assert result["tax"] == pytest.approx(324_000)
    assert result["vat"] == pytest.approx(476_190.4761904762)
    assert result["total_burden"] == pytest.approx(1_340_190.4761904762)
    assert result["net_profit"] == pytest.approx(1_359_809.5238095238)


def test_calculate_usn_income_minus_expenses_22(sample_inputs):
    result = calculate_usn_income_minus_expenses(
        sample_inputs["revenue"],
        sample_inputs["total_expenses"],
        sample_inputs["insurance"],
        22,
        sample_inputs["vat_purchases_percent"],
        sample_inputs["cost_of_goods"],
    )
    assert result["vat"] == pytest.approx(1_298_360.6557377048)
    assert result["total_burden"] == pytest.approx(2_162_360.6557377046)
    assert result["net_profit"] == pytest.approx(537_639.3442622952)


def test_calculate_osno(sample_inputs):
    result = calculate_osno(
        sample_inputs["revenue"],
        sample_inputs["total_expenses"],
        sample_inputs["insurance"],
        sample_inputs["vat_purchases_percent"],
        sample_inputs["cost_of_goods"],
    )
    assert result["tax"] == pytest.approx(172_327.86885245904)
    assert result["vat"] == pytest.approx(1_298_360.6557377048)
    assert result["total_burden"] == pytest.approx(2_010_688.524590164)
    assert result["net_profit"] == pytest.approx(689_311.4754098362)


def test_format_number(sample_inputs):
    assert format_number(1_234_567) == "1 234 567"
    assert format_number(0) == "0"
    assert format_number(None) == "–"
