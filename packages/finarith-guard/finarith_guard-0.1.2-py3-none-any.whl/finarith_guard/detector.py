from decimal import Decimal, getcontext
import math
from .policy import GuardPolicy


getcontext().prec = 50


def detect_float_error(a, b, float_result, op):

    da = Decimal(str(a))
    db = Decimal(str(b))

    if op == "+":
        ref = da + db
    elif op == "-":
        ref = da - db
    elif op == "*":
        ref = da * db
    elif op == "/":
        ref = da / db
    else:
        return None

    ref_float = float(ref)

    abs_err = abs(float_result - ref_float)

    rel_err = abs_err / max(abs(ref_float), 1e-30)

    if abs_err > GuardPolicy.MAX_ABS_ERROR or rel_err > GuardPolicy.MAX_REL_ERROR:
        return {
            "abs_error": abs_err,
            "rel_error": rel_err,
            "expected": ref,
            "got": float_result
        }

    return None
