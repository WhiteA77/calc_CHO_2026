# -*- coding: utf-8 -*-
from typing import Any, Dict, Optional

from flask import Flask, render_template, request

from calculator import CalcInput, run_calculation
from calculator.constants import DEFAULT_FIXED_CONTRIB, MONTH_KEYS
from calculator.utils import format_number

app = Flask(__name__)


def _safe_number(value: Optional[float], default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_base_payload(components: Dict[str, Any], calc_input: Optional[CalcInput]) -> Dict[str, Any]:
    if not components or not calc_input:
        return {}

    return {
        "period_label": None,
        "revenue_gross": _safe_number(getattr(calc_input, "revenue", 0.0)),
        "cost_of_goods_gross": _safe_number(components.get("cost_of_goods")),
        "rent": _safe_number(components.get("rent")),
        "other_expenses": _safe_number(components.get("other_expenses")),
        "fot": _safe_number(components.get("annual_fot")),
        "has_employees": bool(components.get("has_employees")),
        "insurance_standard": _safe_number(components.get("insurance_standard")),
        "fixed_contrib": _safe_number(components.get("fixed_contrib")),
        "share_with_vat": _safe_number(components.get("vat_purchases_percent")),
        "vat_purchases_percent": _safe_number(components.get("vat_purchases_percent")),
        "transition_mode": components.get("transition_mode") or "none",
        "stock_extra": _safe_number(components.get("stock_extra")),
        "stock_expense_amount": _safe_number(components.get("stock_expense_amount")),
        "accumulated_vat_credit": _safe_number(components.get("accumulated_vat_credit")),
        "owner_extra_income": _safe_number(components.get("owner_extra_income")),
        "owner_extra_income_base": _safe_number(components.get("owner_extra_income_base")),
        "owner_extra_profit": _safe_number(components.get("owner_extra_profit")),
        "owner_extra_profit_base": _safe_number(components.get("owner_extra_profit_base")),
    }


def build_regime_payload(title: str, payload: Dict[str, Any], components: Dict[str, Any]) -> Dict[str, Any]:
    summary = {
        "revenue": _safe_number(payload.get("revenue")),
        "expenses": _safe_number(payload.get("expenses")),
        "tax": _safe_number(payload.get("tax")),
        "vat": _safe_number(payload.get("vat")),
        "insurance": _safe_number(payload.get("insurance")),
        "total_burden": _safe_number(payload.get("total_burden")),
        "burden_percent": _safe_number(payload.get("burden_percent")),
        "net_profit": _safe_number(payload.get("net_profit")),
    }

    taxes = {
        "usn_tax": summary["tax"],
        "usn_tax_before_reduction": _safe_number(payload.get("tax_initial")),
        "usn_reduction": _safe_number(payload.get("tax_reduction")),
        "usn_reduction_limit": _safe_number(payload.get("tax_reduction_limit")),
        "vat_to_pay": summary["vat"],
        "vat_charged": _safe_number(payload.get("vat_charged")),
        "vat_deductible": _safe_number(payload.get("vat_deductible")),
        "vat_extra_credit": _safe_number(payload.get("vat_extra_credit")),
    }

    insurance = {
        "insurance_total": summary["insurance"],
        "insurance_standard": _safe_number(components.get("insurance_standard")),
        "owner_extra": _safe_number(payload.get("owner_extra")),
        "owner_extra_base": _safe_number(payload.get("owner_extra_base")),
        "fixed_contrib": _safe_number(payload.get("fixed_contrib")),
    }

    details_keys = (
        "owner_extra",
        "owner_extra_base",
        "usn_regular_tax",
        "usn_min_tax",
        "tax_initial",
        "tax_reduction",
        "tax_reduction_limit",
        "tax_reduction_base",
        "fixed_contrib",
        "fixed_contrib_reduction",
        "ndfl_base",
        "ndfl_tax",
        "income_without_vat",
        "expenses_without_vat",
        "ausn_tax_base",
        "vat_charged",
        "vat_deductible",
        "vat_extra_credit",
    )

    details = {key: _safe_number(payload.get(key)) for key in details_keys}

    return {
        "id": payload.get("regime_id"),
        "title": title,
        "available": True,
        "summary": summary,
        "taxes": taxes,
        "insurance": insurance,
        "profit": {"net_profit": summary["net_profit"]},
        "burden": {
            "total_tax_burden": summary["total_burden"],
            "burden_percent": summary["burden_percent"],
        },
        "details": details,
    }


def build_calc_data(summary, components: Dict[str, Any], calc_input: Optional[CalcInput]) -> Dict[str, Any]:
    if not summary or not summary.results:
        return {}

    base_payload = build_base_payload(components, calc_input)
    regimes: Dict[str, Any] = {}
    order = []

    for title, payload, ok in summary.results:
        if not ok or not payload:
            continue
        regime_id = payload.get("regime_id")
        if not regime_id:
            continue
        order.append(regime_id)
        regimes[regime_id] = build_regime_payload(title, payload, components)

    return {
        "base": base_payload,
        "regimes": regimes,
        "order": order,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    error = None
    form_data = {}
    top_results = None
    components = {}
    fixed_contrib = DEFAULT_FIXED_CONTRIB
    calc_data = {}
    calc_input: Optional[CalcInput] = None

    if request.method == "POST":
        try:
            # Базовые данные из формы
            revenue = float(request.form.get("revenue", 0) or 0)
            cost_percent = float(request.form.get("cost_percent", 0) or 0)
            vat_purchases_percent = float(request.form.get("vat_purchases_percent", 0) or 0)
            rent = float(request.form.get("rent", 0) or 0)
            fixed_contrib = float(request.form.get("fixed_contrib", DEFAULT_FIXED_CONTRIB) or 0)

            employees = int(request.form.get("employees", 0) or 0)
            salary = float(request.form.get("salary", 0) or 0)

            fot_mode = request.form.get("fot_mode", "staff")
            fot_annual = float(request.form.get("fot_annual", 0) or 0)

            other_mode = request.form.get("other_mode", "percent")
            other_percent = float(request.form.get("other_percent", 0) or 0)
            other_amount = float(request.form.get("other_amount", 0) or 0)

            transition_mode = request.form.get("transition_mode", "none")
            if transition_mode not in {"none", "vat", "stock"}:
                transition_mode = "none"

            accumulated_vat_credit = float(request.form.get("accumulated_vat_credit", 0) or 0)
            stock_expense_amount = float(request.form.get("stock_expense_amount", 0) or 0)

            purchases_month_percents = []
            for key in MONTH_KEYS:
                raw = request.form.get(f"purchases_{key}", "").strip()
                value = float(raw) if raw else 0.0
                purchases_month_percents.append(value)

            # Валидация входных значений
            if (
                revenue < 0
                or cost_percent < 0
                or vat_purchases_percent < 0
                or rent < 0
                or employees < 0
                or salary < 0
                or other_percent < 0
                or other_amount < 0
                or fot_annual < 0
                or accumulated_vat_credit < 0
                or stock_expense_amount < 0
                or fixed_contrib < 0
                or any(p < 0 for p in purchases_month_percents)
            ):
                error = "Все значения должны быть неотрицательными"
            elif revenue == 0:
                error = "Выручка должна быть больше нуля"
            else:
                calc_input = CalcInput(
                    revenue=revenue,
                    cost_percent=cost_percent,
                    vat_purchases_percent=vat_purchases_percent,
                    rent=rent,
                    fixed_contrib=fixed_contrib,
                    employees=employees,
                    salary=salary,
                    fot_mode=fot_mode,
                    fot_annual=fot_annual,
                    other_mode=other_mode,
                    other_percent=other_percent,
                    other_amount=other_amount,
                    transition_mode=transition_mode,
                    accumulated_vat_credit=accumulated_vat_credit,
                    stock_expense_amount=stock_expense_amount,
                    purchases_month_percents=purchases_month_percents,
                )

                calc_input = CalcInput(
                    revenue=revenue,
                    cost_percent=cost_percent,
                    vat_purchases_percent=vat_purchases_percent,
                    rent=rent,
                    fixed_contrib=fixed_contrib,
                    employees=employees,
                    salary=salary,
                    fot_mode=fot_mode,
                    fot_annual=fot_annual,
                    other_mode=other_mode,
                    other_percent=other_percent,
                    other_amount=other_amount,
                    transition_mode=transition_mode,
                    accumulated_vat_credit=accumulated_vat_credit,
                    stock_expense_amount=stock_expense_amount,
                    purchases_month_percents=purchases_month_percents,
                )

                summary = run_calculation(calc_input)
                results = summary.results
                top_results = summary.top_results
                components = summary.components
                calc_data = build_calc_data(summary, components, calc_input)

            form_data = {
                "revenue": revenue,
                "cost_percent": cost_percent,
                "vat_purchases_percent": vat_purchases_percent,
                "rent": rent,
                "fixed_contrib": fixed_contrib,
                "employees": employees,
                "salary": salary,
                "fot_mode": fot_mode,
                "fot_annual": fot_annual,
                "other_mode": other_mode,
                "other_percent": other_percent,
                "other_amount": other_amount,
                "transition_mode": transition_mode,
                "accumulated_vat_credit": accumulated_vat_credit,
                "stock_expense_amount": stock_expense_amount,
            }
            for key, value in zip(MONTH_KEYS, purchases_month_percents):
                form_data[f"purchases_{key}"] = value

        except ValueError:
            error = "Пожалуйста, введите корректные числовые значения"
        except Exception as exc:
            error = f"Произошла ошибка при расчёте: {exc}"

    return render_template(
        "index.html",
        results=results,
        error=error,
        form_data=form_data,
        format_number=format_number,
        top_results=top_results,
        components=components,
        calc_data=calc_data,
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5005)
