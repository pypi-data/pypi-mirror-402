import warnings
from finarith_guard import SafeFloat


def test_bulk_precision_detection():

    warning_count = 0

    for i in range(1, 500):

        a = SafeFloat(i * 0.1)
        b = SafeFloat(i * 0.2)

        with warnings.catch_warnings(record=True) as w:

            warnings.simplefilter("always")

            _ = a + b

            if len(w) > 0:
                warning_count += 1

    assert warning_count > 0
