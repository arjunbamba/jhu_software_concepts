import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from homework_sample_code.course_app.clean import Cleaner
from homework_sample_code.course_app.main import load_data, main as run_main, save_data
from homework_sample_code.course_app.scrape import Scraper


SCRAPE_HTML = """
<table>
  <tbody>
    <tr>
      <td><div class="tw-font-medium">Example University</div></td>
      <td><span>Computer Science</span><span>Masters</span></td>
      <td>January 10, 2024</td>
      <td>Accepted on 11 Apr</td>
      <td><a href="/result/12345">link</a></td>
    </tr>
    <tr>
      <td colspan="5">Fall 2025 | GPA 3.80 | International</td>
    </tr>
    <tr>
      <td colspan="5"><p>GRE: 322 (V: 160) AW 4.5</p></td>
    </tr>
  </tbody>
</table>
"""


def fake_html_fetch(_self, url):
    if "page=1" in url:
        return SCRAPE_HTML
    return ""


@pytest.mark.integration
def test_scraper_extracts_expected_raw_entries(monkeypatch):
    """Patch network fetch to static HTML and ensure scrape_data parses expected raw fields."""
    monkeypatch.setattr(Scraper, "_get_html", fake_html_fetch)
    scraper = Scraper(max_entries=5)
    results = scraper.scrape_data(existing_urls=set())

    assert len(results) == 1
    entry = results[0]

    assert entry["university_raw"] == "Example University"
    assert entry["program_raw"] == "Computer Science"
    assert entry["degree_raw"] == "Masters"
    assert entry["date_added_raw"] == "January 10, 2024"
    assert entry["status_raw"] == "Accepted on 11 Apr"
    assert entry["meta_raw"] == "Fall 2025 | GPA 3.80 | International"
    assert entry["comments_raw"] == "GRE: 322 (V: 160) AW 4.5"
    assert entry["url_raw"].endswith("/result/12345")


@pytest.mark.integration
def test_cleaner_transforms_raw_entries():
    """Feed cleaner a raw entry and verify normalization of status, GPA, GRE, term, and degree."""
    cleaner = Cleaner(
        raw_data=[
            {
                "program_raw": "Computer Science",
                "university_raw": "Example University",
                "comments_raw": "GRE: 322 (V: 160) AW 4.5",
                "date_added_raw": "January 10, 2024",
                "url_raw": "https://www.thegradcafe.com/result/12345",
                "status_raw": "Accepted on 11 Apr",
                "meta_raw": "Fall 2025 | GPA 3.80 | International",
                "degree_raw": "Masters",
            }
        ]
    )

    cleaned = cleaner.clean_data()
    assert len(cleaned) == 1

    entry = cleaned[0]
    assert entry["program"] == "Computer Science"
    assert entry["university"] == "Example University"
    assert entry["GPA"] == "3.80"
    assert entry["GRE"] == "322"
    assert entry["GRE V"] == "160"
    assert entry["GRE AW"] == "4.5"
    assert entry["term"] == "Fall 2025"
    assert entry["US/International"] == "International"
    assert entry["Degree"] == "Masters"
    assert entry["status"] == "Accepted"
    assert entry["status_date"] == "11 Apr"


@pytest.fixture
def main_environment(monkeypatch, tmp_path):
    data_file = tmp_path / "llm_extend_applicant_data.json"
    data_file.write_text(json.dumps([
        {
            "program": "Existing Program",
            "university": "Existing University",
            "url": "https://existing",
        }
    ]))

    class FakeScraper(Scraper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def scrape_data(self, existing_urls=None):
            return [
                {
                    "program_raw": "Computer Science",
                    "university_raw": "Example University",
                    "comments_raw": "GRE: 322 (V: 160) AW 4.5",
                    "date_added_raw": "January 10, 2024",
                    "url_raw": "https://www.thegradcafe.com/result/12345",
                    "status_raw": "Accepted on 11 Apr",
                    "meta_raw": "Fall 2025 | GPA 3.80 | International",
                    "degree_raw": "Masters",
                }
            ]

    monkeypatch.setattr("homework_sample_code.course_app.main.Scraper", FakeScraper)

    def fake_load(filename=str(data_file)):
        with open(filename, "r", encoding="utf-8") as fh:
            return json.load(fh)

    monkeypatch.setattr("homework_sample_code.course_app.main.load_data", fake_load)

    saved_payload = {}

    def fake_save(data, filename=str(data_file)):
        saved_payload["data"] = data
        saved_payload["filename"] = filename

    monkeypatch.setattr("homework_sample_code.course_app.main.save_data", fake_save)

    yield SimpleNamespace(data_file=str(data_file), saved=saved_payload)

    load_data.cache_clear() if hasattr(load_data, "cache_clear") else None


@pytest.mark.integration
def test_main_merges_existing_and_new_entries(main_environment):
    """Execute main() with stub scraper/storage and confirm merged dataset is saved."""
    run_main()

    saved = main_environment.saved
    assert Path(saved["filename"]).name == "llm_extend_applicant_data.json"

    data = saved["data"]
    assert len(data) == 2

    new_entry = next(item for item in data if item["program"] == "Computer Science")

    assert new_entry["university"] == "Example University"
    assert new_entry["GPA"] == "3.80"
    assert new_entry["term"] == "Fall 2025"
    assert new_entry["US/International"] == "International"
