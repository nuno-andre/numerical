import pytest

from numerical import Duodecimal, DuodecimalXE, DuodecimalXZ

INVALID = [
    'ñ982',
    '982ñ',
    '+982',
    '--982',
    '-982-',
    '982-',
    '-982.982.982',
    '982.982.'
    '.982',
]


def test_invalid_strings():
    for invalid in INVALID:
        with pytest.raises(ValueError):
            Duodecimal(invalid)


VALID = [
    '982AB',
    '-AB982',
    '-982.AB',
    'AB.982',
]


def test_valid_strings():
    for cls, a, b in (
        (Duodecimal, 'A', 'B'),
        (DuodecimalXE, 'X', 'E'),
        (DuodecimalXZ, 'X', 'Z'),
    ):
        for valid in VALID:
            valid = valid.replace('A', a).replace('B', b)
            cls(valid)



def test_casing():
    assert Duodecimal('982a').value == Duodecimal('982A').value



def test_convert_decorator():
    class Test:
        def __add__(self, other):
            return 5

        def __radd__(self, other):
            return 8

    e = Duodecimal('982')
    t = Test()

    assert t + e == 5
    assert e + t == 8
