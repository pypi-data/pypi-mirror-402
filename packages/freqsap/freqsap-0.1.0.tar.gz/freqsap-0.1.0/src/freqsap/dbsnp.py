"""Module for interacting with the dbSNP database API."""

from __future__ import annotations
import re
import requests
from freqsap.allele import Allele
from freqsap.interfaces import VariantFrequencyAPI
from freqsap.report import ReferenceSNPReport
from freqsap.study import Study
from freqsap.variation import Variation


class DBSNP(VariantFrequencyAPI):
    """Interface to interact with the dbSNP database to obtain frequency information for specific variants."""

    def __init__(self):
        """Initialize the DBSNP API interface.

        Sets up connection parameters and data parsing requirements.
        """
        self._timeout = 10
        self._num_required_sections = 2
        self._num_required_columns = 6

    def get(self, variation: Variation) -> ReferenceSNPReport | None:
        """Get the ReferenceSNPReport for the given single amino-acid polymorphism.

        Args:
            variation (Variation): Variation for which to get the report.

        Returns:
            ReferenceSNPReport | None: Report if it is found on dbSNP, otherwise None.
        """
        freq_url = f"https://www.ncbi.nlm.nih.gov/snp/{variation}/download/frequency"
        r = requests.get(freq_url, headers={"Accept": "application/json"}, timeout=self._timeout)

        sections = [re.split(r"\n+", x.strip()) for x in re.split(r"#Frequency Data Table", r.text)]

        if len(sections) < self._num_required_sections:
            return None

        metadata_section = sections[0]
        studies_section = sections[1]

        metadata_section.pop()
        studies_section.pop(0)

        metadata: dict = {}
        for entry in metadata_section:
            key, value = entry.strip("#").split("\t")
            metadata[key] = value

        studies: list[Study] = []
        studies_section.pop(0).strip("#").split("\t")

        for entry in studies_section:
            tokens = entry.split("\t")

            if len(tokens) < self._num_required_columns:
                return None

            source = tokens[0]
            population = tokens[1]
            group = tokens[2]
            size = tokens[3]
            ref = tokens[4]
            alts = tokens[5]

            ref_nucelotide, ref_frequency = ref.split("=")
            reference = Allele(ref_nucelotide, ref_frequency)
            alternatives: list[Allele] = []
            for alt in alts.split(","):
                alt_nucleotide, alt_frequency = alt.split("=")
                alternatives.append(Allele(alt_nucleotide, alt_frequency))

            study = Study(source, population, group, size, reference, alternatives)
            studies.append(study)

        return ReferenceSNPReport(variation, metadata, studies)

    def available(self) -> bool:
        """Check whether the service is available.

        Returns:
            bool: True if the service is available, False otherwise.
        """
        # Placeholder implementation
        return True
