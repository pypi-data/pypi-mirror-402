"""Module for representing genetic alleles."""

from dataclasses import dataclass


@dataclass
class Allele:
    """Class to represent an allele.

    Attributes:
        nucleotide (str): The nucleotide variant (e.g., 'A', 'T', 'C', 'G').
        frequency (float): The frequency of this allele in a population.
    """

    nucleotide: str
    frequency: float
