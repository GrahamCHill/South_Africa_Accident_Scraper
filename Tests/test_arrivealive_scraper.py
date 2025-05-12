import pytest
from unittest.mock import patch, MagicMock
import os
import tempfile
from Scraper.ARRIVEALIVE_Scraper import ArriveAliveScraper

class TestArriveAliveScraper:
    """
    Tests for the ArriveAliveScraper class.
    """

    # Create a test_data directory to store test data
    test_data_dir = "test_data"
    os.makedirs(test_data_dir, exist_ok=True)

    def setup_method(self):
        """Set up before each test."""
        # Create a test_data directory if it doesn't exist
        os.makedirs(self.test_data_dir, exist_ok=True)

    def test_init(self):
        """Test initialization of ArriveAliveScraper."""
        scraper = ArriveAliveScraper()
        assert scraper.source_name == "ARRIVEALIVE"
        assert scraper.base_url == "https://www.arrivealive.co.za/road-safety-statistics"
        assert scraper.raw_data is None
        assert scraper.records == []

    @patch('builtins.print')
    def test_fetch_data(self, mock_print):
        """Test fetching data from the Arrive Alive website."""
        scraper = ArriveAliveScraper()
        scraper.fetch_data()

        # Check that the raw_data attribute was set
        assert scraper.raw_data is not None

        # Check that the correct messages were printed
        mock_print.assert_any_call(f"[ARRIVEALIVE] Successfully fetched data from: {scraper.base_url}")
        mock_print.assert_any_call(f"[ARRIVEALIVE] Exact scraping location: {scraper.base_url}")

    @patch('builtins.print')
    def test_parse_data(self, mock_print):
        """Test parsing data from the Arrive Alive website."""
        scraper = ArriveAliveScraper()
        scraper.fetch_data()
        scraper.parse_data()

        # Check that records were created
        assert len(scraper.records) > 0

        # Check that each record has the expected attributes
        for record in scraper.records:
            assert record.region in ["Western Cape", "Gauteng", "KwaZulu-Natal"]
            assert 2018 <= record.year <= 2022
            assert record.accident_count > 0
            assert record.source == "ARRIVEALIVE"

        # Check that the correct message was printed
        mock_print.assert_any_call(f"[ARRIVEALIVE] Successfully parsed {len(scraper.records)} records")

    def test_export_to_csv(self):
        """Test exporting records to CSV."""
        scraper = ArriveAliveScraper()
        scraper.fetch_data()
        scraper.parse_data()

        # Export to CSV in the test_data directory
        output_file = os.path.join(self.test_data_dir, "test_arrivealive.csv")
        csv_path = scraper.export_to_csv(output_file)

        # Check that the file was created
        assert os.path.exists(csv_path)

        # Check that the file is not empty
        assert os.path.getsize(csv_path) > 0

        print(f"Test data saved to {os.path.abspath(csv_path)}")

    def test_end_to_end(self):
        """Test the entire scraping process from fetch to export."""
        scraper = ArriveAliveScraper()

        # Fetch and parse data
        scraper.fetch_data()
        scraper.parse_data()

        # Check that records were created
        assert len(scraper.records) > 0

        # Export to CSV in the test_data directory
        output_file = os.path.join(self.test_data_dir, "test_arrivealive_end_to_end.csv")
        csv_path = scraper.export_to_csv(output_file)

        # Check that the file was created
        assert os.path.exists(csv_path)

        # Check that the file is not empty
        assert os.path.getsize(csv_path) > 0

        print(f"Test data saved to {os.path.abspath(csv_path)}")
