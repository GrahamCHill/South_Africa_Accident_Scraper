import pytest
from unittest.mock import patch, MagicMock
import os
import tempfile
import sys
import pandas as pd
from Scraper import BaseScraper, ArriveAliveScraper, StatsSAScraper, DOTScraper, RTMCScraper
import main

class TestMain:
    """
    Tests for the main module.
    """
    
    @patch('main.run_scraper')
    def test_run_all_scrapers(self, mock_run_scraper):
        """Test running all scrapers."""
        # Set up the mock to return a different path for each scraper
        mock_run_scraper.side_effect = [
            "output/arrivealive.csv",
            "output/statssa.csv",
            "output/dot.csv",
            "output/rtmc.csv"
        ]
        
        # Run all scrapers
        csv_paths = main.run_all_scrapers()
        
        # Check that run_scraper was called for each scraper
        assert mock_run_scraper.call_count == 4
        
        # Check that the correct paths were returned
        assert csv_paths == [
            "output/arrivealive.csv",
            "output/statssa.csv",
            "output/dot.csv",
            "output/rtmc.csv"
        ]
    
    @patch('builtins.print')
    def test_run_scraper(self, mock_print):
        """Test running a single scraper."""
        # Create a mock scraper
        mock_scraper = MagicMock(spec=BaseScraper)
        mock_scraper.source_name = "MOCK"
        mock_scraper.export_to_csv.return_value = "output/mock.csv"
        
        # Run the scraper
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = main.run_scraper(mock_scraper, temp_dir)
        
        # Check that the scraper methods were called
        mock_scraper.fetch_data.assert_called_once()
        mock_scraper.parse_data.assert_called_once()
        mock_scraper.export_to_csv.assert_called_once()
        
        # Check that the correct path was returned
        assert csv_path == "output/mock.csv"
        
        # Check that the correct messages were printed
        mock_print.assert_any_call("Running MOCK scraper...")
        mock_print.assert_any_call("Fetching data...")
        mock_print.assert_any_call("Parsing data...")
        mock_print.assert_any_call("Exporting to CSV...")
        mock_print.assert_any_call("Data exported to output/mock.csv")
    
    def test_get_next_available_filename(self):
        """Test getting the next available filename."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test when file doesn't exist
            base_path = os.path.join(temp_dir, "test.csv")
            assert main.get_next_available_filename(base_path) == base_path
            
            # Create the file and test again
            with open(base_path, 'w') as f:
                f.write("test")
            
            # Now it should return test_1.csv
            assert main.get_next_available_filename(base_path) == os.path.join(temp_dir, "test_1.csv")
            
            # Create test_1.csv and test again
            with open(os.path.join(temp_dir, "test_1.csv"), 'w') as f:
                f.write("test")
                
            # Now it should return test_2.csv
            assert main.get_next_available_filename(base_path) == os.path.join(temp_dir, "test_2.csv")
    
    @patch('pandas.read_csv')
    @patch('pandas.DataFrame.to_csv')
    def test_merge_csv_files(self, mock_to_csv, mock_read_csv):
        """Test merging CSV files."""
        # Create mock DataFrames
        df1 = pd.DataFrame({
            "Region": ["Western Cape", "Gauteng"],
            "AccidentCount": [100, 200],
            "Year": [2020, 2020],
            "RunningTotal": [100, 200],
            "Source": ["ARRIVEALIVE", "ARRIVEALIVE"]
        })
        df2 = pd.DataFrame({
            "Region": ["Western Cape", "Gauteng"],
            "AccidentCount": [150, 250],
            "Year": [2020, 2020],
            "RunningTotal": [150, 250],
            "Source": ["STATSSA", "STATSSA"]
        })
        
        # Set up the mock to return the DataFrames
        mock_read_csv.side_effect = [df1, df2]
        
        # Merge the CSV files
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "merged.csv")
            csv_path = main.merge_csv_files(["file1.csv", "file2.csv"], output_file)
        
        # Check that read_csv was called for each file
        assert mock_read_csv.call_count == 2
        
        # Check that to_csv was called once
        mock_to_csv.assert_called_once()
        
        # Check that the correct path was returned
        assert csv_path == output_file
    
    @patch('main.run_all_scrapers')
    @patch('main.run_scraper')
    @patch('main.merge_csv_files')
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_all_sources(self, mock_parse_args, mock_merge_csv_files, mock_run_scraper, mock_run_all_scrapers):
        """Test the main function with all sources."""
        # Set up the mock to return args with source="all"
        mock_args = MagicMock()
        mock_args.source = "all"
        mock_args.output_dir = "output"
        mock_args.merge = True
        mock_parse_args.return_value = mock_args
        
        # Set up the mock to return a list of CSV paths
        mock_run_all_scrapers.return_value = [
            "output/arrivealive.csv",
            "output/statssa.csv",
            "output/dot.csv",
            "output/rtmc.csv"
        ]
        
        # Set up the mock to return a merged CSV path
        mock_merge_csv_files.return_value = "output/accidents_south_africa.csv"
        
        # Run the main function
        main.main()
        
        # Check that run_all_scrapers was called
        mock_run_all_scrapers.assert_called_once_with("output")
        
        # Check that run_scraper was not called
        mock_run_scraper.assert_not_called()
        
        # Check that merge_csv_files was called
        mock_merge_csv_files.assert_called_once()
    
    @patch('main.run_all_scrapers')
    @patch('main.run_scraper')
    @patch('main.merge_csv_files')
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_specific_source(self, mock_parse_args, mock_merge_csv_files, mock_run_scraper, mock_run_all_scrapers):
        """Test the main function with a specific source."""
        # Set up the mock to return args with source="arrivealive"
        mock_args = MagicMock()
        mock_args.source = "arrivealive"
        mock_args.output_dir = "output"
        mock_args.merge = False
        mock_parse_args.return_value = mock_args
        
        # Set up the mock to return a CSV path
        mock_run_scraper.return_value = "output/arrivealive.csv"
        
        # Run the main function
        main.main()
        
        # Check that run_all_scrapers was not called
        mock_run_all_scrapers.assert_not_called()
        
        # Check that run_scraper was called with an ArriveAliveScraper
        mock_run_scraper.assert_called_once()
        scraper_arg = mock_run_scraper.call_args[0][0]
        assert isinstance(scraper_arg, ArriveAliveScraper)
        
        # Check that merge_csv_files was not called
        mock_merge_csv_files.assert_not_called()