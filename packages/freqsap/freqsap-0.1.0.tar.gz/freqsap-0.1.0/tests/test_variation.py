import pytest
from freqsap.variation import Variation


def test_init():
    """Test whether Variation can be instantiated."""
    sut = Variation("", 0)
    assert sut is not None


@pytest.mark.parametrize(
    ("ref", "pos", "expected"),
    [
        ("test", 100, False),
        ("rs1234", 10, True),
        ("rs1234", -10, False),
    ],
)
def test_valid(ref: str, pos: int, expected: bool):
    """Test whether a variation is valid."""
    sut = Variation(ref, pos)  # arrange
    actual = sut.valid()  # act
    assert actual == expected  # assert


def test_to_string():
    """Test string representation of a variation."""
    sut = Variation("rs1234", 0)
    assert str(sut) == "rs1234"
