"""Module for representing genetic variations."""

from dataclasses import dataclass


@dataclass
class Variation:
    """Represents a genetic variation.

    Attributes:
        ref (str): The reference SNP identifier (e.g., 'rs123456').
        position (int): The position of the variation in the protein sequence.
    """

    ref: str
    position: int

    def valid(self) -> bool:
        """Validate the variation.

        Checks if the reference ID starts with 'rs' and position is positive.

        Returns:
            bool: True if valid, False otherwise.
        """
        # Placeholder implementation
        return self.ref.startswith("rs") and self.position > 0

    def __str__(self) -> str:
        """Return the string representation of the variation.

        Returns:
            str: The reference SNP identifier.
        """
        return self.ref
