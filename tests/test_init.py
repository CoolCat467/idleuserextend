"""Test __init__.py."""

import idleuserextend

assert hasattr(idleuserextend, "idleuserextend")
assert idleuserextend.__title__ == "idleuserextend"
assert hasattr(idleuserextend, "check_installed")
assert callable(
    idleuserextend.check_installed,
)


def test_get_mangled_dunder() -> None:
    assert idleuserextend.get_mangled(3, "__init__") == "__init__"


def test_get_mangled_regular() -> None:
    assert idleuserextend.get_mangled(3, "pop") == "pop"


def test_get_mangled() -> None:
    assert idleuserextend.get_mangled(3, "__fish") == "_int__fish"
