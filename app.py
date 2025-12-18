# -*- coding: utf-8 -*-
from flask import Flask, render_template, request

from calculator import CalcInput, run_calculation
from calculator.constants import DEFAULT_FIXED_CONTRIB, MONTH_KEYS
from calculator.utils import format_number

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    error = None
    form_data = {}
    top_results = None
    components = {}
    fixed_contrib = DEFAULT_FIXED_CONTRIB

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

                summary = run_calculation(calc_input)
                results = summary.results
                top_results = summary.top_results
                components = summary.components

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
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5005)
