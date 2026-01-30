import finarith_guard


def test_version_exists():

    assert hasattr(finarith_guard, "__version__")
    assert isinstance(finarith_guard.__version__, str)
