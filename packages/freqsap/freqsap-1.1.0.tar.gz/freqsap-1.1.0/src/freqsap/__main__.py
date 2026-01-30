"""Command-line interface for the freqsap package.

This module provides the main entry point for querying protein variants
and their population frequencies from various databases.
"""

from __future__ import annotations
import argparse
import csv
import sys
from pathlib import Path
from openpyxl import Workbook
from freqsap.accession import Accession
from freqsap.dbsnp import DBSNP
from freqsap.ebi import EBI
from freqsap.interfaces import ProteinVariantAPI
from freqsap.interfaces import VariantFrequencyAPI
from freqsap.report import PopulationFilter
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

    parser.add_argument(
        "-a",
        "--accession",
        type=str,
        required=True,
        help="Protein accession number.",
    )
    parser.add_argument(
        "-r",
        "--regions",
        type=str,
        required=True,
        help="Comma-separated list of regions.",
    )
    parser.add_argument(
        "-d",
        "--delimiter",
        type=str,
        default="\t",
        help="Delimiter for output file (default: tab). Use 'xlsx' to output Excel format. Supports escape sequences like \\t, \\n, etc.",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        type=str,
        help="Output file name.",
    )

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

    args = parser.parse_args()
    # Convert escape sequences in delimiter
    args.delimiter = args.delimiter.encode().decode("unicode_escape")
    return args


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


def write_reports(reports: list[ReferenceSNPReport], regions: list[str], output_path: str, delimiter: str) -> None:
    r"""Write all reports to the output file in delimited format.

    Args:
        reports: List of ReferenceSNPReport objects to write
        regions: List of region populations to report.
        output_path: Path to the output file
        delimiter: Character to use as field delimiter (e.g., '\t' or ','). Use 'xlsx' for Excel format.

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

    if delimiter.lower() == "xlsx":
        _write_xlsx(reports, regions, output_path, header)
    else:
        _write_csv(reports, regions, output_path, header, delimiter)


def _write_csv(
    reports: list[ReferenceSNPReport],
    regions: list[str],
    output_path: str,
    header: list[str],
    delimiter: str,
) -> None:
    """Write reports to a delimited text file (CSV/TSV).

    Args:
        reports: List of ReferenceSNPReport objects to write
        regions: List of populations to report.
        output_path: Path to the output file
        header: List of column headers
        delimiter: Character to use as field delimiter

    Returns:
        None
    """
    with Path.open(output_path, "w") as file:
        writer = csv.DictWriter(file, fieldnames=header, delimiter=delimiter, extrasaction="ignore")
        writer.writeheader()

        for report in reports:
            rows = PopulationFilter.apply(regions, report)
            writer.writerows(rows)


def _write_xlsx(reports: list[ReferenceSNPReport], regions: list[str], output_path: str, header: list[str]) -> None:
    """Write reports to an Excel file (XLSX format).

    Args:
        reports: List of ReferenceSNPReport objects to write
        regions: List of region populations to report.
        output_path: Path to the output file
        header: List of column headers

    Returns:
        None

    Raises:
        ImportError: If openpyxl is not installed
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Variants"

    # Write header
    ws.append(header)

    # Write data rows
    for report in reports:
        rows = PopulationFilter.apply(regions, report)
        for row_dict in rows:
            # Convert dict to list in the correct order according to header
            row = [row_dict.get(col, "") for col in header]
            ws.append(row)

    wb.save(output_path)


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
    check_apis(protein_api, frequency_api)

    # Query protein variants
    accession = Accession(args.accession)
    protein = protein_api.get(accession)

    # Collect frequency reports for all variants
    reports: list[ReferenceSNPReport] = list(
        filter(None, [frequency_api.get(variation) for variation in protein.variations]),
    )

    # Write reports to output file
    write_reports(reports, args.regions.split(","), args.output_file, args.delimiter)


if __name__ == "__main__":
    main()
