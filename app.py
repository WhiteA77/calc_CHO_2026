# -*- coding: utf-8 -*-
from flask import Flask, render_template, request

app = Flask(__name__)

MONTH_KEYS = [
    'jan', 'feb', 'mar', 'apr', 'may', 'jun',
    'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
]


def format_number(num):
    """Форматирует число с разделителями тысяч"""
    if num is None:
        return "–"
    return f"{num:,.0f}".replace(",", " ")


def _check_ausn_limits(revenue, employees):
    """Проверка лимитов АУСН: выручка ≤ 60 млн, сотрудников ≤ 5"""
    return revenue <= 60_000_000 and employees <= 5


def calculate_ausn_8(revenue, total_expenses, employees):
    """
    АУСН 8% — объект «доходы».
    Налог = 8% от выручки, страховые взносы (30% и 1%) не платятся, НДС нет.
    total_expenses сюда передаём БЕЗ страховых взносов и БЕЗ 1% свыше 300 000 ₽.
    """
    if not _check_ausn_limits(revenue, employees):
        return None

    tax = revenue * 0.08
    insurance = 0
    vat = 0

    total_tax_burden = tax + vat + insurance
    net_profit = revenue - total_expenses - tax

    return {
        'revenue': revenue,
        'expenses': total_expenses,
        'tax': tax,
        'vat': vat,
        'insurance': insurance,
        'total_burden': total_tax_burden,
        'burden_percent': (total_tax_burden / revenue * 100) if revenue > 0 else 0,
        'net_profit': net_profit,
    }


def calculate_ausn_20(revenue, total_expenses, employees):
    """
    АУСН 20% — объект «доходы минус расходы».
    Налог = 20% от (доходы - расходы), но не меньше 3% от доходов.
    Страховые взносы (30% и 1%) не платятся, НДС нет.
    total_expenses сюда передаём БЕЗ страховых взносов и БЕЗ 1% свыше 300 000 ₽.
    """
    if not _check_ausn_limits(revenue, employees):
        return None

    base = revenue - total_expenses
    base_for_tax = max(base, 0)

    tax_by_base = base_for_tax * 0.20
    min_tax = revenue * 0.03
    tax = max(tax_by_base, min_tax)

    insurance = 0
    vat = 0

    total_tax_burden = tax + vat + insurance
    net_profit = revenue - total_expenses - tax

    return {
        'revenue': revenue,
        'expenses': total_expenses,
        'tax': tax,
        'vat': vat,
        'insurance': insurance,
        'total_burden': total_tax_burden,
        'burden_percent': (total_tax_burden / revenue * 100) if revenue > 0 else 0,
        'net_profit': net_profit,
    }


def calculate_ausn_20_monthly(
    revenue,
    cost_of_goods,
    rent,
    other_expenses,
    annual_fot,
    purchases_month_percents,
    employees,
):
    """
    АУСН 20% — помесячный расчёт.

    - Доходы по месяцам считаем равномерными (revenue / 12)
    - Аренда, прочие, ФОТ — тоже равномерно по месяцам
    - Себестоимость (закупки) распределяем по месяцам по введённым коэффициентам
      (100 — обычный месяц, 200 — в 2 раза больше и т.д.), потом нормализуем
    - Налог за год = сумма помесячных max(20% от (Д-Р), 3% от доходов месяца)
    - Страховые взносы (30% и 1%) на АУСН не применяются.
    """
    if not _check_ausn_limits(revenue, employees):
        return None

    # Годовые расходы для отчёта (как раньше, без взносов)
    total_expenses_year = cost_of_goods + rent + other_expenses + annual_fot

    # Подготовка распределения коэффициентов
    cleaned = [max(float(p or 0), 0.0) for p in purchases_month_percents]
    total_weight = sum(cleaned)

    if total_weight <= 0:
        # Если пользователь всё занулил или не ввёл — считаем равномерно
        shares = [1 / 12.0] * 12
    else:
        # Нормализуем, чтобы сумма долей = 1
        shares = [p / total_weight for p in cleaned]

    # Равномерные помесячные показатели
    revenue_month = revenue / 12.0
    rent_month = rent / 12.0
    other_month = other_expenses / 12.0
    fot_month = annual_fot / 12.0

    total_tax = 0.0

    for share in shares:
        cost_month = cost_of_goods * share
        expenses_month = cost_month + rent_month + other_month + fot_month

        base = revenue_month - expenses_month
        tax_by_base = max(base, 0) * 0.20
        min_tax = revenue_month * 0.03
        month_tax = max(tax_by_base, min_tax)

        total_tax += month_tax

    tax = total_tax
    insurance = 0
    vat = 0

    total_tax_burden = tax + vat + insurance
    net_profit = revenue - total_expenses_year - tax

    return {
        'revenue': revenue,
        'expenses': total_expenses_year,
        'tax': tax,
        'vat': vat,
        'insurance': insurance,
        'total_burden': total_tax_burden,
        'burden_percent': (total_tax_burden / revenue * 100) if revenue > 0 else 0,
        'net_profit': net_profit,
    }


def calculate_usn_income(
    revenue,
    total_expenses,
    insurance,
    vat_rate,
    purchases_with_vat_percent,
    cost_of_goods,
):
    """Расчёт для УСН Доходы 6% + НДС"""
    usn_tax = revenue * 0.06

    vat_charged = revenue * vat_rate / (100 + vat_rate)

    if vat_rate == 5:
        vat_deductible = 0
    else:
        purchases_base = cost_of_goods * purchases_with_vat_percent / 100
        vat_deductible = purchases_base * vat_rate / (100 + vat_rate)

    vat_to_pay = max(vat_charged - vat_deductible, 0)

    total_tax_burden = usn_tax + vat_to_pay + insurance
    net_profit = revenue - total_expenses - usn_tax - vat_to_pay

    return {
        'revenue': revenue,
        'expenses': total_expenses,
        'tax': usn_tax,
        'vat': vat_to_pay,
        'insurance': insurance,
        'total_burden': total_tax_burden,
        'burden_percent': (total_tax_burden / revenue * 100) if revenue > 0 else 0,
        'net_profit': net_profit,
    }


def calculate_usn_income_minus_expenses(
    revenue,
    total_expenses,
    insurance,
    vat_rate,
    purchases_with_vat_percent,
    cost_of_goods,
):
    """Расчёт для УСН Доходы минус расходы 15% + НДС"""
    usn_base = revenue - total_expenses
    usn_tax = max(usn_base, 0) * 0.15

    vat_charged = revenue * vat_rate / (100 + vat_rate)

    if vat_rate == 5:
        vat_deductible = 0
    else:
        purchases_base = cost_of_goods * purchases_with_vat_percent / 100
        vat_deductible = purchases_base * vat_rate / (100 + vat_rate)

    vat_to_pay = max(vat_charged - vat_deductible, 0)

    total_tax_burden = usn_tax + vat_to_pay + insurance
    net_profit = revenue - total_expenses - usn_tax - vat_to_pay

    return {
        'revenue': revenue,
        'expenses': total_expenses,
        'tax': usn_tax,
        'vat': vat_to_pay,
        'insurance': insurance,
        'total_burden': total_tax_burden,
        'burden_percent': (total_tax_burden / revenue * 100) if revenue > 0 else 0,
        'net_profit': net_profit,
    }


def calculate_usn_income_no_vat(revenue, total_expenses, insurance):
    """УСН Доходы 6% без НДС (для общепита)"""
    usn_tax = revenue * 0.06
    vat_to_pay = 0

    total_tax_burden = usn_tax + vat_to_pay + insurance
    net_profit = revenue - total_expenses - usn_tax - vat_to_pay

    return {
        'revenue': revenue,
        'expenses': total_expenses,
        'tax': usn_tax,
        'vat': vat_to_pay,
        'insurance': insurance,
        'total_burden': total_tax_burden,
        'burden_percent': (total_tax_burden / revenue * 100) if revenue > 0 else 0,
        'net_profit': net_profit,
    }


def calculate_usn_dr_no_vat(revenue, total_expenses, insurance):
    """УСН Доходы минус расходы 15% без НДС (для общепита)"""
    usn_base = revenue - total_expenses
    usn_tax = max(usn_base, 0) * 0.15
    vat_to_pay = 0

    total_tax_burden = usn_tax + vat_to_pay + insurance
    net_profit = revenue - total_expenses - usn_tax - vat_to_pay

    return {
        'revenue': revenue,
        'expenses': total_expenses,
        'tax': usn_tax,
        'vat': vat_to_pay,
        'insurance': insurance,
        'total_burden': total_tax_burden,
        'burden_percent': (total_tax_burden / revenue * 100) if revenue > 0 else 0,
        'net_profit': net_profit,
    }


def calculate_osno(revenue, total_expenses, insurance, purchases_with_vat_percent, cost_of_goods):
    """Расчёт для ОСНО с НДС 22%"""
    vat_rate = 22

    vat_charged = revenue * vat_rate / (100 + vat_rate)

    purchases_base = cost_of_goods * purchases_with_vat_percent / 100
    vat_deductible = purchases_base * vat_rate / (100 + vat_rate)

    vat_to_pay = max(vat_charged - vat_deductible, 0)

    profit_tax_base = revenue - total_expenses - vat_to_pay
    # в 2026 году налог на прибыль 25%
    profit_tax = max(profit_tax_base, 0) * 0.25

    total_tax_burden = profit_tax + vat_to_pay + insurance
    net_profit = revenue - total_expenses - vat_to_pay - profit_tax

    return {
        'revenue': revenue,
        'expenses': total_expenses,
        'tax': profit_tax,
        'vat': vat_to_pay,
        'insurance': insurance,
        'total_burden': total_tax_burden,
        'burden_percent': (total_tax_burden / revenue * 100) if revenue > 0 else 0,
        'net_profit': net_profit,
    }


@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    error = None
    form_data = {}
    top_results = None
    components = {}

    if request.method == 'POST':
        try:
            # Базовые данные
            revenue = float(request.form.get('revenue', 0))
            cost_percent = float(request.form.get('cost_percent', 0))
            vat_purchases_percent = float(request.form.get('vat_purchases_percent', 0))
            rent = float(request.form.get('rent', 0))

            employees = int(request.form.get('employees', 0))
            salary = float(request.form.get('salary', 0))

            # Режим задания ФОТ
            fot_mode = request.form.get('fot_mode', 'staff')
            fot_annual = float(request.form.get('fot_annual', 0))

            # Прочие расходы: режим + поля
            other_mode = request.form.get('other_mode', 'percent')
            other_percent = float(request.form.get('other_percent', 0))
            other_amount = float(request.form.get('other_amount', 0))

            # Коэффициенты закупок по месяцам
            purchases_month_percents = []
            for key in MONTH_KEYS:
                raw = request.form.get(f'purchases_{key}', '').strip()
                value = float(raw) if raw else 0.0
                purchases_month_percents.append(value)

            # Валидация
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
                or any(p < 0 for p in purchases_month_percents)
            ):
                error = "Все значения должны быть неотрицательными"
            elif revenue == 0:
                error = "Выручка должна быть больше нуля"
            else:
                # Себестоимость
                cost_of_goods = revenue * cost_percent / 100

                # Прочие расходы
                if other_mode == 'percent':
                    other_expenses = revenue * other_percent / 100
                else:
                    other_expenses = other_amount

                # ФОТ
                if fot_mode == 'annual':
                    annual_fot = fot_annual
                else:
                    annual_fot = employees * salary * 12

                # Страховые взносы 30% от ФОТ (для УСН/ОСНО)
                insurance_standard = annual_fot * 0.30

                # Взнос 1% с доходов свыше 300 000 ₽ — только для не-АУСН режимов
                owner_extra_1p = max(0.0, revenue - 300_000) * 0.01

                # Общие расходы (без налогов) для УСН/ОСНО:
                # включаем и 30% от ФОТ, и 1% (они уменьшают прибыль)
                total_expenses = (
                    cost_of_goods
                    + rent
                    + other_expenses
                    + annual_fot
                    + insurance_standard
                    + owner_extra_1p
                )

                # Для АУСН расходы без страховых взносов и без 1%
                total_expenses_ausn = cost_of_goods + rent + other_expenses + annual_fot

                # Базовые компоненты для пояснений
                components = {
                    'cost_of_goods': cost_of_goods,
                    'rent': rent,
                    'other_expenses': other_expenses,
                    'annual_fot': annual_fot,
                    'insurance_standard': insurance_standard,
                    'owner_extra_1p': owner_extra_1p,
                    'vat_purchases_percent': vat_purchases_percent,
                }

                # ---- Расчёт режимов ----
                results = []

                # АУСН 8% (без 30% взносов и без 1%)
                ausn_8 = calculate_ausn_8(revenue, total_expenses_ausn, employees)
                if ausn_8:
                    results.append(('АУСН 8%', ausn_8, True))
                else:
                    results.append(('АУСН 8% (нельзя применять — превышены лимиты)', None, False))

                # АУСН 20% (помесячный, тоже без взносов и без 1%)
                ausn_20 = calculate_ausn_20_monthly(
                    revenue=revenue,
                    cost_of_goods=cost_of_goods,
                    rent=rent,
                    other_expenses=other_expenses,
                    annual_fot=annual_fot,
                    purchases_month_percents=purchases_month_percents,
                    employees=employees,
                )
                if ausn_20:
                    results.append(('АУСН 20%', ausn_20, True))
                else:
                    results.append(('АУСН 20% (нельзя применять — превышены лимиты)', None, False))

                # УСН для общепита без НДС (сюда входят 30% ФОТ + 1% сверх 300k)
                insurance_total = insurance_standard + owner_extra_1p
                usn_income_no_vat = calculate_usn_income_no_vat(revenue, total_expenses, insurance_total)
                results.append(('УСН Доходы 6%', usn_income_no_vat, True))

                usn_dr_no_vat = calculate_usn_dr_no_vat(revenue, total_expenses, insurance_total)
                results.append(('УСН Д-Р 15%', usn_dr_no_vat, True))

                # УСН + НДС 5%
                usn_income_5 = calculate_usn_income(
                    revenue,
                    total_expenses,
                    insurance_total,
                    5,
                    vat_purchases_percent,
                    cost_of_goods,
                )
                results.append(('УСН Доходы 6% + НДС 5%', usn_income_5, True))

                usn_dr_5 = calculate_usn_income_minus_expenses(
                    revenue,
                    total_expenses,
                    insurance_total,
                    5,
                    vat_purchases_percent,
                    cost_of_goods,
                )
                results.append(('УСН Д-Р 15% + НДС 5%', usn_dr_5, True))

                # УСН Д-Р 15% + НДС 22% (1% тоже включён)
                usn_dr_22 = calculate_usn_income_minus_expenses(
                    revenue,
                    total_expenses,
                    insurance_total,
                    22,
                    vat_purchases_percent,
                    cost_of_goods,
                )
                results.append(('УСН Д-Р 15% + НДС 22%', usn_dr_22, True))

                # ОСНО + НДС 22% (1% тоже включён)
                osno = calculate_osno(
                    revenue,
                    total_expenses,
                    insurance_total,
                    vat_purchases_percent,
                    cost_of_goods,
                )
                results.append(('ОСНО + НДС 22%', osno, True))

                # Топ-5 режимов
                available = [(name, data) for name, data, ok in results if ok and data]
                top_results = sorted(
                    available,
                    key=lambda item: (item[1]['total_burden'], -item[1]['net_profit']),
                )[:5]

            # form_data — чтобы вернуть значения в форму
            form_data = {
                'revenue': revenue,
                'cost_percent': cost_percent,
                'vat_purchases_percent': vat_purchases_percent,
                'rent': rent,
                'employees': employees,
                'salary': salary,
                'fot_mode': fot_mode,
                'fot_annual': fot_annual,
                'other_mode': other_mode,
                'other_percent': other_percent,
                'other_amount': other_amount,
            }
            for key, value in zip(MONTH_KEYS, purchases_month_percents):
                form_data[f'purchases_{key}'] = value

        except ValueError:
            error = "Пожалуйста, введите корректные числовые значения"
        except Exception as e:
            error = f"Произошла ошибка при расчёте: {str(e)}"

    return render_template(
        'index.html',
        results=results,
        error=error,
        form_data=form_data,
        format_number=format_number,
        top_results=top_results,
        components=components,
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)
