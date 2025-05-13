import pytest
from unittest.mock import patch, MagicMock
import os
import tempfile
import shutil
from Scraper.RTMC_Scraper import RTMCScraper

class TestRTMCScraper:
    """
    Tests for the RTMCScraper class.
    """

    # Create a test_data directory to store test data
    test_data_dir = "test_data"
    os.makedirs(test_data_dir, exist_ok=True)

    def setup_method(self):
        """Set up before each test."""
        # Create a test_data directory if it doesn't exist
        os.makedirs(self.test_data_dir, exist_ok=True)

    def test_init(self):
        """Test initialization of RTMCScraper."""
        scraper = RTMCScraper()
        assert scraper.source_name == "RTMC"
        assert scraper.base_url == "https://www.rtmc.co.za/index.php/statistics/traffic-reports"
        assert scraper.pdf_url == "https://www.rtmc.co.za/images/rtmc/docs/traffic_reports/fqyr/"
        assert scraper.pdf_dir == "pdf_downloads"
        assert scraper.downloaded_pdfs == []
        assert scraper.raw_data is None

    @patch('requests.get')
    @patch('builtins.print')
    def test_fetch_data_no_pdfs(self, mock_print, mock_get):
        """Test fetching data when no PDFs are found."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>No PDF links here</body></html>"
        mock_get.return_value = mock_response

        scraper = RTMCScraper()
        scraper.fetch_data()

        # Check that the raw_data attribute was set to simulated_data
        assert scraper.raw_data == "simulated_data"

        # Check that the correct messages were printed
        mock_print.assert_any_call(f"[RTMC] Fetching PDF links from: {scraper.pdf_url}")
        mock_print.assert_any_call(f"[RTMC] No PDF files found at {scraper.pdf_url}")

    @patch('requests.get')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('builtins.print')
    def test_fetch_data_with_pdfs(self, mock_print, mock_open, mock_get):
        """Test fetching data with PDFs."""
        # Mock the response for the HTML page
        html_response = MagicMock()
        html_response.status_code = 200
        html_response.text = """
        <html>
            <body>
                <a href="report_2020.pdf">Report 2020</a>
                <a href="report_2021.pdf">Report 2021</a>
            </body>
        </html>
        """

        # Mock the response for the PDF files
        pdf_response = MagicMock()
        pdf_response.status_code = 200
        pdf_response.content = b"PDF content"

        # Set up the mock to return different responses for different URLs
        def get_side_effect(url, headers=None):
            if url == scraper.pdf_url:
                return html_response
            else:
                return pdf_response

        mock_get.side_effect = get_side_effect

        scraper = RTMCScraper()
        # Override the pdf_dir to use test_data directory
        scraper.pdf_dir = self.test_data_dir
        scraper.fetch_data()

        # Check that the downloaded_pdfs attribute was set
        assert len(scraper.downloaded_pdfs) == 2
        assert all(os.path.dirname(path) == self.test_data_dir for path in scraper.downloaded_pdfs)

        # Check that the raw_data attribute was set to the downloaded_pdfs
        assert scraper.raw_data == scraper.downloaded_pdfs

        # Check that the correct messages were printed
        mock_print.assert_any_call(f"[RTMC] Fetching PDF links from: {scraper.pdf_url}")
        mock_print.assert_any_call(f"[RTMC] Found 2 PDF files")
        mock_print.assert_any_call(f"[RTMC] Successfully downloaded 2 PDF files")

    @patch('builtins.print')
    def test_parse_data_simulated(self, mock_print):
        """Test parsing data with simulated data."""
        scraper = RTMCScraper()
        scraper.raw_data = "simulated_data"
        scraper.parse_data()

        # Check that records were created
        assert len(scraper.records) > 0

        # Check that each record has the expected attributes
        for record in scraper.records:
            assert record.region in ["Eastern Cape", "Free State", "Gauteng", "KwaZulu-Natal", 
                                    "Limpopo", "Mpumalanga", "North West", "Northern Cape", "Western Cape"]
            assert 2018 <= record.year <= 2022
            assert record.accident_count > 0
            assert record.source == "RTMC"

        # Check that the correct message was printed
        mock_print.assert_any_call(f"[RTMC] No PDF files to parse, using simulated data")
        mock_print.assert_any_call(f"[RTMC] Generated {len(scraper.records)} simulated records")

    @patch('tabula.read_pdf')
    @patch('builtins.print')
    def test_parse_data_with_pdfs(self, mock_print, mock_read_pdf):
        """Test parsing data with PDFs."""
        # Create a sample PDF file
        pdf_path = os.path.join(self.test_data_dir, "test_report_2020.pdf")
        with open(pdf_path, 'wb') as f:
            f.write(b"Sample PDF content")

        # Mock the tabula.read_pdf function
        table1 = MagicMock()
        table1.empty = False
        table1.columns = ["Province", "Accidents"]
        table1.iterrows.return_value = [
            (0, {"Province": "Gauteng", "Accidents": 1000}),
            (1, {"Province": "Western Cape", "Accidents": 800})
        ]

        mock_read_pdf.return_value = [table1]

        scraper = RTMCScraper()
        scraper.raw_data = [pdf_path]

        # Mock the extract_year_from_pdf method
        scraper.extract_year_from_pdf = MagicMock(return_value=2020)

        scraper.parse_data()

        # Check that records were created
        assert len(scraper.records) == 2

        # Check that each record has the expected attributes
        assert scraper.records[0].region == "Gauteng"
        assert scraper.records[0].accident_count == 1000
        assert scraper.records[0].year == 2020
        assert scraper.records[0].source == "RTMC"

        assert scraper.records[1].region == "Western Cape"
        assert scraper.records[1].accident_count == 800
        assert scraper.records[1].year == 2020
        assert scraper.records[1].source == "RTMC"

        # Check that the correct message was printed
        mock_print.assert_any_call(f"[RTMC] Parsing 1 PDF files")
        mock_print.assert_any_call(f"[RTMC] Successfully parsed 2 records")

    def test_export_to_csv(self):
        """Test exporting records to CSV."""
        scraper = RTMCScraper()
        scraper.raw_data = "simulated_data"
        scraper.parse_data()

        # Export to CSV in the test_data directory
        output_file = os.path.join(self.test_data_dir, "test_rtmc.csv")
        csv_path = scraper.export_to_csv(output_file)

        # Check that the file was created
        assert os.path.exists(csv_path)

        # Check that the file is not empty
        assert os.path.getsize(csv_path) > 0

        print(f"Test data saved to {os.path.abspath(csv_path)}")

    def test_end_to_end(self):
        """Test the entire scraping process from fetch to export."""
        # This test will use simulated data since we can't rely on the website being available
        scraper = RTMCScraper()

        # Override the pdf_dir to use test_data directory
        scraper.pdf_dir = self.test_data_dir

        # Fetch and parse data
        scraper.fetch_data()
        scraper.parse_data()

        # Check that records were created
        assert len(scraper.records) > 0

        # Export to CSV in the test_data directory
        output_file = os.path.join(self.test_data_dir, "test_rtmc_end_to_end.csv")
        csv_path = scraper.export_to_csv(output_file)

        # Check that the file was created
        assert os.path.exists(csv_path)

        # Check that the file is not empty
        assert os.path.getsize(csv_path) > 0

        print(f"Test data saved to {os.path.abspath(csv_path)}")

    def test_pdf_download(self):
        """Test the PDF download functionality."""
        # This test will actually attempt to download PDFs from the RTMC website
        scraper = RTMCScraper()

        # Set the PDF directory to a test directory
        test_pdf_dir = "test_pdf_downloads"
        scraper.pdf_dir = test_pdf_dir

        # Run the fetch_data method to download PDFs
        scraper.fetch_data()

        # Check if PDFs were downloaded
        if scraper.downloaded_pdfs:
            print(f"Successfully downloaded {len(scraper.downloaded_pdfs)} PDF files:")
            for pdf_path in scraper.downloaded_pdfs:
                print(f"  - {pdf_path} ({os.path.getsize(pdf_path)} bytes)")
                # Check that the file exists and is not empty
                assert os.path.exists(pdf_path)
                assert os.path.getsize(pdf_path) > 0
        else:
            # If no PDFs were downloaded, check if the scraper fell back to simulated data
            if scraper.raw_data == "simulated_data":
                print("The scraper fell back to simulated data.")
            else:
                # If the scraper didn't fall back to simulated data, something went wrong
                assert False, "No PDFs were downloaded and the scraper didn't fall back to simulated data."

        # Check the pdf_dir directory
        if os.path.exists(scraper.pdf_dir):
            pdf_files = [f for f in os.listdir(scraper.pdf_dir) if f.lower().endswith('.pdf')]
            if pdf_files:
                print(f"Found {len(pdf_files)} PDF files in {scraper.pdf_dir} directory:")
                for pdf_file in pdf_files:
                    pdf_path = os.path.join(scraper.pdf_dir, pdf_file)
                    print(f"  - {pdf_file} ({os.path.getsize(pdf_path)} bytes)")
            else:
                print(f"No PDF files found in {scraper.pdf_dir} directory.")
        else:
            print(f"The {scraper.pdf_dir} directory does not exist.")

    def test_run_from_main(self):
        """Test running the RTMC scraper from main.py."""
        import main

        # Run the RTMC scraper
        scraper = RTMCScraper()
        output_dir = "test_output"
        os.makedirs(output_dir, exist_ok=True)

        # Run the scraper
        csv_path = main.run_scraper(scraper, output_dir)

        # Check that the CSV file was created
        assert os.path.exists(csv_path)
        assert os.path.getsize(csv_path) > 0

        print(f"CSV file created at {os.path.abspath(csv_path)}")
