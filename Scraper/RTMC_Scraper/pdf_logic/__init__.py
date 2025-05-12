"""
PDF Logic module for the RTMC Scraper.

This module provides functionality for downloading and extracting data from PDF files.
"""
from .downloader import download_pdfs
from .pdf_reader import extract_year_from_pdf, extract_tables_from_pdf, extract_accident_data_from_tables, process_pdf_files

__all__ = [
    'download_pdfs',
    'extract_year_from_pdf',
    'extract_tables_from_pdf',
    'extract_accident_data_from_tables',
    'process_pdf_files',
]