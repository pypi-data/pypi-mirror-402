"""Module for interacting with the EBI Proteins API."""

from __future__ import annotations
from typing import Generator
import requests
from freqsap.accession import Accession
from freqsap.exceptions import AccessionNotFoundError
from freqsap.interfaces import ProteinVariantAPI
from freqsap.protein import Protein
from freqsap.variation import Variation


class EBI(ProteinVariantAPI):
    """Class to access the EBI protein API."""

    def __init__(self):
        """Initialize the EBI API interface.

        Sets up HTTP headers and connection timeout.
        """
        self._headers = {"Accept": "application/json"}
        self._timeout = 3

    def _request(self, url: str) -> requests.Response:
        """Private function to submit requests.

        Args:
            url (str): Base URL to query.

        Returns:
            requests.Response: Response returned by the server.
        """
        return requests.get(url, headers=self._headers, timeout=self._timeout)

    def available(self) -> bool:
        """Check whether the service is available.

        Returns:
            bool: True if service is available, False otherwise.
        """
        expected_response = '{"requestedURL":"https://www.ebi.ac.uk/proteins/api/variation?offset=0&size=100","errorMessage":["At least one of these request parameters is required: accession, disease, omim, evidence, taxid, dbtype or dbid"]}'
        reponse = self._request("https://www.ebi.ac.uk/proteins/api/variation?offset=0&size=100").text

        return reponse == expected_response

    def get(self, accession: Accession) -> Protein:
        """Get the protein represented by the Accession.

        Args:
            accession (Accession): Accession of the Protein.

        Returns:
            Protein: Protein specified by the accession.
        """
        response = self._request(f"https://www.ebi.ac.uk/proteins/api/variation/{accession}")
        _check_response(accession, response)
        variations = list(_get_variants(response.json()))
        return Protein(accession, variations)


def _get_dbsnp_id(xrefs: list[dict]) -> str | None:
    """Parse dbSNP id from the xrefs entry. Private function.

    Args:
        xrefs (list[dict]): List of xrefs specified in the protein.

    Returns:
        str | None: dbSNP id, if found, otherwise None.
    """
    for xref in xrefs:
        if xref.get("name") in ["dbSNP", "gnomAD", "TOPMed"] and xref.get("id", "").startswith("rs"):
            return xref["id"]
    return None


def _check_response(accession: Accession, response: requests.Response) -> None:
    """Check the response for the accession for errors.

    Args:
        accession (Accession): Accession which was searched.
        response (requests.Response): Response obtained from the server.

    Raises:
        AccessionNotFound: Raises exception if the accession wasn't found.
        Raises all other exceptions raised by the requests module.
    """
    if not response.ok:
        http_not_found_error = 404
        if response.reason == "Not Found" and response.status_code == http_not_found_error:
            raise AccessionNotFoundError(message=f"Accession {accession} not found.")
        response.raise_for_status()


def _get_variants(response: dict) -> Generator[Variation]:
    """Extract variations from EBI API response.

    Args:
        response (dict): JSON response from EBI API containing protein features.

    Yields:
        Variation: Each variation found with a valid dbSNP reference ID.
    """
    variants = list(filter(lambda x: x.get("type") == "VARIANT", response["features"]))
    for var in variants:
        if ref := _get_dbsnp_id(var["xrefs"]):
            yield Variation(ref, var["begin"])
