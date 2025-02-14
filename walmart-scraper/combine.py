import os
import json
import csv
from pathlib import Path


# Define the attributes to include as columns (supporting dot notation for nested fields)
SELECTED_ATTRIBUTES = [
    "id",
    "usItemId",
    "name",
    "type",
    "averageRating",
    "numberOfReviews",
    "salesUnitType",
    "sellerName",
    "imageInfo.thumbnailUrl"  # Example of a nested attribute
]

# Directory containing the JSON files
INPUT_DIR = Path("/home/cho/PipedreamCode/scrapfly-scrapers/walmart-scraper/results")  # Change this to the directory where JSON files are located
OUTPUT_FILE = "output.csv"
VALID_TYPE = "REGULAR"


def get_nested_value(data, keys):
    """Retrieve nested dictionary value using a list of keys"""
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return ""
    return data


def is_valid_record(item, required_keys, valid_type):
    """Check if the record is valid by ensuring required keys exist and type matches"""
    if item.get("type") != valid_type:
        return False
    return all(get_nested_value(item, key.split(".")) != "" for key in required_keys)


def json_to_csv(input_dir, output_file, selected_attributes):
    """Convert multiple JSON files to a single CSV file"""
    csv_data = []

    # Process each JSON file
    for json_file in input_dir.glob("*.json"):
        category_name = json_file.stem  # Extract category name from filename

        with open(json_file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"Failed to read {json_file}: {e}")
                continue

            if isinstance(data, list):
                for item in data:
                    if is_valid_record(item, selected_attributes, VALID_TYPE):
                        row = {attr: get_nested_value(item, attr.split(".")) for attr in selected_attributes}
                        row["category"] = category_name
                        csv_data.append(row)

    # Write to CSV
    if csv_data:
        fieldnames = selected_attributes + ["category"]
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)

        print(f"CSV file saved as {output_file}")
    else:
        print("No valid data found to write to CSV.")


if __name__ == "__main__":
    json_to_csv(INPUT_DIR, OUTPUT_FILE, SELECTED_ATTRIBUTES)
