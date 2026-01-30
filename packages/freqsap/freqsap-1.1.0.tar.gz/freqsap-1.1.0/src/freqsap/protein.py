"""Module for representing protein data."""

from typing import Iterable
from freqsap.accession import Accession
from freqsap.variation import Variation


class Protein:
    """Represents a protein with its accession and associated variations.

    Attributes:
        _accession (Accession): The protein accession identifier.
        _variations (Iterable[Variation]): Collection of genetic variations in this protein.
    """

    def __init__(self, accession: Accession, variations: Iterable[Variation]):
        """Initialize a Protein object.

        Args:
            accession (Accession): The protein accession identifier.
            variations (Iterable[Variation]): Collection of variations associated with this protein.
        """
        self._accession = accession
        self._variations = variations

    @property
    def variations(self) -> Iterable[Variation]:
        """Get the variations associated with this protein."""
        return self._variations
