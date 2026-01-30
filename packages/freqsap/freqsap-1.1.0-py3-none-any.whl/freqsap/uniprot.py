"""Module for interacting with the UniProt API."""

from __future__ import annotations
import sys
import requests
from freqsap.accession import Accession
from freqsap.interfaces import ProteinVariantAPI
from freqsap.protein import Protein
from freqsap.variation import Variation


class UniProt(ProteinVariantAPI):
    """Interface to the UniProt protein database API.

    Provides methods to query protein information and variations from UniProt.
    """

    def __init__(self):
        """Initialize the UniProt API interface.

        Sets up default query parameters, HTTP headers, and connection timeout.
        """
        self._params = {"fields": ["accession", "xref_dbsnp"]}
        self._headers = {"accept": "application/json"}
        self._timeout = 3

    def get(self, accession: Accession) -> Protein:
        """Retrieve protein and its variations from UniProt.

        Args:
            accession (Accession): The protein accession identifier.

        Returns:
            Protein: The protein object with its variations.
        """
        response = self.query(accession)
        variations = [self.parse(feature) for feature in response["features"]]

        return Protein(accession, variations)

    def query(self, accession: str) -> dict:
        """Query UniProt for protein data.

        Args:
            accession (str): The protein accession identifier.

        Returns:
            dict: JSON response from UniProt API.

        Raises:
            requests.HTTPError: If the request fails.
        """
        base_url = f"https://rest.uniprot.org/uniprotkb/{accession}"
        response = self.request(base_url)

        if not response.ok:
            response.raise_for_status()
            sys.exit()

        return response.json()

    def parse(self, feature: dict) -> Variation | None:
        """Parse a feature dictionary to extract variation information.

        Args:
            feature (dict): Feature dictionary from UniProt response.

        Returns:
            Variation | None: Variation object if a valid dbSNP reference is found, None otherwise.
        """
        if feature["type"] != "Natural variant":
            return None

        xrefs = feature["featureCrossReferences"]
        position = int(feature["location"]["start"]["value"])

        for ref in xrefs:
            if self.is_dbsnp(ref):
                return Variation(ref["id"], position=position)

        return None

    def request(self, url: str) -> requests.Response:
        """Make an HTTP GET request to UniProt.

        Args:
            url (str): The URL to request.

        Returns:
            requests.Response: The HTTP response.
        """
        return requests.get(url, headers=self._headers, params=self._params, timeout=self._timeout)

    def is_dbsnp(self, xref: dict) -> bool:
        """Check if a cross-reference is a dbSNP reference.

        Args:
            xref (dict): Cross-reference dictionary.

        Returns:
            bool: True if the reference is from dbSNP and starts with 'rs', False otherwise.
        """
        return xref.get("database") == "dbSNP" and xref.get("id", "").startswith("rs")

    def available(self) -> bool:
        """Check if the UniProt API is available.

        Returns:
            bool: True if the service is available, False otherwise.
        """
        return self.request("https://rest.uniprot.org/uniprotkb/P68871").ok
