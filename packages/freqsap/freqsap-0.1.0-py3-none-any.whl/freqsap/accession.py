"""Module for handling protein accession identifiers."""

import re


class Accession:
    """Protein accession identifier.

    Validates and stores UniProt accession identifiers according to the
    UniProt accession number format.
    """

    def __init__(self, accession: str):
        """Initialize the Accession object.

        Args:
            accession (str): The protein accession identifier string.
        """
        self._id = accession
        self._pattern = r"[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2}"

    def valid(self) -> bool:
        """Validate the accession using the built in regex pattern.

        Returns:
            bool: True if valid, otherwise False.
        """
        return re.fullmatch(self._pattern, self._id) is not None

    def __str__(self) -> str:
        """Return the string representation of the accession.

        Returns:
            str: The accession identifier string.
        """
        return self._id
