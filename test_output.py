import os
from Scraper.ARRIVEALIVE_Scraper import ArriveAliveScraper

# Create a scraper instance
scraper = ArriveAliveScraper()

# Fetch and parse data
scraper.fetch_data()
scraper.parse_data()

# Export to CSV
output_dir = "test_output"
os.makedirs(output_dir, exist_ok=True)
csv_path = scraper.export_to_csv(output_dir=output_dir)

# Print the absolute path of the exported file
abs_path = os.path.abspath(csv_path)
print(f"Data exported to {abs_path}")

# Check if the file exists
if os.path.exists(csv_path):
    print(f"File exists: {csv_path}")
    print(f"File size: {os.path.getsize(csv_path)} bytes")
else:
    print(f"File does not exist: {csv_path}")