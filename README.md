# South African Accident Data Scraper

A Python project that scrapes accident data from various South African sources and outputs it to CSV files.

## Overview

This project provides a framework for scraping accident data from multiple South African sources, including:

- Arrive Alive
- Statistics South Africa (StatsSA)
- Department of Transport (DOT)
- Road Traffic Management Corporation (RTMC)
- City of Cape Town
- iTraffic

The scraped data is standardized and exported to CSV files with the following headers:
- Region
- AccidentCount
- Year
- RunningTotal
- Source

By default, the data is exported to a file named `accidents_south_africa.csv` in the `output` directory within the project root. If this file already exists, a number is appended to the filename (e.g., `accidents_south_africa_1.csv`, `accidents_south_africa_2.csv`, etc.).

### Output Files Location

All output files are saved in the `output` directory by default. This directory is created in the project root if it doesn't exist. The absolute path to this directory is displayed in the console when the script finishes running.

For example, if your project is located at `C:\Users\YourName\Projects\improved-accident-scraper`, the output files will be at:
```
C:\Users\YourName\Projects\improved-accident-scraper\output\accidents_south_africa.csv
```

You can specify a different output directory using the `--output-dir` option.

## Installation

### Requirements

- Python 3.13 or higher
- Dependencies listed in pyproject.toml

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/improved-accident-scraper.git
   cd improved-accident-scraper
   ```

2. Install the package and its dependencies:
   ```
   pip install -e .
   ```

## Usage

### Command Line Interface

The project provides a command-line interface for running the scrapers:

```
python main.py [--source SOURCE] [--output-dir OUTPUT_DIR] [--merge]
```

Options:
- `--source`: The data source to scrape. Choices are "all", "arrivealive", "statssa", "dot", "rtmc". Default is "all".
- `--output-dir`: The directory to save the output files. Default is "output" in the project root. This is where you'll find your CSV files.
- `--merge`: Merge all CSV files into a single file.

### Examples

1. Scrape data from all sources:
   ```
   python main.py
   ```

2. Scrape data from a specific source:
   ```
   python main.py --source arrivealive
   ```

3. Scrape data from all sources and merge into a single CSV file (accidents_south_africa.csv):
   ```
   python main.py --merge
   ```
   This will create a file named `accidents_south_africa.csv` in the output directory. If this file already exists, a number will be appended to the filename (e.g., `accidents_south_africa_1.csv`).

4. Specify a custom output directory (this is where your CSV files will be saved):
   ```
   python main.py --output-dir data/accidents
   ```
   This will save all output files to the `data/accidents` directory instead of the default `output` directory.

### Programmatic Usage

You can also use the scrapers programmatically in your own Python code:

```python
from Scraper.ARRIVEALIVE_Scraper import ArriveAliveScraper

# Create a scraper instance
scraper = ArriveAliveScraper()

# Fetch and parse data
scraper.fetch_data()
scraper.parse_data()

# Export to CSV using the default filename (accidents_south_africa.csv) in the default output directory
csv_path = scraper.export_to_csv()
print(f"Data exported to {csv_path}")
# The file will be saved in the 'output' directory in your project root

# Or specify a custom output file and/or directory
# csv_path = scraper.export_to_csv(output_file="custom_filename.csv", output_dir="custom_output_dir")
# print(f"Data exported to {csv_path}")
# This will save the file to 'custom_output_dir/custom_filename.csv'
```

## Project Structure

- `main.py`: Main entry point for the application
- `Scraper/`: Directory containing all scraper modules
  - `base_scraper.py`: Base class for all scrapers
  - `ARRIVEALIVE_Scraper/`: Arrive Alive scraper
  - `STATSSA_Scraper/`: Statistics South Africa scraper
  - `DOT_Scraper/`: Department of Transport scraper
  - `RTMC_Scraper/`: Road Traffic Management Corporation scraper
  - `CITYOFCAPETOWN_Scraper/`: City of Cape Town scraper
  - `ITRAFFIC_Scraper/`: iTraffic scraper
- `output/`: Directory where all output CSV files are saved (created automatically if it doesn't exist)

## Extending the Project

To add a new scraper:

1. Create a new directory in the `Scraper/` directory for your scraper
2. Create a `scraper.py` file in the new directory
3. Implement a class that inherits from `BaseScraper` and implements the `fetch_data` and `parse_data` methods
4. Update the `__init__.py` file in the new directory to expose your scraper class
5. Update `main.py` to include your new scraper

## Testing

The project includes a comprehensive test suite using pytest. The tests cover:

- Base scraper functionality
- Specific scraper implementations
- Main orchestration logic
- CSV output functionality

### Running Tests

To run the tests, use the following command:

```
pytest Tests/
```

To run tests with coverage information:

```
pytest Tests/ --cov=Scraper --cov=main
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
