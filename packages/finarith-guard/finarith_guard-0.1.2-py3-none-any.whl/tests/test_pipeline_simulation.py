from finarith_guard import SafeFloat


def test_price_pipeline():

    prices = [
        SafeFloat(100),
        SafeFloat(250),
        SafeFloat(50)
    ]

    tax = SafeFloat(1.10)

    totals = []

    for p in prices:

        total = p * tax
        totals.append(total.unwrap())

    assert len(totals) == 3

    assert totals[0] == 110.0
