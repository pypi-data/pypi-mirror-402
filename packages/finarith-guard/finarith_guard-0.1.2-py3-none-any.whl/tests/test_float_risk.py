from finarith_guard.guard import SafeFloat
import warnings


def test_float_precision_warning():

    a = SafeFloat(0.1)
    b = SafeFloat(0.2)

    with warnings.catch_warnings(record=True) as w:

        warnings.simplefilter("always")

        c = a + b

        assert len(w) == 1
        assert "Arithmetic Risk Detected" in str(w[0].message)
