from finarith_guard.guard import SafeFloat

def test_safe_division():

    a = SafeFloat(10)
    b = SafeFloat(2)

    c = a / b

    assert c.unwrap() == 5.0
