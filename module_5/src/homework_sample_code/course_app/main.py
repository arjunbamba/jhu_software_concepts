from scrape import Scraper
from clean import Cleaner
import json
import os

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
data_file = os.path.join(parent_dir, "llm_extend_applicant_data.json")

def save_data(data, filename=data_file):
    """Persist cleaned applicant data to disk.

    :param list[dict] data: Sequence of cleaned applicant records that should be
        written.
    :param str filename: Destination JSON file. Defaults to
        :data:`data_file` in the project root.
    :return: ``None``
    :rtype: None
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"STATUS: Data saved to {filename}")


def load_data(filename=data_file):
    """Load previously cleaned applicant data from disk.

    :param str filename: JSON file to read. Defaults to :data:`data_file`.
    :return: Parsed JSON document representing cleaned applicant entries.
    :rtype: list[dict]
    """
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def main():
    """Scrape, clean, and merge the latest GradCafe entries into the dataset.

    Existing cleaned records are reloaded from disk, new raw entries are fetched
    via :class:`~homework_sample_code.course_app.scrape.Scraper`, transformed by
    :class:`~homework_sample_code.course_app.clean.Cleaner`, and the combined
    dataset is saved back to :data:`data_file`.

    :return: ``None``
    :rtype: None
    """
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
