"""Module for representing population study data."""

from __future__ import annotations
from dataclasses import dataclass
from freqsap.allele import Allele


@dataclass
class Study:
    """Represents a population genetics study with allele frequency data.

    Attributes:
        source (str): The data source or database name.
        population (str): The population identifier.
        group (str): The population group or ethnicity.
        size (int): The sample size of the study.
        reference (Allele): The reference allele with its frequency.
        alternatives (list[Allele]): List of alternative alleles with their frequencies.
    """

    source: str
    population: str
    group: str
    size: int
    reference: Allele
    alternatives: list[Allele]

    def header(self) -> list[str]:
        """Get the column headers for this study's data.

        Returns:
            list[str]: List of column header names.
        """
        return self.row().keys()

    def row(self) -> dict:
        """Convert study data to a dictionary row format.

        Creates a dictionary with study metadata, reference allele data,
        and all alternative allele data with dynamically numbered columns.

        Returns:
            dict: Dictionary containing all study data in row format.
        """
        base = {
            "study": self.source,
            "population": self.population,
            "group": self.group,
            "size": self.size,
            "ref_allele_na": self.reference.nucleotide,
            "ref_allele_freq": self.reference.frequency,
        }

        for i in range(len(self.alternatives)):
            alternative = self.alternatives[i]
            base.update(
                {f"alt_allele_{i + 1}_na": alternative.nucleotide, f"alt_allele_{i + 1}_freq": alternative.frequency},
            )

        return base
