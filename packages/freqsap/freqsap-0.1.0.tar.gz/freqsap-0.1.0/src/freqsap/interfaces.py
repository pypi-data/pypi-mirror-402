"""Module defining abstract interfaces for protein and variant frequency APIs."""

from abc import ABC
from abc import abstractmethod
from freqsap.accession import Accession
from freqsap.protein import Protein
from freqsap.report import ReferenceSNPReport
from freqsap.variation import Variation


# Interface for protein variant data sources
class ProteinVariantAPI(ABC):
    """Abstract base class for protein variant data sources.

    Defines the interface that all protein variant API implementations must follow.
    """

    @abstractmethod
    def get(self, accession: Accession) -> Protein:
        """Retrieve protein information for the given accession.

        Args:
            accession (Accession): The protein accession identifier.

        Returns:
            Protein: The protein object with its variants.
        """

    @abstractmethod
    def available(self) -> bool:
        """Check if the API service is currently available.

        Returns:
            bool: True if the service is available, False otherwise.
        """


# Interface for variant frequency data sources
class VariantFrequencyAPI(ABC):
    """Abstract base class for variant frequency data sources.

    Defines the interface that all variant frequency API implementations must follow.
    """

    @abstractmethod
    def get(self, variation: Variation) -> ReferenceSNPReport:
        """Retrieve frequency information for the given variation.

        Args:
            variation (Variation): The genetic variation to query.

        Returns:
            ReferenceSNPReport: A report containing frequency data for the variation.
        """

    @abstractmethod
    def available(self) -> bool:
        """Check if the API service is currently available.

        Returns:
            bool: True if the service is available, False otherwise.
        """
