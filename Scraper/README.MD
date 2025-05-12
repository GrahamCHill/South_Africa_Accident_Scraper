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

## Usage

### Command Line Interface

The project provides a command-line interface for running the scrapers:

```
python main.py [--source SOURCE] [--output-dir OUTPUT_DIR] [--merge]
```

Options:
- `--source`: The data source to scrape. Choices are "all", "arrivealive", "statssa", "dot", "rtmc". Default is "all".
- `--output-dir`: The directory to save the output files. Default is "output" in the project root.
- `--merge`: Merge all CSV files into a single file.

### Programmatic Usage

You can also use the scrapers programmatically in your own Python code:

```python
from Scraper.ARRIVEALIVE_Scraper import ArriveAliveScraper

# Create a scraper instance
scraper = ArriveAliveScraper()

# Fetch and parse data
scraper.fetch_data()
scraper.parse_data()

# Export to CSV
csv_path = scraper.export_to_csv()
print(f"Data exported to {csv_path}")
```

## Requirements

- Python 3.13 or higher
- Dependencies:
  - requests>=2.28.0
  - beautifulsoup4>=4.11.0
  - pandas>=1.5.0
  - lxml>=4.9.0
  - tabula-py>=2.5.0
  - argparse>=1.4.0
  - pytest>=8.3.5
  - base-scraper>=1.0.2

## License

This project is proprietary and is licensed under a closed/commercial license. All rights reserved.

**License Terms:**
- This software is the property of The Shard South Africa.
- No permission is granted to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of this software without explicit written permission from The Shard South Africa.
- For licensing inquiries, please contact The Shard South Africa.

## Extending

To add a new scraper:

1. Create a new directory in the `Scraper/` directory for your scraper
2. Create a `scraper.py` file in the new directory
3. Implement a class that inherits from `BaseScraper` and implements the `fetch_data` and `parse_data` methods
4. Update the `__init__.py` file in the new directory to expose your scraper class
5. Update `main.py` to include your new scraper
