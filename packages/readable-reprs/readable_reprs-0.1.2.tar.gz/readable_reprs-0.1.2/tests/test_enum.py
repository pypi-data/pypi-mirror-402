from enum import Enum


class Colour(str, Enum):
    RED = "RED"
    BLUE = "BLUE"
    GREEN = "GREEN"


def test_str_enum() -> None:
    assert repr(Colour.RED) == "Colour.RED"


class Flags(Enum):
    ON = 1
    OFF = 2
    FAULT = 3


def test_int_enum() -> None:
    assert repr(Flags.FAULT) == "Flags.FAULT"


def test_enum_introspection() -> None:
    assert Flags.__repr__.__name__ == "__repr__"
    assert Flags.__repr__.__qualname__ == "Enum.__repr__"
    assert Flags.__repr__.__module__ == "enum"
