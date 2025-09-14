from scrape import Scraper
from clean import Cleaner
import json
import os

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
data_file = os.path.join(parent_dir, "llm_extend_applicant_data.json")

def save_data(data, filename=data_file):
    # Saves cleaned data into json file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"STATUS: Data saved to {filename}")


def load_data(filename=data_file):
    # Loads cleaned data from json file
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def main():
    # Load existing cleaned data
    existing_cleaned = load_data()
    existing_urls = {d.get("url", "") for d in existing_cleaned if d.get("url")}

    print(f"Loaded {len(existing_cleaned)} existing entries.")

    # Scrape new data only
    scraper = Scraper(max_entries=30000)  # can still cap max
    raw_data = scraper.scrape_data(existing_urls=existing_urls)

    print(f"Scraped {len(raw_data)} NEW raw entries.")

    # Clean only the new raw data
    cleaner = Cleaner(raw_data=raw_data)
    new_cleaned = cleaner.clean_data()

    print(f"Cleaned {len(new_cleaned)} NEW entries.")

    # Merge old + new, then save
    combined = existing_cleaned + new_cleaned
    save_data(combined)
    print(f"Total entries after merge: {len(combined)}")


if __name__ == "__main__":
    main()