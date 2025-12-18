"""Calculator package exposing high-level API."""

from .engine import run_calculation
from .models import CalcInput, CalcResult

__all__ = ["CalcInput", "CalcResult", "run_calculation"]
