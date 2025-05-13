"""
PDF Reader module for the RTMC Scraper.

This module provides functionality for extracting data from PDF files.
"""
import os
import re
import tabula
import pandas as pd
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io
from typing import List, Dict, Optional, Tuple
from Scraper import AccidentRecord


def read_config() -> dict:
    """
    Read configuration from the config.txt file.

    Returns:
        A dictionary containing configuration values
    """
    config = {}
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config.txt")
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    config[key.strip()] = value
        return config
    except Exception as e:
        print(f"Error reading config file: {e}")
        return {}


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


def pdf_to_text_ocr(pdf_path: str, dpi: int = 150, save_output: bool = True) -> str:
    """
    Extract text from a PDF file using OCR.

    Args:
        pdf_path: Path to the PDF file
        dpi: DPI for rendering PDF pages as images
        save_output: Whether to save the extracted text to a file

    Returns:
        Extracted text as a string
    """
    text = ""
    # Check if the output file already exists
    output_file = os.path.splitext(pdf_path)[0] + "_ocr.txt"
    if os.path.exists(output_file):
        print(f"[RTMC] OCR text file already exists for {pdf_path}, skipping OCR processing")
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                text = f.read()
            return text
        except Exception as e:
            print(f"[RTMC] Error reading existing OCR text file: {e}")
            # If there's an error reading the file, continue with OCR processing

    try:
        # Get tesseract path from config
        config = read_config()
        tesseract_cmd = config.get('tesseract_cmd')
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        # Open the PDF file
        pdf_document = fitz.open(pdf_path)
        total_pages = len(pdf_document)
        progress_bar_width = 50  # Width of the progress bar

        print(f"[RTMC] Starting OCR processing for {os.path.basename(pdf_path)} ({total_pages} pages)")

        for page_number in range(total_pages):
            # Show OCR progress
            progress = int(100 * page_number / total_pages)
            filled_length = int(progress_bar_width * page_number // total_pages)
            bar = '█' * filled_length + '░' * (progress_bar_width - filled_length)
            print(f"\r[RTMC] OCR Progress: |{bar}| {progress}% (Page {page_number + 1}/{total_pages})", end="")

            # Render page as an image
            page = pdf_document[page_number]
            pix = page.get_pixmap(dpi=dpi)
            image = Image.open(io.BytesIO(pix.tobytes("png")))

            # Perform OCR on the image
            ocr_text = pytesseract.image_to_string(image)
            text += f"--- Page {page_number + 1} ---\n"
            text += ocr_text + "\n"

        # Show final OCR progress
        bar = '█' * progress_bar_width
        print(f"\r[RTMC] OCR Progress: |{bar}| 100% (Page {total_pages}/{total_pages})", end="")
        print()  # New line after the progress bar

        pdf_document.close()
        print(f"[RTMC] OCR processing completed for {pdf_path}")

        # Save the extracted text to a file if requested
        if save_output and text:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"[RTMC] OCR text saved to {output_file}")
    except Exception as e:
        print(f"[RTMC] Error processing PDF with OCR: {e}")
    return text


def text_to_dataframe(text: str) -> List[pd.DataFrame]:
    """
    Convert extracted text to pandas DataFrames.

    This is a simple implementation that tries to identify tables in the text.

    Args:
        text: Extracted text from PDF

    Returns:
        A list of pandas DataFrames
    """
    tables = []
    try:
        # Split text by page
        pages = text.split("--- Page ")

        for page in pages:
            if not page.strip():
                continue

            # Try to identify tables in the text
            lines = page.strip().split('\n')
            if len(lines) < 3:  # Need at least header and some data
                continue

            # Simple heuristic: look for lines with multiple columns (separated by spaces)
            data = []
            for line in lines:
                # Skip lines that are too short or don't have enough columns
                if len(line.strip()) < 10 or line.count(' ') < 2:
                    continue

                # Split by multiple spaces to get columns
                columns = [col.strip() for col in re.split(r'\s{2,}', line.strip())]
                if len(columns) >= 2:  # Need at least 2 columns
                    data.append(columns)

            if len(data) >= 2:  # Need at least header and some data
                # Use the first row as header
                header = data[0]
                # Ensure all rows have the same number of columns
                max_cols = max(len(row) for row in data)
                for i in range(len(data)):
                    while len(data[i]) < max_cols:
                        data[i].append('')

                # Create DataFrame
                df = pd.DataFrame(data[1:], columns=header)
                tables.append(df)
    except Exception as e:
        print(f"[RTMC] Error converting text to DataFrame: {e}")

    return tables


def extract_tables_from_pdf(pdf_path: str) -> List[pd.DataFrame]:
    """
    Extract tables from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        A list of pandas DataFrames containing the extracted tables
    """
    try:
        # First try to extract tables using tabula
        tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
        if tables and len(tables) > 0:
            print(f"[RTMC] Extracted {len(tables)} tables from {pdf_path} using tabula")
            return tables
        else:
            print(f"[RTMC] No tables found in {pdf_path} using tabula, trying OCR...")
            # If tabula fails, try OCR
            text = pdf_to_text_ocr(pdf_path)
            if text:
                # Convert extracted text to DataFrames
                tables = text_to_dataframe(text)
                print(f"[RTMC] Extracted {len(tables)} tables from {pdf_path} using OCR")
                return tables
            else:
                print(f"[RTMC] Failed to extract text from {pdf_path} using OCR")
                return []
    except Exception as e:
        print(f"[RTMC] Error extracting tables from {pdf_path}: {e}")
        # Try OCR as a fallback
        try:
            print(f"[RTMC] Trying OCR as fallback for {pdf_path}...")
            text = pdf_to_text_ocr(pdf_path)
            if text:
                tables = text_to_dataframe(text)
                print(f"[RTMC] Extracted {len(tables)} tables from {pdf_path} using OCR fallback")
                return tables
        except Exception as ocr_e:
            print(f"[RTMC] OCR fallback also failed for {pdf_path}: {ocr_e}")
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
    total_pdfs = len(pdf_files)
    processed_pdfs = 0
    failed_pdfs = 0
    progress_bar_width = 50  # Width of the progress bar

    print(f"[RTMC] Starting to process {total_pdfs} PDF files")

    for i, pdf_path in enumerate(pdf_files, 1):
        # Show overall processing progress
        progress = int(100 * (i-1) / total_pdfs)
        filled_length = int(progress_bar_width * (i-1) // total_pdfs)
        bar = '█' * filled_length + '░' * (progress_bar_width - filled_length)
        print(f"\r[RTMC] PDF Processing Progress: |{bar}| {progress}% ({i-1}/{total_pdfs} files)", end="")
        print()  # New line after the progress bar

        try:
            print(f"[RTMC] Processing PDF {i}/{total_pdfs}: {os.path.basename(pdf_path)}")

            # Extract year from PDF
            year = None
            try:
                year = extract_year_from_pdf(pdf_path)
                if not year:
                    # Try to extract year from filename as fallback
                    filename = os.path.basename(pdf_path)
                    year_match = re.search(r'20\d{2}', filename)
                    if year_match:
                        year = int(year_match.group(0))
                    else:
                        # Use current year as last resort
                        import datetime
                        year = datetime.datetime.now().year
                        print(f"[RTMC] Using current year ({year}) as fallback for {pdf_path}")
            except Exception as e:
                print(f"[RTMC] Error extracting year from {pdf_path}: {e}")
                # Use current year as fallback
                import datetime
                year = datetime.datetime.now().year
                print(f"[RTMC] Using current year ({year}) as fallback for {pdf_path}")

            # Extract tables from PDF
            tables = []
            try:
                tables = extract_tables_from_pdf(pdf_path)
                if not tables:
                    print(f"[RTMC] No tables found in {pdf_path}, will try direct OCR")
                    # Try direct OCR as a last resort
                    text = pdf_to_text_ocr(pdf_path)
                    if text:
                        # Try to extract data directly from text
                        # This is a simple implementation that looks for patterns like "Province: X, Accidents: Y"
                        provinces = ["Eastern Cape", "Free State", "Gauteng", "KwaZulu-Natal", 
                                    "Limpopo", "Mpumalanga", "North West", "Northern Cape", "Western Cape"]
                        for province in provinces:
                            # Look for the province name followed by a number
                            pattern = f"{province}[\\s\\S]{{1,50}}?(\\d+)"
                            match = re.search(pattern, text, re.IGNORECASE)
                            if match:
                                try:
                                    accident_count = int(match.group(1))
                                    record = AccidentRecord(province, accident_count, year, source_name)
                                    records.append(record)
                                    print(f"[RTMC] Extracted record for {province} from text: {accident_count} accidents")
                                except (ValueError, IndexError):
                                    pass
            except Exception as e:
                print(f"[RTMC] Error extracting tables from {pdf_path}: {e}")

            # Extract accident data from tables
            if tables:
                try:
                    pdf_records = extract_accident_data_from_tables(tables, year, source_name)
                    if pdf_records:
                        records.extend(pdf_records)
                        print(f"[RTMC] Extracted {len(pdf_records)} records from {pdf_path}")
                    else:
                        print(f"[RTMC] No accident data found in tables from {pdf_path}")
                except Exception as e:
                    print(f"[RTMC] Error extracting accident data from tables in {pdf_path}: {e}")

            processed_pdfs += 1
            print(f"[RTMC] Progress: {processed_pdfs}/{total_pdfs} PDFs processed")

        except Exception as e:
            print(f"[RTMC] Unexpected error processing {pdf_path}: {e}")
            failed_pdfs += 1

    # Show final processing progress
    progress_bar_width = 50  # Width of the progress bar
    bar = '█' * progress_bar_width
    print(f"\r[RTMC] PDF Processing Progress: |{bar}| 100% ({total_pdfs}/{total_pdfs} files)", end="")
    print()  # New line after the progress bar

    print(f"[RTMC] PDF processing completed: {processed_pdfs} processed, {failed_pdfs} failed, {len(records)} total records extracted")
    return records
