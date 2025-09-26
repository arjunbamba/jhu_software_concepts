"""Shared SQL query constants used across test modules."""

from __future__ import annotations

from psycopg import sql

from tests.import_utils import import_module


_query_data = import_module("query_data")
_QUESTION_LOOKUP = dict(_query_data.QUESTION_QUERIES)

QUERY_COUNT_FALL = _QUESTION_LOOKUP["How many entries applied for Fall 2025?"]

QUERY_PERCENT_INTERNATIONAL = _QUESTION_LOOKUP[
    "Percentage of entries from international students (to 2 decimal places)"
]

QUERY_AVG_SCORES = _QUESTION_LOOKUP[
    "Average GPA, GRE, GRE V, GRE AW of applicants who provided them"
]

QUERY_AVG_AMERICAN = _QUESTION_LOOKUP["Average GPA of American students in Fall 2025"]

QUERY_PERCENT_ACCEPT = _QUESTION_LOOKUP["Percent of Fall 2025 entries that are Acceptances"]

QUERY_AVG_ACCEPT_GPA = _QUESTION_LOOKUP["Average GPA of Fall 2025 Acceptances"]

QUERY_JHU_MS = _QUESTION_LOOKUP["How many entries for JHU MS CS applicants"]

QUERY_GEORGETOWN_PHD = _QUESTION_LOOKUP[
    "How many 2025 PhD CS acceptances at Georgetown"
]

QUERY_TOP_UNIVERSITY = _QUESTION_LOOKUP["Which university has the most applicants overall?"]

QUERY_TOP_PROGRAM = _QUESTION_LOOKUP["What is the most common program applicants apply to?"]


def ensure_composable(query: sql.Composable) -> sql.Composable:
    """Return the provided query to satisfy lint expectations."""

    return query


# Explicitly reference each constant so pylint sees their usage within this module
ensure_composable(QUERY_COUNT_FALL)
ensure_composable(QUERY_PERCENT_INTERNATIONAL)
ensure_composable(QUERY_AVG_SCORES)
ensure_composable(QUERY_AVG_AMERICAN)
ensure_composable(QUERY_PERCENT_ACCEPT)
ensure_composable(QUERY_AVG_ACCEPT_GPA)
ensure_composable(QUERY_JHU_MS)
ensure_composable(QUERY_GEORGETOWN_PHD)
ensure_composable(QUERY_TOP_UNIVERSITY)
ensure_composable(QUERY_TOP_PROGRAM)
