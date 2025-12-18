# -*- coding: utf-8 -*-
from flask import Flask, render_template, request

app = Flask(__name__)

MONTH_KEYS = [
    'jan', 'feb', 'mar', 'apr', 'may', 'jun',
    'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
]

THRESHOLD_1_PERCENT = 300_000
DEFAULT_FIXED_CONTRIB = 57_390
NDFL_BRACKETS_2026 = [
    (2_400_000, 0.13),
    (5_000_000, 0.15),
    (20_000_000, 0.18),
    (50_000_000, 0.20),
    (None, 0.22),
]


def calculate_owner_extra_income(revenue):
    """Дополнительный взнос 1% для режимов 'доходы'"""
    base_before_threshold = revenue
    taxable = max(0.0, base_before_threshold - THRESHOLD_1_PERCENT)
    return taxable * 0.01, base_before_threshold


def calculate_owner_extra_profit(revenue, expenses_without_self_contrib):
    """
    Дополнительный взнос 1% для режимов 'доходы минус расходы' и ОСНО.
    Расходы берём без учёта взносов за себя и самого 1%.
    """
    base_before_threshold = revenue - expenses_without_self_contrib
    taxable = max(0.0, base_before_threshold - THRESHOLD_1_PERCENT)
    return taxable * 0.01, base_before_threshold


def calculate_progressive_ndfl(base, brackets=NDFL_BRACKETS_2026):
    """
    Рассчитывает НДФЛ по прогрессивной шкале.

    Шкала задаётся списком порогов и ставок. Последняя ступень должна иметь
    limit=None, чтобы охватить всю оставшуюся базу.
    """
    taxable = max(float(base or 0), 0.0)
    tax = 0.0
    prev_limit = 0.0

    for limit, rate in brackets:
        if taxable <= prev_limit:
            break
        upper_bound = taxable if limit is None else min(taxable, float(limit))
        portion = upper_bound - prev_limit
        if portion <= 0:
            break
        tax += portion * rate
        prev_limit = upper_bound

    return tax


def format_number(num):
    """Форматирует число с разделителями тысяч"""
    if num is None:
        return "–"
    return f"{num:,.0f}".replace(",", " ")


def _check_ausn_limits(revenue, employees):
    """Проверка лимитов АУСН: выручка ≤ 60 млн, сотрудников ≤ 5"""
    return revenue <= 60_000_000 and employees <= 5


def calculate_ausn_8(revenue, total_expenses, employees, fixed_contrib=0.0):
    """
    АУСН 8% — объект «доходы».
    Налог = 8% от выручки, взносов нет, НДС нет.
    total_expenses сюда передаём БЕЗ страховых взносов.
    На АУСН 1% свыше 300 000 ₽ не платится.
    """
    if not _check_ausn_limits(revenue, employees):
        return None

    tax = revenue * 0.08
    vat = 0
    insurance = fixed_contrib

    total_tax_burden = tax + vat + insurance
    net_profit = revenue - total_expenses - tax - fixed_contrib

    return {
        'revenue': revenue,
        'expenses': total_expenses,
        'tax': tax,
        'vat': vat,
        'insurance': insurance,
        'total_burden': total_tax_burden,
        'burden_percent': (total_tax_burden / revenue * 100) if revenue > 0 else 0,
        'net_profit': net_profit,
        'fixed_contrib': fixed_contrib,
    }


def calculate_ausn_20(revenue, total_expenses, employees, fixed_contrib=0.0):
    """
    АУСН 20% — объект «доходы минус расходы».
    Налог = 20% от (доходы - расходы), но не меньше 3% от доходов.
    Взносов нет, НДС нет.
    total_expenses сюда передаём БЕЗ страховых взносов.
    На АУСН 1% свыше 300 000 ₽ не платится.
    """
    if not _check_ausn_limits(revenue, employees):
        return None

    base = revenue - total_expenses
    base_for_tax = max(base, 0)

    tax_by_base = base_for_tax * 0.20
    min_tax = revenue * 0.03
    tax = max(tax_by_base, min_tax)

    vat = 0
    insurance = fixed_contrib

    total_tax_burden = tax + vat + insurance
    net_profit = revenue - total_expenses - tax - fixed_contrib

    return {
        'revenue': revenue,
        'expenses': total_expenses,
        'tax': tax,
        'vat': vat,
        'insurance': insurance,
        'total_burden': total_tax_burden,
        'burden_percent': (total_tax_burden / revenue * 100) if revenue > 0 else 0,
        'net_profit': net_profit,
        'fixed_contrib': fixed_contrib,
    }


def calculate_ausn_20_monthly(
    revenue,
    cost_of_goods,
    rent,
    other_expenses,
    annual_fot,
    purchases_month_percents,
    employees,
    fixed_contrib=0.0,
):
    """
    АУСН 20% — расчёт по итогам года.

    Налог = 20% от (годовые доходы − годовые расходы), но не меньше 3% от годовой
    выручки. Минимальный налог применяется один раз за год. Параметр распределения
    закупок оставлен для возможного дальнейшего развития, но на итоговый расчёт
    сейчас не влияет.
    """
    if not _check_ausn_limits(revenue, employees):
        return None

    total_expenses_year = cost_of_goods + rent + other_expenses + annual_fot

    tax_base = revenue - total_expenses_year
    base_for_tax = max(tax_base, 0.0)
    tax_by_base = base_for_tax * 0.20
    min_tax = revenue * 0.03
    tax = max(tax_by_base, min_tax)
    vat = 0
    insurance = fixed_contrib

    total_tax_burden = tax + vat + insurance
    net_profit = revenue - total_expenses_year - tax - fixed_contrib

    return {
        'revenue': revenue,
        'expenses': total_expenses_year,
        'tax': tax,
        'vat': vat,
        'insurance': insurance,
        'total_burden': total_tax_burden,
        'burden_percent': (total_tax_burden / revenue * 100) if revenue > 0 else 0,
        'net_profit': net_profit,
        'ausn_tax_base': base_for_tax,
        'fixed_contrib': fixed_contrib,
    }


def calculate_usn_income(
    revenue,
    total_expenses,
    insurance,
    insurance_standard,
    vat_rate,
    purchases_with_vat_percent,
    cost_of_goods,
    fixed_contrib=0.0,
    has_employees=False,
    accumulated_vat_credit=0.0,
):
    """Расчёт для УСН Доходы 6% + НДС"""
    tax_initial = revenue * 0.06
    reduction_base = insurance_standard
    max_reduction = tax_initial * 0.50
    reduction_from_standard = min(reduction_base, max_reduction)

    if has_employees:
        available_for_fixed = max(max_reduction - reduction_from_standard, 0)
        reduction_from_fixed = min(fixed_contrib, available_for_fixed)
    else:
        max_without_standard = max(tax_initial - reduction_from_standard, 0)
        reduction_from_fixed = min(fixed_contrib, max_without_standard)

    tax_reduction = reduction_from_standard + reduction_from_fixed
    usn_tax = max(tax_initial - tax_reduction, 0)

    vat_charged = revenue * vat_rate / (100 + vat_rate)

    if vat_rate == 5:
        vat_deductible = 0
        extra_credit = 0
    else:
        purchases_base = cost_of_goods * purchases_with_vat_percent / 100
        vat_deductible = purchases_base * vat_rate / (100 + vat_rate)
        extra_credit = accumulated_vat_credit

    vat_to_pay = max(vat_charged - vat_deductible - extra_credit, 0)

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
        'tax_initial': tax_initial,
        'tax_reduction': tax_reduction,
        'tax_reduction_limit': max_reduction,
        'tax_reduction_base': reduction_base,
        'fixed_contrib': fixed_contrib,
        'fixed_contrib_reduction': reduction_from_fixed,
    }


def calculate_usn_income_minus_expenses(
    revenue,
    total_expenses,
    insurance,
    vat_rate,
    purchases_with_vat_percent,
    cost_of_goods,
    accumulated_vat_credit=0.0,
    stock_extra=0.0,
    fixed_contrib=0.0,
):
    """Расчёт для УСН Доходы минус расходы 15% + НДС"""
    usn_base = revenue - total_expenses - stock_extra
    taxable_base = max(usn_base, 0)
    tax_regular = taxable_base * 0.15
    min_tax = revenue * 0.01
    usn_tax = max(tax_regular, min_tax)

    vat_charged = revenue * vat_rate / (100 + vat_rate)

    if vat_rate == 5:
        # Льготный НДС 5%, вычетов нет, накопленный НДС тоже не применяем
        vat_deductible = 0
        extra_credit = 0
    else:
        purchases_base = cost_of_goods * purchases_with_vat_percent / 100
        vat_deductible = purchases_base * vat_rate / (100 + vat_rate)
        # При ставке 22% можно применить накопленный НДС к вычету
        extra_credit = accumulated_vat_credit

    vat_to_pay = max(vat_charged - vat_deductible - extra_credit, 0)

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
        'usn_regular_tax': tax_regular,
        'usn_min_tax': min_tax,
        'fixed_contrib': fixed_contrib,
    }


def calculate_usn_income_no_vat(
    revenue,
    total_expenses,
    insurance,
    insurance_standard,
    fixed_contrib=0.0,
    has_employees=False,
):
    """УСН Доходы 6% без НДС"""
    tax_initial = revenue * 0.06
    reduction_base = insurance_standard
    max_reduction = tax_initial * 0.50
    reduction_from_standard = min(reduction_base, max_reduction)

    if has_employees:
        available_for_fixed = max(max_reduction - reduction_from_standard, 0)
        reduction_from_fixed = min(fixed_contrib, available_for_fixed)
    else:
        max_without_standard = max(tax_initial - reduction_from_standard, 0)
        reduction_from_fixed = min(fixed_contrib, max_without_standard)

    tax_reduction = reduction_from_standard + reduction_from_fixed
    usn_tax = max(tax_initial - tax_reduction, 0)
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
        'tax_initial': tax_initial,
        'tax_reduction': tax_reduction,
        'tax_reduction_limit': max_reduction,
        'tax_reduction_base': reduction_base,
        'fixed_contrib': fixed_contrib,
        'fixed_contrib_reduction': reduction_from_fixed,
    }


def calculate_usn_dr_no_vat(
    revenue,
    total_expenses,
    insurance,
    stock_extra=0.0,
    fixed_contrib=0.0,
):
    """УСН Доходы минус расходы 15% без НДС"""
    usn_base = revenue - total_expenses - stock_extra
    taxable_base = max(usn_base, 0)
    tax_regular = taxable_base * 0.15
    min_tax = revenue * 0.01
    usn_tax = max(tax_regular, min_tax)
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
        'usn_regular_tax': tax_regular,
        'usn_min_tax': min_tax,
        'fixed_contrib': fixed_contrib,
    }


def calculate_osno(
    revenue,
    total_expenses,
    insurance,
    purchases_with_vat_percent,
    cost_of_goods,
    accumulated_vat_credit=0.0,
    stock_extra=0.0,
    fixed_contrib=0.0,
):
    """Расчёт для ОСНО с НДС 22%"""
    vat_rate = 22

    vat_charged = revenue * vat_rate / (100 + vat_rate)

    purchases_base = cost_of_goods * purchases_with_vat_percent / 100
    vat_deductible = purchases_base * vat_rate / (100 + vat_rate)

    # Учитываем накопленный НДС к вычету
    vat_to_pay = max(vat_charged - vat_deductible - accumulated_vat_credit, 0)

    profit_tax_base = revenue - total_expenses - stock_extra - vat_to_pay
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
        'fixed_contrib': fixed_contrib,
    }


def calculate_osno_ip(
    revenue,
    base_total_expenses,
    purchases_with_vat_percent,
    cost_of_goods,
    rent,
    other_expenses,
    annual_fot,
    insurance_standard,
    fixed_contrib=0.0,
    accumulated_vat_credit=0.0,
    stock_extra=0.0,
):
    """Расчёт для ОСНО (ИП) с прогрессивным НДФЛ"""
    vat_rate = 22

    vat_charged = revenue * vat_rate / (100 + vat_rate)

    purchases_base = cost_of_goods * purchases_with_vat_percent / 100
    vat_deductible = purchases_base * vat_rate / (100 + vat_rate)

    vat_to_pay = max(vat_charged - vat_deductible - accumulated_vat_credit, 0)

    income_without_vat = revenue - vat_charged
    stock_part = stock_extra if stock_extra > 0 else 0.0

    base_expenses_without_vat = (
        (cost_of_goods - vat_deductible)
        + rent
        + other_expenses
        + annual_fot
        + insurance_standard
        + stock_part
    )

    # База для расчёта 1% (без самого 1% и без фиксированного взноса)
    base_for_one_percent = income_without_vat - base_expenses_without_vat - fixed_contrib
    base_for_one_percent = max(base_for_one_percent, 0.0)
    extra_one_percent = max(base_for_one_percent - THRESHOLD_1_PERCENT, 0.0) * 0.01

    ndfl_base = base_for_one_percent - extra_one_percent
    ndfl_base = max(ndfl_base, 0.0)
    ndfl_tax = calculate_progressive_ndfl(ndfl_base)

    insurance_total = insurance_standard + fixed_contrib + extra_one_percent

    total_tax_burden = ndfl_tax + vat_to_pay + insurance_total
    net_profit = (
        income_without_vat
        - base_expenses_without_vat
        - ndfl_tax
        - fixed_contrib
        - extra_one_percent
    )

    display_expenses = base_total_expenses + fixed_contrib + extra_one_percent

    return {
        'revenue': revenue,
        'expenses': display_expenses,
        'tax': ndfl_tax,
        'vat': vat_to_pay,
        'insurance': insurance_total,
        'total_burden': total_tax_burden,
        'burden_percent': (total_tax_burden / revenue * 100) if revenue > 0 else 0,
        'net_profit': net_profit,
        'ndfl_base': ndfl_base,
        'income_without_vat': income_without_vat,
        'expenses_without_vat': base_expenses_without_vat,
        'fixed_contrib': fixed_contrib,
        'owner_extra': extra_one_percent,
        'owner_extra_base': base_for_one_percent,
    }


@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    error = None
    form_data = {}
    top_results = None
    components = {}
    fixed_contrib = DEFAULT_FIXED_CONTRIB

    if request.method == 'POST':
        try:
            # Базовые данные
            revenue = float(request.form.get('revenue', 0))
            cost_percent = float(request.form.get('cost_percent', 0))
            vat_purchases_percent = float(request.form.get('vat_purchases_percent', 0))
            rent = float(request.form.get('rent', 0))
            fixed_contrib = float(request.form.get('fixed_contrib', DEFAULT_FIXED_CONTRIB))

            employees = int(request.form.get('employees', 0))
            salary = float(request.form.get('salary', 0))

            # Режим задания ФОТ
            fot_mode = request.form.get('fot_mode', 'staff')
            fot_annual = float(request.form.get('fot_annual', 0))

            # Прочие расходы: режим + поля
            other_mode = request.form.get('other_mode', 'percent')
            other_percent = float(request.form.get('other_percent', 0))
            other_amount = float(request.form.get('other_amount', 0))

            # Блок "Учёт перехода"
            transition_mode = request.form.get('transition_mode', 'none')
            if transition_mode not in {'none', 'vat', 'stock'}:
                transition_mode = 'none'

            accumulated_vat_credit = float(request.form.get('accumulated_vat_credit', 0) or 0)
            stock_expense_amount = float(request.form.get('stock_expense_amount', 0) or 0)

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
                or accumulated_vat_credit < 0
                or stock_expense_amount < 0
                or fixed_contrib < 0
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

                has_employees = annual_fot > 0

                # Страховые взносы 30% от ФОТ (для всех, кроме АУСН)
                insurance_standard = annual_fot * 0.30

                # Общие расходы (без налогов) для УСН/ОСНО без 1% за себя
                total_expenses_common = (
                    cost_of_goods
                    + rent
                    + other_expenses
                    + annual_fot
                    + insurance_standard
                )

                stock_extra = stock_expense_amount if transition_mode == 'stock' else 0.0
                vat_credit_to_apply = accumulated_vat_credit if transition_mode == 'vat' else 0.0

                # База расходов без взносов за себя для расчёта 1%
                expenses_without_self_contrib = (
                    cost_of_goods
                    + rent
                    + other_expenses
                    + annual_fot
                    + insurance_standard
                    + stock_extra
                )

                owner_extra_income, owner_extra_income_base = calculate_owner_extra_income(revenue)
                owner_extra_profit, owner_extra_profit_base = calculate_owner_extra_profit(
                    revenue,
                    expenses_without_self_contrib,
                )

                # Для АУСН расходы без страховых взносов и без 1%, и без остатков
                total_expenses_ausn = cost_of_goods + rent + other_expenses + annual_fot

                # Базовые компоненты для пояснений
                components = {
                    'cost_of_goods': cost_of_goods,
                    'rent': rent,
                    'other_expenses': other_expenses,
                    'annual_fot': annual_fot,
                    'insurance_standard': insurance_standard,
                    'fixed_contrib': fixed_contrib,
                    'owner_extra_income': owner_extra_income,
                    'owner_extra_income_base': owner_extra_income_base,
                    'owner_extra_profit': owner_extra_profit,
                    'owner_extra_profit_base': owner_extra_profit_base,
                    'vat_purchases_percent': vat_purchases_percent,
                    'accumulated_vat_credit': accumulated_vat_credit,
                    'stock_expense_amount': stock_expense_amount,
                    'stock_extra': stock_extra,
                    'transition_mode': transition_mode,
                }

                total_expenses_income_regime = (
                    total_expenses_common + owner_extra_income + fixed_contrib
                )
                total_expenses_profit_regime = (
                    total_expenses_common + owner_extra_profit + fixed_contrib
                )

                # ---- Расчёт режимов ----
                results = []

                # АУСН 8% (без 30% взносов, без 1%, без остатков)
                ausn_8 = calculate_ausn_8(
                    revenue,
                    total_expenses_ausn,
                    employees,
                    fixed_contrib=fixed_contrib,
                )
                if ausn_8:
                    results.append(('АУСН 8%', ausn_8, True))
                else:
                    results.append(('АУСН 8% (нельзя применять — превышены лимиты)', None, False))

                # АУСН 20% (помесячный, тоже без взносов, 1% и остатков)
                ausn_20 = calculate_ausn_20_monthly(
                    revenue=revenue,
                    cost_of_goods=cost_of_goods,
                    rent=rent,
                    other_expenses=other_expenses,
                    annual_fot=annual_fot,
                    purchases_month_percents=purchases_month_percents,
                    employees=employees,
                    fixed_contrib=fixed_contrib,
                )
                if ausn_20:
                    results.append(('АУСН 20%', ausn_20, True))
                else:
                    results.append(('АУСН 20% (нельзя применять — превышены лимиты)', None, False))

                # УСН Доходы 6% (без НДС) — остатки не учитываются
                insurance_total_income = (
                    insurance_standard + owner_extra_income + fixed_contrib
                )
                usn_income_no_vat = calculate_usn_income_no_vat(
                    revenue,
                    total_expenses_income_regime,
                    insurance_total_income,
                    insurance_standard,
                    fixed_contrib=fixed_contrib,
                    has_employees=has_employees,
                )
                if usn_income_no_vat:
                    usn_income_no_vat['owner_extra'] = owner_extra_income
                    usn_income_no_vat['owner_extra_base'] = owner_extra_income_base
                results.append(('УСН Доходы 6%', usn_income_no_vat, True))

                # УСН Доходы 6% + НДС 5% — остатки не учитываются, НДС 5% без вычетов
                usn_income_5 = calculate_usn_income(
                    revenue,
                    total_expenses_income_regime,
                    insurance_total_income,
                    insurance_standard,
                    5,
                    vat_purchases_percent,
                    cost_of_goods,
                    fixed_contrib=fixed_contrib,
                    has_employees=has_employees,
                )
                if usn_income_5:
                    usn_income_5['owner_extra'] = owner_extra_income
                    usn_income_5['owner_extra_base'] = owner_extra_income_base
                results.append(('УСН Доходы 6% + НДС 5%', usn_income_5, True))

                # УСН Доходы 6% + НДС 22% — учитываем вычеты по закупкам и накопленный НДС
                usn_income_22 = calculate_usn_income(
                    revenue,
                    total_expenses_income_regime,
                    insurance_total_income,
                    insurance_standard,
                    22,
                    vat_purchases_percent,
                    cost_of_goods,
                    fixed_contrib=fixed_contrib,
                    has_employees=has_employees,
                    accumulated_vat_credit=vat_credit_to_apply,
                )
                if usn_income_22:
                    usn_income_22['owner_extra'] = owner_extra_income
                    usn_income_22['owner_extra_base'] = owner_extra_income_base
                results.append(('УСН Доходы 6% + НДС 22%', usn_income_22, True))

                insurance_total_profit = (
                    insurance_standard + owner_extra_profit + fixed_contrib
                )

                # УСН Д-Р 15% — списание остатков влияет только на налоговую базу
                usn_dr_no_vat = calculate_usn_dr_no_vat(
                    revenue,
                    total_expenses_profit_regime,
                    insurance_total_profit,
                    stock_extra=stock_extra,
                    fixed_contrib=fixed_contrib,
                )
                if usn_dr_no_vat:
                    usn_dr_no_vat['owner_extra'] = owner_extra_profit
                    usn_dr_no_vat['owner_extra_base'] = owner_extra_profit_base
                results.append(('УСН Д-Р 15%', usn_dr_no_vat, True))

                # УСН Д-Р 15% + НДС 5% — списание остатков только для налога, НДС 5% без вычетов
                usn_dr_5 = calculate_usn_income_minus_expenses(
                    revenue,
                    total_expenses_profit_regime,
                    insurance_total_profit,
                    5,
                    vat_purchases_percent,
                    cost_of_goods,
                    accumulated_vat_credit=0.0,  # при 5% накопленный НДС не применяется
                    stock_extra=stock_extra,
                    fixed_contrib=fixed_contrib,
                )
                if usn_dr_5:
                    usn_dr_5['owner_extra'] = owner_extra_profit
                    usn_dr_5['owner_extra_base'] = owner_extra_profit_base
                results.append(('УСН Д-Р 15% + НДС 5%', usn_dr_5, True))

                # УСН Д-Р 15% + НДС 22% — списание остатков и накопленный НДС
                usn_dr_22 = calculate_usn_income_minus_expenses(
                    revenue,
                    total_expenses_profit_regime,
                    insurance_total_profit,
                    22,
                    vat_purchases_percent,
                    cost_of_goods,
                    accumulated_vat_credit=vat_credit_to_apply,
                    stock_extra=stock_extra,
                    fixed_contrib=fixed_contrib,
                )
                if usn_dr_22:
                    usn_dr_22['owner_extra'] = owner_extra_profit
                    usn_dr_22['owner_extra_base'] = owner_extra_profit_base
                results.append(('УСН Д-Р 15% + НДС 22%', usn_dr_22, True))

                # ОСНО + НДС 22% (ООО) — списание остатков только для налога на прибыль
                osno = calculate_osno(
                    revenue,
                    total_expenses_profit_regime,
                    insurance_total_profit,
                    vat_purchases_percent,
                    cost_of_goods,
                    accumulated_vat_credit=vat_credit_to_apply,
                    stock_extra=stock_extra,
                    fixed_contrib=fixed_contrib,
                )
                if osno:
                    osno['owner_extra'] = owner_extra_profit
                    osno['owner_extra_base'] = owner_extra_profit_base
                results.append(('ОСНО + НДС 22% (ООО)', osno, True))

                # ОСНО + НДС 22% (ИП) — вместо налога на прибыль считаем прогрессивный НДФЛ
                osno_ip = calculate_osno_ip(
                    revenue,
                    total_expenses_common,
                    vat_purchases_percent,
                    cost_of_goods,
                    rent,
                    other_expenses,
                    annual_fot,
                    insurance_standard,
                    fixed_contrib,
                    accumulated_vat_credit=vat_credit_to_apply,
                    stock_extra=stock_extra,
                )
                if osno_ip:
                    osno_ip['owner_extra'] = owner_extra_profit
                    osno_ip['owner_extra_base'] = owner_extra_profit_base
                results.append(('ОСНО + НДС 22% (ИП)', osno_ip, True))

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
                'fixed_contrib': fixed_contrib,
                'employees': employees,
                'salary': salary,
                'fot_mode': fot_mode,
                'fot_annual': fot_annual,
                'other_mode': other_mode,
                'other_percent': other_percent,
                'other_amount': other_amount,
                'transition_mode': transition_mode,
                'accumulated_vat_credit': accumulated_vat_credit,
                'stock_expense_amount': stock_expense_amount,
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
