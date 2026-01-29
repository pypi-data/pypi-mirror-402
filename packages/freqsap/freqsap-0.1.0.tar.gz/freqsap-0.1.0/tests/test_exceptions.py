from freqsap.exceptions import AccessionNotFoundError


def test_can_create():
    """Test whether exception can be instantiated."""
    actual = AccessionNotFoundError("")
    assert actual is not None
