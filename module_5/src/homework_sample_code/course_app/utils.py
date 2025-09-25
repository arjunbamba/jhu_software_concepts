"""Shared utility helpers for the course application."""

from __future__ import annotations

import importlib
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import psycopg
from psycopg import Connection
from psycopg.conninfo import conninfo_to_dict, make_conninfo

SRC_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DB_CONFIG = {
    "database_url": os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:abc123@localhost:5432/gradcafe",
    )
}


def ensure_src_on_path() -> None:
    """Ensure the project root is present on ``sys.path``.

    :return: ``None``
    :rtype: None
    """

    if str(SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(SRC_ROOT))


def import_module(module_name: str):
    """Import ``module_name`` with a fallback that injects the src path.

    :param str module_name: Dotted module path to import.
    :return: Imported module object.
    :rtype: module
    """

    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:  # pragma: no cover - defensive fallback
        ensure_src_on_path()
        return importlib.import_module(module_name)


def connect(database_url: str) -> Connection:
    """Create a psycopg connection using the provided ``DATABASE_URL``.

    :param str database_url: Connection string understood by psycopg.
    :return: Live psycopg connection.
    :rtype: Connection
    """

    return psycopg.connect(database_url)


def make_admin_database_url(database_url: str, admin_db: str = "postgres") -> str:
    """Create a connection string targeting ``admin_db`` with existing credentials.

    :param str database_url: Base database connection string.
    :param str admin_db: Administrative database name to target.
    :return: Derived connection string that points at ``admin_db``.
    :rtype: str
    """

    info = conninfo_to_dict(database_url)
    info["dbname"] = admin_db
    return make_conninfo(**info)


def supports_context_manager(resource: Any) -> bool:
    """Return whether ``resource`` implements context manager hooks.

    :param Any resource: Object that may provide ``__enter__``/``__exit__`` methods.
    :return: ``True`` when the resource is a context manager, otherwise ``False``.
    :rtype: bool
    """

    return all(hasattr(resource, attr) for attr in ("__enter__", "__exit__"))


@contextmanager
def managed_connection(connection: Any) -> Iterator[Any]:
    """Yield ``connection`` ensuring cleanup for non-context manager clients.

    :param Any connection: Connection-like object potentially lacking context support.
    :yield: Connection wrapped in a context manager interface.
    :rtype: Iterator[Any]
    """

    if supports_context_manager(connection):
        with connection as managed:
            yield managed
    else:
        try:
            yield connection
        finally:
            close = getattr(connection, "close", None)
            if callable(close):  # pragma: no branch
                close()


@contextmanager
def managed_cursor(connection: Any) -> Iterator[Any]:
    """Yield a cursor from ``connection`` with safe way to close.

    :param Any connection: Connection supplying a ``cursor`` factory method.
    :yield: Cursor object that is properly closed on exit.
    :rtype: Iterator[Any]
    """

    cursor = connection.cursor()
    if supports_context_manager(cursor):
        with cursor as managed:
            yield managed
    else:
        try:
            yield cursor
        finally:
            close = getattr(cursor, "close", None)
            if callable(close):
                close()
