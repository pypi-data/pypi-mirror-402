from .detector import detect_float_error
from .policy import GuardPolicy
from .exceptions import ArithmeticRiskWarning, ArithmeticRiskError
import warnings
from decimal import Decimal, ROUND_HALF_EVEN


class SafeFloat:

    def __init__(self, value):
        self.value = float(value)

    def _handle(self, other, result, op):

        risk = detect_float_error(self.value, other.value, result, op)

        if risk:

            msg = (
                f"\n⚠ Arithmetic Risk Detected\n"
                f"Operation: {self.value} {op} {other.value}\n"
                f"Expected(Decimal): {risk['expected']}\n"
                f"Got(float): {risk['got']}\n"
                f"Abs error: {risk['abs_error']}\n"
                f"Rel error: {risk['rel_error']}"
            )

            if GuardPolicy.RAISE_ON_VIOLATION:
                raise ArithmeticRiskError(msg)

            warnings.warn(msg, ArithmeticRiskWarning)

        return SafeFloat(result)

    def __add__(self, other):
        result = self.value + other.value
        return self._handle(other, result, "+")

    def __sub__(self, other):
        result = self.value - other.value
        return self._handle(other, result, "-")

    def __mul__(self, other):
        result = self.value * other.value
        return self._handle(other, result, "*")

    def __truediv__(self, other):
        result = self.value / other.value
        return self._handle(other, result, "/")

    def __repr__(self):
        return f"SafeFloat({self.value})"

    def unwrap(self):
        return self.value

    def money(self, places=2):
        """
        Return properly rounded money value
        """
        return float(
            Decimal(str(self.value))
            .quantize(Decimal("1." + "0" * places), rounding=ROUND_HALF_EVEN)
        )
