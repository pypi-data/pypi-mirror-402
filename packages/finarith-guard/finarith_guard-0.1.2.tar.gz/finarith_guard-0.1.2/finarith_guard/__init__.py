"""
finarith_guard
---------------

Runtime arithmetic safety guard for Python.

Detects floating-point precision risks, rounding problems,
and unsafe arithmetic operations in fintech pipelines.
"""

from .guard import SafeFloat
from .policy import GuardPolicy
from .exceptions import ArithmeticRiskWarning, ArithmeticRiskError

__all__ = [
    "SafeFloat",
    "GuardPolicy",
    "ArithmeticRiskWarning",
    "ArithmeticRiskError"
]

__version__ = "0.1.2"
