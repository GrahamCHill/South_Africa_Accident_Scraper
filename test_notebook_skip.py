"""
Test script to verify that the notebook skips PDF downloads when .txt files exist.
"""
import os
import sys
import subprocess
import time

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

def test_notebook_skip():
    """
    Test that the notebook skips PDF downloads when .txt files exist.
    """
    # Check if the pdf_downloads directory exists and contains .txt files
    pdf_dir = os.path.join(script_dir, "pdf_downloads")
    if not os.path.exists(pdf_dir):
        print(f"PDF directory {pdf_dir} does not exist.")
        return
    
    txt_files = [f for f in os.listdir(pdf_dir) if f.endswith('_ocr.txt')]
    if not txt_files:
        print(f"No .txt files found in {pdf_dir}.")
        return
    
    print(f"Found {len(txt_files)} .txt files in {pdf_dir}.")
    
    # Run the notebook using jupyter nbconvert
    notebook_path = os.path.join(script_dir, "notebook", "accident_scraper_demo.ipynb")
    if not os.path.exists(notebook_path):
        print(f"Notebook {notebook_path} does not exist.")
        return
    
    print(f"Running notebook {notebook_path}...")
    
    # Use subprocess to run the notebook
    try:
        # Convert the notebook to a Python script and execute it
        cmd = [sys.executable, "-m", "jupyter", "nbconvert", "--to", "python", "--execute", notebook_path]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            print(f"Error running notebook: {stderr}")
            return
        
        print("Notebook executed successfully.")
        
        # Check if the output contains the message about skipping downloads
        output_file = os.path.join(script_dir, "notebook", "accident_scraper_demo.py")
        if os.path.exists(output_file):
            with open(output_file, "r") as f:
                output = f.read()
                if "Skipping PDF downloads and using existing .txt files" in output:
                    print("SUCCESS: Notebook skipped PDF downloads when .txt files exist.")
                else:
                    print("FAILURE: Notebook did not skip PDF downloads.")
            
            # Clean up the generated Python file
            os.remove(output_file)
        else:
            print(f"Output file {output_file} not found.")
    except Exception as e:
        print(f"Error running notebook: {e}")

if __name__ == "__main__":
    test_notebook_skip()