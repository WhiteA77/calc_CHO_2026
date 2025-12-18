"""VAT calculation helpers."""


def calc_vat_charged(revenue: float, vat_rate: float) -> float:
    if vat_rate <= 0:
        return 0.0
    return revenue * vat_rate / (100 + vat_rate)


def calc_vat_deductible(purchases: float, share_with_vat: float, vat_rate: float) -> float:
    if vat_rate <= 0 or purchases <= 0:
        return 0.0
    base = purchases * share_with_vat / 100.0
    return calc_vat_charged(base, vat_rate)


def calc_vat_to_pay(charged: float, deductible: float, extra_credit: float = 0.0) -> float:
    return max(charged - deductible - extra_credit, 0.0)
