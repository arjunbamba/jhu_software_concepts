"""Entrypoint for scraping and cleaning GradCafe admissions data."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable, List, Mapping

try:
    from homework_sample_code.course_app.utils import ensure_src_on_path, import_module
except ModuleNotFoundError:  # pragma: no cover - fallback for ``python main.py``
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from homework_sample_code.course_app.utils import ensure_src_on_path, import_module

ensure_src_on_path()

scrape_module = import_module("homework_sample_code.course_app.scrape")
clean_module = import_module("homework_sample_code.course_app.clean")

Scraper = scrape_module.Scraper
Cleaner = clean_module.Cleaner


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = PROJECT_ROOT / "llm_extend_applicant_data.json"


def save_data(data: List[Mapping[str, str]], filename: Path = DATA_FILE) -> None:
    """Persist cleaned applicant data to disk.

    :param list data: Serialisable list of applicant mappings.
    :param pathlib.Path filename: Target path for the JSON payload.
    :return: ``None``
    :rtype: None
    """

    with filename.open("w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)
    print(f"STATUS: Data saved to {filename}")


def load_data(filename: Path = DATA_FILE) -> List[Mapping[str, str]]:
    """Load previously cleaned applicant data from disk.

    :param pathlib.Path filename: File location containing the JSON payload.
    :return: List of applicant mappings, possibly empty.
    :rtype: list[Mapping[str, str]]
    """

    if not filename.exists():
        return []
    with filename.open("r", encoding="utf-8") as json_file:
        return json.load(json_file)


def _merge_entries(
    existing_entries: Iterable[Mapping[str, str]],
    new_entries: Iterable[Mapping[str, str]],
) -> List[Mapping[str, str]]:
    """Combine the existing dataset with freshly cleaned entries.

    :param Iterable existing_entries: Iterable of previously stored applicants.
    :param Iterable new_entries: Iterable containing the latest scraped applicants.
    :return: Concatenated list of applicant dictionaries.
    :rtype: list[Mapping[str, str]]
    """

    return list(existing_entries) + list(new_entries)


def main(max_entries: int = 30000) -> None:
    """Scrape, clean, and merge the latest GradCafe entries into the dataset.

    :param int max_entries: Maximum number of new records to scrape in this run.
    :return: ``None``
    :rtype: None
    """

    existing_cleaned = load_data()
    existing_urls = {entry.get("url", "") for entry in existing_cleaned if entry.get("url")}

    print(f"Loaded {len(existing_cleaned)} existing entries.")

    scraper = Scraper(max_entries=max_entries)
    raw_entries = scraper.scrape_data(existing_urls=existing_urls)
    print(f"Scraped {len(raw_entries)} NEW raw entries.")

    cleaner = Cleaner(raw_data=raw_entries)
    cleaned_entries = cleaner.clean_data()
    print(f"Cleaned {len(cleaned_entries)} NEW entries.")

    combined = _merge_entries(existing_cleaned, cleaned_entries)
    save_data(combined)
    print(f"Total entries after merge: {len(combined)}")


if __name__ == "__main__":  # pragma: no cover - manual execution entry point
    main()
