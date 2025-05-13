"""
PDF Downloader module for the RTMC Scraper.

This module provides functionality for downloading PDF files from the RTMC website.
"""
import os
import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Tuple
import time
import random
from requests.exceptions import RequestException, Timeout, ConnectionError
import PyPDF2
from io import BytesIO


def is_valid_pdf(content: bytes) -> bool:
    """
    Check if the content is a valid PDF file.

    Args:
        content: The content to check

    Returns:
        True if the content is a valid PDF, False otherwise
    """
    try:
        # Try to open the PDF file
        PyPDF2.PdfReader(BytesIO(content))
        return True
    except Exception:
        return False


def download_single_pdf(pdf_url: str, local_path: str, headers: dict, max_retries: int = 3, 
                        timeout: int = 30, backoff_factor: float = 0.5) -> Tuple[bool, str]:
    """
    Download a single PDF file with retries and timeouts.

    Args:
        pdf_url: The URL to download the PDF from
        local_path: The local path to save the PDF to
        headers: The headers to use for the request
        max_retries: The maximum number of retries
        timeout: The timeout in seconds
        backoff_factor: The backoff factor for retries

    Returns:
        A tuple of (success, message)
    """
    for attempt in range(max_retries):
        try:
            # Add jitter to avoid overwhelming the server
            if attempt > 0:
                sleep_time = backoff_factor * (2 ** attempt) + random.uniform(0, 0.1)
                print(f"[RTMC] Retry {attempt}/{max_retries} after {sleep_time:.2f}s for {pdf_url}")
                time.sleep(sleep_time)

            # Stream the download to show progress and handle large files
            with requests.get(pdf_url, headers=headers, stream=True, timeout=timeout) as response:
                if response.status_code != 200:
                    continue  # Try again if not 200

                # Get file size if available
                total_size = int(response.headers.get('content-length', 0))
                if total_size > 0:
                    print(f"[RTMC] Downloading {os.path.basename(local_path)} ({total_size/1024/1024:.2f} MB)")

                # Download with progress tracking
                content = bytearray()
                downloaded = 0
                chunk_size = 8192  # 8KB chunks
                last_progress = 0
                progress_bar_width = 50  # Width of the progress bar in characters

                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        content.extend(chunk)
                        downloaded += len(chunk)

                        # Show detailed progress for every download
                        if total_size > 0:
                            progress = int(100 * downloaded / total_size)
                            # Update progress more frequently (every 2%)
                            if progress >= last_progress + 2 or downloaded == total_size:
                                # Create a visual progress bar
                                filled_length = int(progress_bar_width * downloaded // total_size)
                                bar = '█' * filled_length + '░' * (progress_bar_width - filled_length)

                                print(f"\r[RTMC] Downloading: |{bar}| {progress}% ({downloaded/1024/1024:.2f}/{total_size/1024/1024:.2f} MB)", end="")
                                last_progress = progress

                                # Print a newline when download is complete
                                if downloaded == total_size:
                                    print()

                # Validate the PDF
                if not is_valid_pdf(content):
                    return False, "Invalid PDF content"

                # Save the file
                with open(local_path, 'wb') as f:
                    f.write(content)

                return True, "Success"

        except Timeout:
            print(f"[RTMC] Timeout downloading {pdf_url}")
        except ConnectionError:
            print(f"[RTMC] Connection error downloading {pdf_url}")
        except RequestException as e:
            print(f"[RTMC] Request exception downloading {pdf_url}: {e}")
        except Exception as e:
            print(f"[RTMC] Unexpected error downloading {pdf_url}: {e}")

    return False, f"Failed after {max_retries} attempts"


def download_pdfs(pdf_url: str, pdf_dir: str) -> List[str]:
    """
    Download PDF files from the RTMC website.

    Args:
        pdf_url: The URL to download PDFs from
        pdf_dir: The directory to save downloaded PDFs

    Returns:
        A list of paths to downloaded PDF files, or an empty list if no PDFs were found
    """
    try:
        # Create directory for PDF downloads if it doesn't exist
        os.makedirs(pdf_dir, exist_ok=True)

        # List to store paths to downloaded PDFs
        downloaded_pdfs = []

        # Set up headers for the request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # Make a request to the PDF URL with timeout
        print(f"[RTMC] Fetching PDF links from: {pdf_url}")
        try:
            response = requests.get(pdf_url, headers=headers, timeout=30)
            response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        except (RequestException, Timeout, ConnectionError) as e:
            print(f"[RTMC] Error fetching PDF links: {e}")
            return []

        # Parse the HTML to find links to PDF files
        soup = BeautifulSoup(response.text, 'html.parser')
        pdf_links = []

        # Find all links that end with .pdf
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.lower().endswith('.pdf'):
                pdf_links.append(href)

        if not pdf_links:
            print(f"[RTMC] No PDF files found at {pdf_url}")
            return []

        print(f"[RTMC] Found {len(pdf_links)} PDF files")
        total_pdfs = len(pdf_links)
        successful_downloads = 0

        # Download each PDF file with progress information
        print(f"[RTMC] Starting download of {total_pdfs} PDF files")
        progress_bar_width = 50  # Width of the overall progress bar

        for i, pdf_link in enumerate(pdf_links, 1):
            # Show overall progress
            overall_progress = int(100 * (i-1) / total_pdfs)
            filled_length = int(progress_bar_width * (i-1) // total_pdfs)
            bar = '█' * filled_length + '░' * (progress_bar_width - filled_length)
            print(f"\r[RTMC] Overall progress: |{bar}| {overall_progress}% ({i-1}/{total_pdfs} files)", end="")
            print()  # New line after the progress bar

            # Construct the full URL if it's a relative link
            if not pdf_link.startswith('http'):
                if pdf_link.startswith('/'):
                    pdf_link = f"https://www.rtmc.co.za{pdf_link}"
                else:
                    pdf_link = f"{pdf_url}/{pdf_link}"

            # Extract the filename from the URL
            filename = os.path.basename(pdf_link)
            local_path = os.path.join(pdf_dir, filename)

            # Check if corresponding .txt file exists (indicating OCR has been done)
            txt_path = os.path.splitext(local_path)[0] + "_ocr.txt"
            # We don't skip downloads just because a .txt file exists
            # We only skip if the PDF file itself exists and is valid

            # Check if file already exists and is valid
            if os.path.exists(local_path):
                try:
                    with open(local_path, 'rb') as f:
                        content = f.read()
                    if is_valid_pdf(content):
                        print(f"[RTMC] File {filename} already exists and is valid, skipping download")
                        downloaded_pdfs.append(local_path)
                        successful_downloads += 1
                        continue
                    else:
                        print(f"[RTMC] File {filename} exists but is invalid, re-downloading")
                        # Delete the invalid file
                        os.remove(local_path)
                except Exception as e:
                    print(f"[RTMC] Error checking existing file {filename}: {e}")
                    # Delete the potentially corrupted file
                    if os.path.exists(local_path):
                        os.remove(local_path)

            # Download the PDF file with retries and progress tracking
            print(f"[RTMC] Downloading file {i}/{total_pdfs}: {filename}")
            success, message = download_single_pdf(pdf_link, local_path, headers, max_retries=3, timeout=60, backoff_factor=0.5)

            if success:
                downloaded_pdfs.append(local_path)
                successful_downloads += 1
                print(f"[RTMC] Successfully downloaded {filename} ({successful_downloads}/{total_pdfs})")
            else:
                print(f"[RTMC] Failed to download {filename}: {message}")

            # Add a small delay between downloads to avoid overwhelming the server
            if i < total_pdfs:
                time.sleep(random.uniform(0.5, 2.0))

        # Show final overall progress
        overall_progress = 100
        bar = '█' * progress_bar_width
        print(f"\r[RTMC] Overall progress: |{bar}| {overall_progress}% ({total_pdfs}/{total_pdfs} files)", end="")
        print()  # New line after the progress bar

        print(f"[RTMC] Successfully downloaded {successful_downloads}/{total_pdfs} PDF files")
        print(f"[RTMC] Exact scraping location: {pdf_url}")

        return downloaded_pdfs

    except Exception as e:
        print(f"[RTMC] Error downloading PDFs from {pdf_url}: {e}")
        return []
