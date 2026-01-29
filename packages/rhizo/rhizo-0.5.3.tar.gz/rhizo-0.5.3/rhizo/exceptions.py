"""
Rhizo exception types for specific error conditions.

These custom exceptions provide:
1. Type-safe error handling (no string matching)
2. Structured error information (table_name, version, etc.)
3. Backwards compatibility (inherit from standard exceptions)
"""

from __future__ import annotations


class RhizoError(Exception):
    """Base class for all Rhizo-specific errors."""
    pass


class TableNotFoundError(RhizoError, IOError):
    """
    Raised when a table does not exist in the catalog.

    Inherits from IOError for backwards compatibility with existing
    `except IOError` handlers.
    """

    def __init__(self, table_name: str):
        self.table_name = table_name
        super().__init__(f"Table not found: {table_name}")


class VersionNotFoundError(RhizoError, IOError):
    """
    Raised when a specific version does not exist for a table.

    Inherits from IOError for backwards compatibility.
    """

    def __init__(self, table_name: str, version: int):
        self.table_name = table_name
        self.version = version
        super().__init__(f"Version {version} not found for table: {table_name}")


class EmptyResultError(RhizoError, ValueError):
    """
    Raised when a query or filter returns no results.

    Inherits from ValueError for backwards compatibility with existing
    `except ValueError` handlers.
    """

    def __init__(self, message: str = "Query returned empty result"):
        super().__init__(message)


class SizeLimitExceededError(RhizoError, ValueError):
    """
    Raised when input data exceeds configured size limits.

    Prevents OOM attacks from oversized inputs.
    """

    def __init__(self, actual: int, maximum: int, unit: str = "bytes"):
        self.actual = actual
        self.maximum = maximum
        self.unit = unit
        super().__init__(
            f"Size limit exceeded: {actual:,} {unit} > {maximum:,} {unit} maximum"
        )
