"""Utilities for normalising GradCafe scraper output."""

from __future__ import annotations

import re
from typing import Iterable, List, Mapping


StatusTuple = tuple[str, str]


def _clean_text(value: str) -> str:
    """Collapse whitespace and strip leading/trailing spaces.

    :param str value: Text to normalise.
    :return: Cleaned string with single spaces and trimmed edges.
    :rtype: str
    """

    if not value:
        return ""
    return " ".join(value.split()).strip()


def _parse_status(status_raw: str) -> StatusTuple:
    """Split status strings into state and optional date components.

    :param str status_raw: Raw status text from the scraper output.
    :return: Tuple containing status label and optional status date.
    :rtype: tuple[str, str]
    """

    if not isinstance(status_raw, str):
        return "", ""

    status_raw = status_raw.strip()
    if not status_raw:
        return "", ""

    unified = re.sub(r"wait\s*listed", "Waitlisted", status_raw, flags=re.I)
    status_match = re.search(
        r"\b(Accepted|Rejected|Waitlisted|Interview|Withdrawn)\b",
        unified,
        re.I,
    )
    status = status_match.group(1).title() if status_match else unified

    date_match = re.search(r"on\s*([\w\d\s,]+)", unified, re.I)
    status_date = date_match.group(1).strip() if date_match else ""

    return status.strip(), status_date


def _extract_term(meta_text: str) -> str:
    """Identify the admission term when present.

    :param str meta_text: Combined metadata text describing the entry.
    :return: Formatted term string such as ``"Fall 2025"`` or ``""``.
    :rtype: str
    """

    if not meta_text:
        return ""

    match = re.search(r"(Fall|Spring|Summer|Winter)\s*(\d{4})", meta_text, re.I)
    return f"{match.group(1).title()} {match.group(2)}" if match else ""


def _extract_origin(meta_text: str) -> str:
    """Return applicant origin when labelled as American or International.

    :param str meta_text: Metadata text potentially containing origin markers.
    :return: ``"American"``, ``"International"``, or ``""`` when absent.
    :rtype: str
    """

    if not meta_text:
        return ""

    if re.search(r"\bAmerican\b", meta_text, re.I):
        return "American"
    if re.search(r"\bInternational\b", meta_text, re.I):
        return "International"
    return ""


def _extract_gpa(text: str) -> str:
    """Extract GPA tokens such as ``3.80`` from free text.

    :param str text: Freeform comments or metadata text.
    :return: GPA token when detected, otherwise ``""``.
    :rtype: str
    """

    if not text:
        return ""

    match = re.search(r"GPA\s*[:]*\s*([0-9]\.\d{1,2})", text, re.I)
    if match:
        return match.group(1)

    match = re.search(r"GPA\s*([0-9]\.\d{1,2})", text, re.I)
    return match.group(1) if match else ""


def _extract_gre(text: str) -> StatusTuple:
    """Return overall GRE and verbal scores when included in text.

    :param str text: Freeform text containing GRE details.
    :return: Tuple of total score and verbal score strings.
    :rtype: tuple[str, str]
    """

    if not text:
        return "", ""

    gre_total = ""
    match = re.search(r"\bGRE[:\s]*([0-9]{3})\b", text, re.I)
    if match:
        gre_total = match.group(1)

    gre_verbal = ""
    match = re.search(r"(?:V[:\s]*|Verbal[:\s]*)([0-9]{2,3})", text, re.I)
    if match:
        gre_verbal = match.group(1)
    else:
        match = re.search(r"\b([0-9]{2,3})\s*V\b", text, re.I)
        if match:
            gre_verbal = match.group(1)

    return gre_total, gre_verbal


def _extract_gre_aw(text: str) -> str:
    """Extract GRE analytical writing values from text.

    :param str text: Freeform text potentially containing AW details.
    :return: Analytical writing score or ``""`` if not present.
    :rtype: str
    """

    if not text:
        return ""

    match = re.search(r"(?:AW|AWA|Analytical Writing)[:\s]*([0-9]\.?\d?)", text, re.I)
    return match.group(1) if match else ""


def _normalise_degree(raw_program: str, raw_degree: str) -> str:
    """Return a title-cased degree string using program fallback when needed.

    :param str raw_program: Program name supplied by the scraper.
    :param str raw_degree: Degree text supplied by the scraper.
    :return: Normalised degree descriptor or ``""`` when unavailable.
    :rtype: str
    """

    degree = _clean_text(raw_degree)
    if degree:
        return degree.title()

    match = re.search(r"(Masters|PhD|MFA|MS|MA)\b", raw_program, re.I)
    return match.group(1).title() if match else ""


class Cleaner:
    """Transform raw GradCafe scraper entries into structured applicant data."""

    def __init__(self, raw_data: Iterable[Mapping[str, str]]):
        """Initialise the cleaner with raw scraper data.

        :param Iterable raw_data: Sequence of dictionaries produced by the scraper.
        """
        self.raw_data = list(raw_data)

    @staticmethod
    def normalise_entry(raw_entry: Mapping[str, str]) -> dict:
        """Convert a single raw record into the cleaned schema.

        :param Mapping raw_entry: Raw GradCafe entry emitted by the scraper.
        :return: Dictionary shaped according to the cleaned dataset schema.
        :rtype: dict
        """

        normalised = {
            key: ("" if value is None else str(value))
            for key, value in raw_entry.items()
        }

        comments = _clean_text(normalised.get("comments_raw", ""))
        meta = normalised.get("meta_raw", "")
        combined_text = f"{comments} {meta}".strip()

        status, status_date = _parse_status(normalised.get("status_raw", ""))
        gre_total, gre_verbal = _extract_gre(combined_text)

        return {
            "program": _clean_text(normalised.get("program_raw", "")),
            "university": _clean_text(normalised.get("university_raw", "")),
            "comments": comments,
            "date_added": _clean_text(normalised.get("date_added_raw", "")),
            "url": _clean_text(normalised.get("url_raw", "")),
            "status": status,
            "status_date": status_date,
            "term": _extract_term(meta),
            "US/International": _extract_origin(meta),
            "GRE": gre_total,
            "GRE V": gre_verbal,
            "GRE AW": _extract_gre_aw(combined_text),
            "GPA": _extract_gpa(meta) or _extract_gpa(combined_text),
            "Degree": _normalise_degree(
                normalised.get("program_raw", ""),
                normalised.get("degree_raw", ""),
            ),
            "llm-generated-program": "",
            "llm-generated-university": "",
        }

    def clean_data(self) -> List[dict]:
        """Normalise raw entries into the application schema.

        :return: List of cleaned applicant dictionaries.
        :rtype: list[dict]
        """

        return [self.normalise_entry(entry) for entry in self.raw_data]
