"""Utilities for scraping GradCafe survey pages into structured rows."""

from __future__ import annotations

import re
from typing import List, Optional, Sequence, Tuple

import urllib3
from bs4 import BeautifulSoup


ResultRow = Tuple[str, str]


class Scraper:
    """Stateful helper that crawls GradCafe survey result pages."""

    def __init__(
        self,
        url: str = "https://www.thegradcafe.com/survey/",
        max_entries: int = 30000,
    ) -> None:
        """Configure a scraper instance for GradCafe survey pages.

        :param str url: Base survey URL that exposes paginated results.
        :param int max_entries: Maximum number of rows to collect per scrape.
        :return: ``None``
        :rtype: None
        """

        self.base = url
        self.http = urllib3.PoolManager()
        self.max_entries = max_entries

    def close(self) -> None:
        """Release underlying HTTP resources.

        :return: ``None``
        :rtype: None
        """

        self.http.clear()

    def scrape_data(self, existing_urls: Optional[Sequence[str]] = None) -> List[dict]:
        """Iteratively download survey pages and return unseen applicant rows.

        :param Sequence existing_urls: URLs that have already been processed.
        :return: List of newly discovered applicant entries.
        :rtype: list[dict]
        """

        existing = set(existing_urls or [])
        new_entries: List[dict] = []
        page = 1
        stop_scraping = False

        while len(new_entries) < self.max_entries and not stop_scraping:
            page_url = f"{self.base}?page={page}"
            collected = len(new_entries)
            print(
                f"Scraping page {page}: {page_url} "
                f"(collected {collected}/{self.max_entries})"
            )

            html = self._get_html(page_url)
            if not html:
                print("No HTML returned for URL, stopping.")
                break

            page_entries = self._extract_raw_data(html)
            if not page_entries:
                print("No entries parsed on this page, stopping.")
                break

            for entry in page_entries:
                if entry["url_raw"] in existing:
                    print("Encountered previously-seen entry. Stopping scrape.")
                    stop_scraping = True
                    break
                new_entries.append(entry)
                if len(new_entries) >= self.max_entries:
                    break

            page += 1

        print(f"Finished scraping. Collected {len(new_entries)} NEW raw entries.")
        print("")
        return new_entries

    def _get_html(self, url: str) -> Optional[str]:
        """Retrieve the raw HTML for a given paginated survey URL.

        :param str url: Fully-qualified URL to fetch.
        :return: HTML payload as a string, or ``None`` on failure.
        :rtype: str | None
        """

        response = self.http.request("GET", url)
        if response.status != 200:
            return None
        return response.data.decode("utf-8")

    def _extract_raw_data(self, html: str) -> List[dict]:
        """Parse a survey page into raw applicant dictionaries.

        :param str html: Raw HTML returned by the survey page.
        :return: List of dictionaries representing applicant entries.
        :rtype: list[dict]
        """

        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select("tbody tr")
        if not rows:
            return []

        parsed_entries: List[dict] = []
        index = 0
        total_rows = len(rows)

        while index < total_rows:
            entry, consumed = self._parse_entry(rows, index)
            index += consumed
            if entry is not None:
                parsed_entries.append(entry)

        return parsed_entries

    def _parse_entry(self, rows: Sequence, start_index: int) -> Tuple[Optional[dict], int]:
        """Parse rows starting at ``start_index`` into an entry and consumed count.

        :param Sequence rows: Sequence of table rows from the survey page.
        :param int start_index: Index of the row to interpret as the main entry.
        :return: Tuple of parsed entry dict (or ``None``) and rows consumed.
        :rtype: tuple[dict | None, int]
        """

        row = rows[start_index]
        main_entry = self._parse_main_row(row)
        if main_entry is None:
            return None, 1

        consumed = 1
        total_rows = len(rows)
        next_index = start_index + consumed

        if next_index < total_rows:
            metadata, used = self._extract_metadata(rows[next_index])
            if metadata:
                main_entry["meta_raw"] = metadata
                consumed += used
                next_index += used

        if next_index < total_rows:
            comments, used = self._extract_comments(rows[next_index])
            if comments:
                main_entry["comments_raw"] = comments
                consumed += used

        return main_entry, consumed

    @staticmethod
    def _parse_main_row(row) -> Optional[dict]:
        """Derive the base entry information from the primary row.

        :param bs4.element.Tag row: Table row containing the primary entry data.
        :return: Parsed entry dictionary or ``None`` when the row is not valid.
        :rtype: dict | None
        """

        if not Scraper._has_university_cell(row):
            return None

        cells = row.find_all("td")
        program, degree = Scraper._parse_program_and_degree(cells)

        return {
            "university_raw": Scraper._cell_text(cells, 0),
            "program_raw": program,
            "degree_raw": degree,
            "date_added_raw": Scraper._cell_text(cells, 2),
            "status_raw": Scraper._cell_text(cells, 3),
            "url_raw": Scraper._extract_result_url(row),
            "meta_raw": "",
            "comments_raw": "",
        }

    @staticmethod
    def _has_university_cell(row) -> bool:
        """Return whether the row looks like a main applicant entry.

        :param bs4.element.Tag row: Candidate table row from the survey.
        :return: ``True`` when the row contains university information.
        :rtype: bool
        """

        if row.select_one("td .tw-font-medium"):
            return True
        first_td = row.select_one("td")
        return bool(first_td and first_td.get_text(strip=True))

    @staticmethod
    def _cell_text(cells: Sequence, index: int) -> str:
        """Safely fetch the normalised text for the target ``index``.

        :param Sequence cells: Collection of ``td`` elements.
        :param int index: Index within ``cells`` to extract.
        :return: String content of the cell or ``""`` when missing.
        :rtype: str
        """

        if index < len(cells):
            return cells[index].get_text(" ", strip=True)
        return ""

    @staticmethod
    def _parse_program_and_degree(cells: Sequence) -> ResultRow:
        """Extract program and degree strings from the second column.

        :param Sequence cells: ``td`` elements composing the survey row.
        :return: Tuple containing program and degree strings.
        :rtype: ResultRow
        """

        program = degree = ""
        if len(cells) < 2:
            return program, degree

        column = cells[1]
        spans = column.select("span")
        if spans:
            program = spans[0].get_text(strip=True)
            if len(spans) >= 2:
                degree = spans[-1].get_text(strip=True)
        else:
            program = column.get_text(" ", strip=True)

        if not degree:
            degree = Scraper._infer_degree_from_column(column, program)

        return program, degree

    @staticmethod
    def _infer_degree_from_column(column, program: str) -> str:
        """Fallback when the degree is embedded within the program column.

        :param bs4.element.Tag column: Second column extracted from the row.
        :param str program: Program text already parsed from the column.
        :return: Inferred degree text or ``""`` when it cannot be determined.
        :rtype: str
        """

        possible_degree = column.get_text(" ", strip=True)
        if program and possible_degree.startswith(program):
            suffix = possible_degree[len(program) :].strip()
            return suffix
        return ""

    @staticmethod
    def _extract_result_url(row) -> str:
        """Return the absolute result URL if present in the row.

        :param bs4.element.Tag row: Table row that may contain a result link.
        :return: Absolute result URL or ``""`` when not found.
        :rtype: str
        """

        anchor = row.find("a", href=True)
        if not anchor:
            return ""
        href = anchor["href"]
        if href.startswith("http"):
            return href
        if "/result/" in href:
            return f"https://www.thegradcafe.com{href}"
        return ""

    @staticmethod
    def _extract_metadata(row) -> Tuple[str, int]:
        """Return metadata text and rows consumed when the row contains stats.

        :param bs4.element.Tag row: Table row potentially holding metadata.
        :return: Tuple of metadata text and number of rows consumed.
        :rtype: tuple[str, int]
        """

        meta_text = row.get_text(" | ", strip=True)
        if re.search(r"(Fall|Spring)\s*\d{4}|GPA\s*\d|American|International", meta_text, re.I):
            return meta_text, 1
        return "", 0

    @staticmethod
    def _extract_comments(row) -> Tuple[str, int]:
        """Return comment text and consumption flag.

        :param bs4.element.Tag row: Table row possibly containing comments.
        :return: Tuple of comment text and rows consumed.
        :rtype: tuple[str, int]
        """

        paragraph = row.find("p")
        if paragraph and paragraph.get_text(strip=True):
            return paragraph.get_text(" ", strip=True), 1
        return "", 0
