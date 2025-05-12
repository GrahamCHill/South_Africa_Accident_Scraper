"""
PDF Reader module for the RTMC Scraper.

This module provides functionality for extracting data from PDF files.
"""
import os
import re
import tabula
import pandas as pd
from typing import List, Dict, Optional, Tuple
from Scraper import AccidentRecord


def extract_year_from_pdf(pdf_path: str) -> Optional[int]:
    """
    Extract the year from the PDF filename or content.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        The extracted year as an integer, or None if no year could be extracted
    """
    # First try to extract year from filename
    filename = os.path.basename(pdf_path)
    year_match = re.search(r'20\d{2}', filename)
    if year_match:
        return int(year_match.group(0))

    # If that fails, try to extract year from the PDF content
    try:
        # Extract text from the first page
        tables = tabula.read_pdf(pdf_path, pages=1, multiple_tables=True)
        if tables:
            # Convert tables to string and search for year
            for table in tables:
                table_str = str(table)
                year_match = re.search(r'20\d{2}', table_str)
                if year_match:
                    return int(year_match.group(0))
    except Exception as e:
        print(f"[RTMC] Error extracting year from PDF {pdf_path}: {e}")

    # If all else fails, return None
    return None


def extract_tables_from_pdf(pdf_path: str) -> List[pd.DataFrame]:
    """
    Extract tables from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        A list of pandas DataFrames containing the extracted tables
    """
    try:
        tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
        print(f"[RTMC] Extracted {len(tables)} tables from {pdf_path}")
        return tables
    except Exception as e:
        print(f"[RTMC] Error extracting tables from {pdf_path}: {e}")
        return []


def extract_accident_data_from_tables(tables: List[pd.DataFrame], year: int, source_name: str) -> List[AccidentRecord]:
    """
    Extract accident data from tables.

    Args:
        tables: List of pandas DataFrames containing tables extracted from a PDF
        year: The year of the data
        source_name: The name of the data source

    Returns:
        A list of AccidentRecord objects
    """
    records = []

    for table in tables:
        # Skip empty tables
        if table.empty:
            continue

        # Try to identify tables with accident data
        # Look for columns that might contain region names and accident counts
        for col in table.columns:
            if 'province' in col.lower() or 'region' in col.lower():
                # This table might contain accident data by region
                for _, row in table.iterrows():
                    region = None
                    accident_count = None

                    # Try to extract region and accident count
                    for col_name in table.columns:
                        col_lower = col_name.lower()
                        if 'province' in col_lower or 'region' in col_lower:
                            region = row[col_name]
                        elif 'accident' in col_lower or 'crash' in col_lower or 'fatal' in col_lower:
                            try:
                                accident_count = int(row[col_name])
                            except (ValueError, TypeError):
                                # Not a number, skip
                                pass

                    # If we found both region and accident count, create a record
                    if region and accident_count:
                        record = AccidentRecord(region, accident_count, year, source_name)
                        records.append(record)

    return records


def process_pdf_files(pdf_files: List[str], source_name: str) -> List[AccidentRecord]:
    """
    Process a list of PDF files and extract accident records.

    Args:
        pdf_files: List of paths to PDF files
        source_name: The name of the data source

    Returns:
        A list of AccidentRecord objects
    """
    records = []

    for pdf_path in pdf_files:
        print(f"[RTMC] Processing PDF: {pdf_path}")

        # Extract year from PDF
        year = extract_year_from_pdf(pdf_path)
        if not year:
            print(f"[RTMC] Could not extract year from {pdf_path}, skipping")
            continue

        # Extract tables from PDF
        tables = extract_tables_from_pdf(pdf_path)
        if not tables:
            print(f"[RTMC] No tables found in {pdf_path}, skipping")
            continue

        # Extract accident data from tables
        pdf_records = extract_accident_data_from_tables(tables, year, source_name)
        if pdf_records:
            records.extend(pdf_records)
            print(f"[RTMC] Extracted {len(pdf_records)} records from {pdf_path}")
        else:
            print(f"[RTMC] No accident data found in {pdf_path}")

    return records
