"""Command-line interface for the freqsap package.

This module provides the main entry point for querying protein variants
and their population frequencies from various databases.
"""

from __future__ import annotations
import argparse
import csv
import sys
from pathlib import Path
from freqsap.accession import Accession
from freqsap.dbsnp import DBSNP
from freqsap.ebi import EBI
from freqsap.interfaces import ProteinVariantAPI
from freqsap.interfaces import VariantFrequencyAPI
from freqsap.report import ReferenceSNPReport
from freqsap.uniprot import UniProt


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments containing:
            - accession: Protein accession identifier
            - output: Path to output file
            - protein_api: Protein variant API choice (uniprot or ebi)
            - frequency_api: Variant frequency API choice (dbsnp)
            - delimiter: Output file delimiter (default: tab)
    """
    parser = argparse.ArgumentParser(description="Query protein variants and their frequencies from various databases.")

    parser.add_argument("accession", type=str, help="Protein accession identifier to query")

    parser.add_argument("output", type=str, help="Path to output file for results")

    parser.add_argument(
        "--protein-api",
        type=str,
        choices=["uniprot", "ebi"],
        default="ebi",
        help="Protein variant API to use (default: ebi)",
    )

    parser.add_argument(
        "--frequency-api",
        type=str,
        choices=["dbsnp"],
        default="dbsnp",
        help="Variant frequency API to use (default: dbsnp)",
    )

    parser.add_argument("--delimiter", type=str, default="\t", help="Delimiter for output file (default: tab)")

    return parser.parse_args()


def get_protein_api(api_name: str) -> ProteinVariantAPI:
    """Instantiate the chosen protein API.

    Args:
        api_name: Name of the protein API to instantiate ('uniprot' or 'ebi')

    Returns:
        ProteinVariantAPI: An instance of the requested protein variant API

    Raises:
        KeyError: If the api_name is not recognized
    """
    apis = {"uniprot": UniProt, "ebi": EBI}
    return apis[api_name]()


def get_frequency_api(api_name: str) -> VariantFrequencyAPI:
    """Instantiate the chosen frequency API.

    Args:
        api_name: Name of the frequency API to instantiate ('dbsnp')

    Returns:
        VariantFrequencyAPI: An instance of the requested variant frequency API

    Raises:
        KeyError: If the api_name is not recognized
    """
    apis = {"dbsnp": DBSNP}
    return apis[api_name]()


def write_reports(reports: list[ReferenceSNPReport], output_path: str, delimiter: str) -> None:
    r"""Write all reports to the output file in delimited format.

    Args:
        reports: List of ReferenceSNPReport objects to write
        output_path: Path to the output file
        delimiter: Character to use as field delimiter (e.g., '\t' or ',')

    Returns:
        None

    Raises:
        IOError: If the output file cannot be written
        IndexError: If reports list is empty
    """
    header = reports[0].header()
    for report in reports:
        other = report.header()
        if header < other:
            header.extend(other[len(header) :])

    with Path.open(output_path, "w") as file:
        writer = csv.DictWriter(file, fieldnames=header, delimiter=delimiter, extrasaction="ignore")
        writer.writeheader()

        for report in reports:
            writer.writerows(report.rows())


def check_apis(protein_api: ProteinVariantAPI, frequency_api: VariantFrequencyAPI) -> None:
    """Check if the chosen APIs are available.

    Args:
        protein_api: Instance of the protein variant API
        frequency_api: Instance of the variant frequency API

    Returns:
        None

    Raises:
        SystemExit: If either API is not available
    """
    if not protein_api.available():
        sys.exit(1)

    if not frequency_api.available():
        sys.exit(1)


def main() -> None:
    """Main entry point for the freqsap application.

    This function orchestrates the entire workflow:
    1. Parses command line arguments
    2. Instantiates the chosen protein and frequency APIs
    3. Validates API availability
    4. Queries protein variants using the accession
    5. Collects frequency reports for all variants
    6. Writes results to the specified output file

    Returns:
        None

    Raises:
        SystemExit: If APIs are unavailable or other errors occur
    """
    args = parse_args()

    # Instantiate chosen APIs
    protein_api = get_protein_api(args.protein_api)
    frequency_api = get_frequency_api(args.frequency_api)

    # Check if APIs are available
    check_apis(args, protein_api, frequency_api)

    # Query protein variants
    accession = Accession(args.accession)
    protein = protein_api.get(accession)

    # Collect frequency reports for all variants
    reports: list[ReferenceSNPReport] = list(
        filter(None, [frequency_api.get(variation) for variation in protein.variations]),
    )

    # Write reports to output file
    write_reports(reports, args.output, args.delimiter)


if __name__ == "__main__":
    main()
