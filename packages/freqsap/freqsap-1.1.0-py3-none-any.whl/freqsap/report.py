"""Module for generating reports from variant frequency data."""

from __future__ import annotations
from typing import ClassVar
from freqsap.study import Study
from freqsap.variation import Variation


class ReferenceSNPReport:
    """Report containing frequency data for a reference SNP.

    Aggregates metadata and study data for a specific genetic variation.

    Attributes:
        _variation (Variation): The genetic variation this report describes.
        _metadata (dict): Metadata about the variation.
        _studies (list[Study]): List of population studies with frequency data.
    """

    def __init__(self, variation: Variation, metadata: dict, studies: list[Study]):
        """Initialize a ReferenceSNPReport.

        Args:
            variation (Variation): The genetic variation being reported on.
            metadata (dict): Metadata associated with the variation.
            studies (list[Study]): List of studies containing frequency information.
        """
        self._variation: Variation = variation
        self._metadata: dict = metadata
        self._studies: list[Study] = studies

    def header(self) -> list[str]:
        """Generate column headers for the report.

        Combines base fields (id, position) with study-specific headers,
        ensuring no duplicate fields.

        Returns:
            list[str]: List of column header names.
        """
        fields = ["id", "position"]
        for study in self._studies:
            for entry in study.header():
                if entry not in fields:
                    fields.append(entry)
        return fields

    def rows(self) -> list[dict]:
        """Generate data rows for the report.

        Each row contains the variation ID and position combined with data from one study.

        Returns:
            list[dict]: List of dictionaries, each representing one row of data.
        """
        _base = {"id": self._variation.ref, "position": self._variation.position}
        return [_base | study.row() for study in self._studies]


class PopulationFilter:
    """Class to filter reports for only certain populations."""

    _mapping: ClassVar[dict[str, set[str]]] = {
        "Africa": {"African"},
        "North America": {
            "American",
            "African American",
            "Mexican",
            "Cuban",
            "European American",
            "NativeAmerican",
            "NativeHawaiian",
        },
        "Asia": {
            "Asian",
            "East Asian",
            "Central Asia",
            "JAPANESE",
            "KOREAN",
            "South Asian",
            "SouthAsian",
        },
        "Europe": {
            "Europe",
            "European",
            "Finnish from FINRISK project",
            "Spanish controls",
            "TWIN COHORT",
        },
        "Global": {"Global", "Total"},
        "South America": {
            "Latin American 1",
            "Latin American 2",
            "Dominican",
            "PuertoRican",
            "SouthAmerican",
        },
        "Middle East": {"Middle Eastern", "Near_East"},
        "Other": {"Other"},
    }

    @staticmethod
    def apply(regions: list[str], report: ReferenceSNPReport) -> list[dict]:
        """Filter reports for certain regions.

        Args:
            regions (list[str]): List of regions to include.
            report (ReferenceSNPReport): Report from which to filter rows.

        Returns:
            list[dict]: Rows from only the specified regions.
        """
        populations = set.union(*[PopulationFilter._mapping.get(group, set()) for group in regions])
        return list(filter(lambda x: x.get("population") in populations, report.rows()))
