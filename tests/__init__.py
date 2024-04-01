import pytest  # noqa: F401


def test_imports():
    from lovecraft import cli
    from lovecraft.input import letters, stories

    assert cli
    assert letters
    assert stories
