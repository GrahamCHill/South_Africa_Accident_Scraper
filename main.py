"""
Main entry point for the South African Accident Data Scraper.

This script orchestrates the scraping process by:
1. Importing all the scrapers
2. Creating instances of each scraper
3. Fetching and parsing data from each source
4. Exporting the data to CSV files
"""
import os
import argparse
import time
import inspect
import sys
from typing import List, Dict, Any, Type, Tuple
from pathlib import Path

# Import scrapers
from Scraper import BaseScraper, AccidentRecord

# Get the directory of the script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def discover_scrapers() -> Dict[str, Type[BaseScraper]]:
    """
    Dynamically discover all scraper classes from the Scraper package.

    Returns:
        A dictionary mapping lowercase source names to scraper classes
    """
    import Scraper

    # Get all classes from the Scraper package
    scraper_classes = {}
    for name in Scraper.__all__:
        obj = getattr(Scraper, name)
        # Check if it's a class and a subclass of BaseScraper, but not BaseScraper itself
        if inspect.isclass(obj) and issubclass(obj, BaseScraper) and obj != BaseScraper:
            # Use lowercase source name as the key
            scraper_classes[obj().source_name.lower()] = obj

    return scraper_classes


def run_scraper(scraper: BaseScraper, output_dir: str = "output") -> str:
    """
    Run a scraper and export the data to a CSV file.

    Args:
        scraper: The scraper to run
        output_dir: The directory to save the output file

    Returns:
        The path to the created CSV file
    """
    print(f"Running {scraper.source_name} scraper...")

    # Fetch data
    print("Fetching data...")
    scraper.fetch_data()

    # Parse data
    print("Parsing data...")
    scraper.parse_data()

    # Export to CSV
    print("Exporting to CSV...")
    # Ensure output_dir is an absolute path relative to the script directory
    abs_output_dir = os.path.join(SCRIPT_DIR, output_dir)
    os.makedirs(abs_output_dir, exist_ok=True)
    # Let the scraper use its default output file name but specify the output directory
    csv_path = scraper.export_to_csv(output_dir=abs_output_dir)

    # Convert to absolute path for clearer user feedback
    abs_path = os.path.abspath(csv_path)
    print(f"Data exported to {abs_path}")
    return csv_path


def run_all_scrapers(output_dir: str = "output") -> List[str]:
    """
    Run all scrapers and export the data to CSV files.

    Args:
        output_dir: The directory to save the output files

    Returns:
        A list of paths to the created CSV files
    """
    # Discover all scraper classes
    scraper_classes = discover_scrapers()

    # Create instances of each scraper
    scrapers = [cls() for cls in scraper_classes.values()]

    print(f"Found {len(scrapers)} scrapers: {', '.join(scraper.source_name for scraper in scrapers)}")

    # Run each scraper
    csv_paths = []
    for scraper in scrapers:
        try:
            csv_path = run_scraper(scraper, output_dir)
            csv_paths.append(csv_path)
        except Exception as e:
            print(f"Error running {scraper.source_name} scraper: {e}")

    return csv_paths


def get_next_available_filename(base_path: str) -> str:
    """
    Get the next available filename by appending a number if the file already exists.

    Args:
        base_path: The base path without the number suffix

    Returns:
        The next available filename
    """
    if not os.path.exists(base_path):
        return base_path

    base_name, ext = os.path.splitext(base_path)
    counter = 1
    while os.path.exists(f"{base_name}_{counter}{ext}"):
        counter += 1

    return f"{base_name}_{counter}{ext}"

def merge_csv_files(csv_paths: List[str] = None, output_file: str = None, output_dir: str = None) -> str:
    """
    Merge multiple CSV files into a single file.

    Args:
        csv_paths: A list of paths to the CSV files to merge. If None, all CSV files in the output_dir will be merged.
        output_file: The path to the output file. If None, a default name will be used.
        output_dir: The directory to look for CSV files if csv_paths is None. If None, the default output directory will be used.

    Returns:
        The path to the merged CSV file
    """
    import pandas as pd
    import glob

    # If output_dir is not provided, use the default output directory
    if output_dir is None:
        output_dir = os.path.join(SCRIPT_DIR, "output")
        os.makedirs(output_dir, exist_ok=True)

    # If csv_paths is not provided, find all CSV files in the output directory
    if csv_paths is None:
        csv_pattern = os.path.join(output_dir, "*.csv")
        csv_paths = glob.glob(csv_pattern)
        # Exclude any files that start with "accidents_south_africa" to avoid merging already merged files
        csv_paths = [path for path in csv_paths if not os.path.basename(path).startswith("accidents_south_africa")]

    if not csv_paths:
        print("No CSV files found to merge.")
        return None

    print("\nMerging CSV files...")
    print(f"Number of files to merge: {len(csv_paths)}")
    print(f"Files to merge: {', '.join(os.path.basename(path) for path in csv_paths)}")

    # Read all CSV files
    dfs = []
    for csv_path in csv_paths:
        try:
            df = pd.read_csv(csv_path)
            dfs.append(df)
        except Exception as e:
            print(f"Error reading {csv_path}: {e}")

    if not dfs:
        print("No valid CSV files found to merge.")
        return None

    # Concatenate all dataframes
    merged_df = pd.concat(dfs, ignore_index=True)

    # Remove duplicates based on Region, Year, and Source
    merged_df = merged_df.drop_duplicates(subset=["Region", "Year", "Source"])

    # Generate default output file name if not provided
    if output_file is None:
        # Ensure output_dir is an absolute path relative to the script directory
        output_dir = os.path.join(SCRIPT_DIR, "output")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "accidents_south_africa.csv")
        output_file = get_next_available_filename(output_file)
    else:
        # If output_file is provided, ensure its directory exists
        output_dir = os.path.dirname(output_file)
        if not os.path.isabs(output_dir):
            # If output_dir is not an absolute path, make it relative to the script directory
            output_dir = os.path.join(SCRIPT_DIR, output_dir)
            output_file = os.path.join(output_dir, os.path.basename(output_file))
        os.makedirs(output_dir, exist_ok=True)

    # Write to CSV
    merged_df.to_csv(output_file, index=False)

    return output_file


def main():
    """
    Main entry point.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="South African Accident Data Scraper")

    # Discover all scraper classes
    scraper_classes = discover_scrapers()

    # Add "all" to the choices
    choices = ["all"] + list(scraper_classes.keys())

    parser.add_argument("--source", choices=choices,
                        # Change default to all when other scrapers are active
                        default="rtmc",help="The data source to scrape")
    parser.add_argument("--output-dir", default="output", help="The directory to save the output files")
    args = parser.parse_args()

    # Ensure output_dir is an absolute path relative to the script directory
    abs_output_dir = args.output_dir
    if not os.path.isabs(abs_output_dir):
        abs_output_dir = os.path.join(SCRIPT_DIR, args.output_dir)

    # Create output directory
    os.makedirs(abs_output_dir, exist_ok=True)

    # Run scrapers based on the source argument
    csv_paths = []
    if args.source == "all":
        csv_paths = run_all_scrapers(abs_output_dir)
    else:
        # Create the appropriate scraper based on the source argument
        scraper_class = scraper_classes.get(args.source)
        if scraper_class:
            scraper = scraper_class()
            csv_path = run_scraper(scraper, abs_output_dir)
            csv_paths.append(csv_path)
        else:
            print(f"Error: Unknown source '{args.source}'. Available sources: {', '.join(scraper_classes.keys())}")

    # Always merge CSV files, either from the current run or all files in the output directory
    if len(csv_paths) > 0:
        # If we have CSV paths from the current run, merge those
        merged_file = merge_csv_files(csv_paths, os.path.join(abs_output_dir, "accidents_south_africa.csv"))
    else:
        # Otherwise, merge all CSV files in the output directory
        merged_file = merge_csv_files(output_dir=abs_output_dir)

    if merged_file:
        abs_merged_file = os.path.abspath(merged_file)
        print(f"All data merged into {abs_merged_file}")

    # Print a summary of where to find the output files
    print("\nSUMMARY:")
    print(f"All output files are located in: {abs_output_dir}")
    print(f"You can find your CSV files at this location on your computer.")


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"Scraping completed in {end_time - start_time:.2f} seconds")
