"""
Test script to verify that OCR processing is skipped for PDFs with existing .txt files.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Import the necessary modules
from Scraper.RTMC_Scraper.pdf_logic.pdf_reader import pdf_to_text_ocr

def test_ocr_skip():
    """
    Test that OCR processing is skipped for PDFs with existing .txt files.
    """
    # Get a list of PDF files in the pdf_downloads directory
    pdf_dir = os.path.join(script_dir, "pdf_downloads")
    if not os.path.exists(pdf_dir):
        print(f"PDF directory {pdf_dir} does not exist.")
        return
    
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    if not pdf_files:
        print(f"No PDF files found in {pdf_dir}.")
        return
    
    # Take the first PDF file for testing
    test_pdf = os.path.join(pdf_dir, pdf_files[0])
    print(f"Testing with PDF file: {test_pdf}")
    
    # Check if the corresponding .txt file exists
    txt_file = os.path.splitext(test_pdf)[0] + "_ocr.txt"
    txt_exists = os.path.exists(txt_file)
    print(f"Corresponding .txt file exists: {txt_exists}")
    
    if txt_exists:
        # Get the modification time of the .txt file
        txt_mtime = os.path.getmtime(txt_file)
        print(f"Original .txt file modification time: {txt_mtime}")
        
        # Process the PDF file
        print("Processing PDF file...")
        text = pdf_to_text_ocr(test_pdf)
        
        # Check if the .txt file was modified
        new_txt_mtime = os.path.getmtime(txt_file)
        print(f"New .txt file modification time: {new_txt_mtime}")
        
        if new_txt_mtime == txt_mtime:
            print("SUCCESS: OCR processing was skipped for the PDF with existing .txt file.")
        else:
            print("FAILURE: OCR processing was performed despite existing .txt file.")
    else:
        # Process the PDF file to create the .txt file
        print("No existing .txt file found. Processing PDF file to create one...")
        text = pdf_to_text_ocr(test_pdf)
        
        # Check if the .txt file was created
        txt_exists = os.path.exists(txt_file)
        print(f".txt file created: {txt_exists}")
        
        if txt_exists:
            print("SUCCESS: .txt file was created.")
            
            # Process the PDF file again to test skipping
            print("Processing PDF file again to test skipping...")
            text = pdf_to_text_ocr(test_pdf)
            
            # Check if the message about skipping was printed
            print("If you see a message about skipping OCR processing above, the test passed.")
        else:
            print("FAILURE: .txt file was not created.")

if __name__ == "__main__":
    test_ocr_skip()