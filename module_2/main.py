from scrape import Scraper
from clean import Cleaner
import json

data_file = "applicant_data.json"

def save_data(data, filename=data_file):
    # Saves cleaned data into json file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"STATUS: Data saved to {filename}")
    return


def main():
    # Scrape data
    # set max_entries to desired target (default 30000 in Scraper)
    scraper = Scraper(max_entries=200)
    raw_data = scraper.scrape_data()
    print("GOT RAW DATA ENTRIES:", len(raw_data))
    if len(raw_data) > 0:
        print("SAMPLE RAW ENTRY:", raw_data[0])
    
    print("")

    # Clean data
    cleaner = Cleaner(raw_data=raw_data)
    cleaned_data = cleaner.clean_data()
    print("GOT CLEANED DATA ENTRIES:", len(cleaned_data))
    if len(cleaned_data) > 0:
        print("SAMPLE CLEANED ENTRY:", cleaned_data[0])

    print("")

    # Save Data
    save_data(cleaned_data)
    print(f"SAVED DATA: {len(cleaned_data)} entries to {data_file}")

    print("")


if __name__ == "__main__":
    main()