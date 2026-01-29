# ruff: noqa: PLR2004
import pytest
import requests
from freqsap.uniprot import UniProt
from tests import internet


@pytest.fixture
def api() -> UniProt:
    """Fixture to create UniProt API endpoint."""
    return UniProt()


@pytest.fixture
def accession():
    """Fixture to get valid protein accession as a string."""
    return "P02788"


@pytest.mark.skipif(not internet(), reason="Can't connect to network!")
def test_available():
    """Test if UniProt endpoint is available."""
    sut = UniProt()
    expected = requests.get(url="https://google.com", timeout=3).ok
    assert sut.available() == expected


@pytest.mark.skipif(not internet(), reason="Can't connect to network!")
def test_query(api: UniProt, accession: str):
    """Test whether query function returns expected result."""
    sut = api.query(accession)
    expected = 6
    assert sut["primaryAccession"] == accession
    assert len(sut["features"]) == expected


def test_is_dbsnp(api: UniProt):
    """Check whetehr an xref points to dbsnp."""
    xref = {"database": "dbSNP", "id": "rs121913547"}
    assert api.is_dbsnp(xref)


@pytest.mark.skipif(not internet(), reason="Can't connect to network!")
def test_get(api: UniProt, accession: str):
    """Test whether we can get the protein specified by the accession and it has all variations."""
    actual = api.get(accession)
    expected = 6
    assert len(actual.variations) == expected


def test_has_all_variants(api: UniProt):
    """Second test whether specified protein has all variations."""
    variants = api.get("P02792").variations
    assert len(variants) == 2
