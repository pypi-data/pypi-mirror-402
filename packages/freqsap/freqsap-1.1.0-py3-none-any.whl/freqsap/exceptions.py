"""Module for custom exceptions used in freqsap."""


class AccessionNotFoundError(Exception):
    """Exception raised when a protein accession identifier is not found in the database.

    Attributes:
        message (str): Explanation of the error.
    """

    def __init__(self, message: str):
        """Initialize the AccessionNotFoundError.

        Args:
            message (str): Explanation of the error.
        """
        super().__init__(message)
