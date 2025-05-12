"""
PDF Downloader module for the RTMC Scraper.

This module provides functionality for downloading PDF files from the RTMC website.
"""
import os
import requests
from bs4 import BeautifulSoup
from typing import List, Optional


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

        # Make a request to the PDF URL
        print(f"[RTMC] Fetching PDF links from: {pdf_url}")
        response = requests.get(pdf_url, headers=headers)

        if response.status_code != 200:
            print(f"[RTMC] Error: Received status code {response.status_code} from {pdf_url}")
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

        # Download each PDF file
        for pdf_link in pdf_links:
            # Construct the full URL if it's a relative link
            if not pdf_link.startswith('http'):
                if pdf_link.startswith('/'):
                    pdf_link = f"https://www.rtmc.co.za{pdf_link}"
                else:
                    pdf_link = f"{pdf_url}/{pdf_link}"

            # Extract the filename from the URL
            filename = os.path.basename(pdf_link)
            local_path = os.path.join(pdf_dir, filename)

            # Download the PDF file
            print(f"[RTMC] Downloading {pdf_link} to {local_path}")
            pdf_response = requests.get(pdf_link, headers=headers)

            if pdf_response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(pdf_response.content)
                downloaded_pdfs.append(local_path)
                print(f"[RTMC] Successfully downloaded {filename}")
            else:
                print(f"[RTMC] Error downloading {pdf_link}: Status code {pdf_response.status_code}")

        print(f"[RTMC] Successfully downloaded {len(downloaded_pdfs)} PDF files")
        print(f"[RTMC] Exact scraping location: {pdf_url}")

        return downloaded_pdfs

    except Exception as e:
        print(f"[RTMC] Error downloading PDFs from {pdf_url}: {e}")
        return []