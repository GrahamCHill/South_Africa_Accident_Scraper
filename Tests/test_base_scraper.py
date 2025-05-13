import os
import pytest
from unittest.mock import patch, MagicMock
import tempfile
import csv
from Scraper.base_scraper import BaseScraper, AccidentRecord

class TestBaseScraper:
    """
    Tests for the BaseScraper class.
    """
    
    class MockScraper(BaseScraper):
        """
        Mock implementation of BaseScraper for testing.
        """
        def __init__(self):
            super().__init__("MOCK")
            self.base_url = "https://example.com/mock"
        
        def fetch_data(self):
            """Mock implementation of fetch_data."""
            self.records = []
            
        def parse_data(self):
            """Mock implementation of parse_data."""
            # Add some test records
            regions = ["Western Cape", "Gauteng", "KwaZulu-Natal"]
            for region in regions:
                for year in range(2018, 2023):
                    record = AccidentRecord(region, 100 * year, year, self.source_name)
                    self.records.append(record)
    
    def test_init(self):
        """Test initialization of BaseScraper."""
        scraper = self.MockScraper()
        assert scraper.source_name == "MOCK"
        assert scraper.records == []
        
    def test_calculate_running_totals(self):
        """Test calculation of running totals."""
        scraper = self.MockScraper()
        scraper.parse_data()  # Add some test records
        
        # Before calculation, all running totals should be 0
        for record in scraper.records:
            assert record.running_total == 0
            
        # Calculate running totals
        scraper.calculate_running_totals()
        
        # Check running totals for Western Cape
        wc_records = [r for r in scraper.records if r.region == "Western Cape"]
        wc_records.sort(key=lambda x: x.year)
        
        expected_total = 0
        for i, record in enumerate(wc_records):
            expected_total += record.accident_count
            assert record.running_total == expected_total
            
    def test_get_next_available_filename(self):
        """Test getting the next available filename."""
        scraper = self.MockScraper()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test when file doesn't exist
            base_path = os.path.join(temp_dir, "test.csv")
            assert scraper.get_next_available_filename(base_path) == base_path
            
            # Create the file and test again
            with open(base_path, 'w') as f:
                f.write("test")
            
            # Now it should return test_1.csv
            assert scraper.get_next_available_filename(base_path) == os.path.join(temp_dir, "test_1.csv")
            
            # Create test_1.csv and test again
            with open(os.path.join(temp_dir, "test_1.csv"), 'w') as f:
                f.write("test")
                
            # Now it should return test_2.csv
            assert scraper.get_next_available_filename(base_path) == os.path.join(temp_dir, "test_2.csv")
    
    def test_export_to_csv(self):
        """Test exporting records to CSV."""
        scraper = self.MockScraper()
        scraper.parse_data()  # Add some test records
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Export to CSV
            output_file = os.path.join(temp_dir, "test_output.csv")
            csv_path = scraper.export_to_csv(output_file)
            
            # Check that the file was created
            assert os.path.exists(csv_path)
            
            # Check the content of the CSV file
            with open(csv_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                
                # Check that we have the expected number of rows
                assert len(rows) == len(scraper.records)
                
                # Check that the headers are correct
                assert set(rows[0].keys()) == {"Region", "AccidentCount", "Year", "RunningTotal", "Source"}
                
                # Check a sample row
                sample_record = scraper.records[0]
                sample_row = rows[0]
                assert sample_row["Region"] == sample_record.region
                assert int(sample_row["AccidentCount"]) == sample_record.accident_count
                assert int(sample_row["Year"]) == sample_record.year
                assert sample_row["Source"] == sample_record.source_name