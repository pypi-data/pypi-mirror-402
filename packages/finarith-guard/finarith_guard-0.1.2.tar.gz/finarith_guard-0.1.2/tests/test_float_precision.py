import warnings
from finarith_guard import SafeFloat, ArithmeticRiskWarning


def test_float_addition_precision_warning():

    a = SafeFloat(0.1)
    b = SafeFloat(0.2)

    with warnings.catch_warnings(record=True) as w:

        warnings.simplefilter("always", ArithmeticRiskWarning)

        _ = a + b

        assert len(w) == 1
        assert "Arithmetic Risk Detected" in str(w[0].message)
