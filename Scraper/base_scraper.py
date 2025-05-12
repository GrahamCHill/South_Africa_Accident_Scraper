"""
Base Scraper module that defines the common interface for all scrapers.
"""
from abc import ABC, abstractmethod
import csv
from typing import List, Dict, Any
import os
from datetime import datetime


class AccidentRecord:
    """
    Data model for accident records.
    """
    def __init__(self, region: str, accident_count: int, year: int, source: str):
        self.region = region
        self.accident_count = accident_count
        self.year = year
        self.source = source
        self.running_total = 0  # Will be calculated later

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the record to a dictionary.
        """
        return {
            "Region": self.region,
            "AccidentCount": self.accident_count,
            "Year": self.year,
            "RunningTotal": self.running_total,
            "Source": self.source
        }


class BaseScraper(ABC):
    """
    Base class for all scrapers.
    """
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.records: List[AccidentRecord] = []

    @abstractmethod
    def fetch_data(self) -> None:
        """
        Fetch data from the source.
        This method should be implemented by each concrete scraper.
        """
        pass

    @abstractmethod
    def parse_data(self) -> None:
        """
        Parse the fetched data and convert it to AccidentRecord objects.
        This method should be implemented by each concrete scraper.
        """
        pass

    def calculate_running_totals(self) -> None:
        """
        Calculate running totals for each region and year.
        """
        # Group records by region
        region_records = {}
        for record in self.records:
            if record.region not in region_records:
                region_records[record.region] = []
            region_records[record.region].append(record)

        # Sort records by year for each region and calculate running totals
        for region, records in region_records.items():
            records.sort(key=lambda x: x.year)
            running_total = 0
            for record in records:
                running_total += record.accident_count
                record.running_total = running_total

    def get_next_available_filename(self, base_path: str) -> str:
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

    def export_to_csv(self, output_file: str = None, output_dir: str = "output") -> str:
        """
        Export the records to a CSV file.

        Args:
            output_file: The path to the output file. If None, a default name will be used.
            output_dir: The directory to save the output file. Default is "output".

        Returns:
            The path to the created CSV file.
        """
        if not self.records:
            raise ValueError("No records to export. Make sure to fetch and parse data first.")

        # Calculate running totals
        self.calculate_running_totals()

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Generate default output file name if not provided
        if output_file is None:
            output_file = os.path.join(output_dir, "accidents_south_africa.csv")
            output_file = self.get_next_available_filename(output_file)

        # Write records to CSV
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ["Region", "AccidentCount", "Year", "RunningTotal", "Source"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for record in self.records:
                writer.writerow(record.to_dict())

        return output_file
