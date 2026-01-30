import warnings
from finarith_guard import SafeFloat


def test_safe_division_no_warning():

    a = SafeFloat(10)
    b = SafeFloat(2)

    with warnings.catch_warnings(record=True) as w:

        warnings.simplefilter("always")

        result = a / b

        assert result.unwrap() == 5.0
        assert len(w) == 0
