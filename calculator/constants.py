"""Domain constants and defaults for calculator."""

MONTH_KEYS = [
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
]

AUSN_REVENUE_LIMIT = 60_000_000
AUSN_EMPLOYEE_LIMIT = 5

THRESHOLD_1_PERCENT = 300_000
DEFAULT_FIXED_CONTRIB = 57_390
INSURANCE_RATE_ON_FOT = 0.30

USN_INCOME_RATE = 0.06
USN_PROFIT_RATE = 0.15
USN_PROFIT_MIN_RATE = 0.01
USN_REDUCTION_LIMIT = 0.50

AUSN_INCOME_RATE = 0.08
AUSN_PROFIT_RATE = 0.20
AUSN_PROFIT_MIN_RATE = 0.03

VAT_RATE_REDUCED = 5
VAT_RATE_STANDARD = 22

PROFIT_TAX_RATE = 0.25

NDFL_BRACKETS_2026 = [
    (2_400_000, 0.13),
    (5_000_000, 0.15),
    (20_000_000, 0.18),
    (50_000_000, 0.20),
    (None, 0.22),
]
