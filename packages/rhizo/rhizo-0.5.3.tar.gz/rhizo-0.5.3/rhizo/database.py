"""
Database - Simple, high-level interface for Rhizo.

This module provides an easy-to-use API for common operations:

    import rhizo

    db = rhizo.open("./mydata")
    db.write("users", df)
    result = db.sql("SELECT * FROM users WHERE age > 21")
    db.close()

For advanced features (branching, transactions, OLAP), use QueryEngine directly.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union, Dict, List, Any

import pyarrow as pa

from .engine import QueryEngine, QueryResult
from .writer import WriteResult
try:
    from .olap_engine import OLAPEngine, DATAFUSION_AVAILABLE
except ImportError:
    DATAFUSION_AVAILABLE = False
    OLAPEngine = None  # type: ignore

if TYPE_CHECKING:
    import pandas as pd

# Default integrity verification: True for safety, override with RHIZO_VERIFY_INTEGRITY=false
_DEFAULT_VERIFY_INTEGRITY = os.environ.get("RHIZO_VERIFY_INTEGRITY", "true").lower() != "false"


class Database:
    """
    High-level Rhizo database interface.

    Provides simple methods for common operations while handling all the
    infrastructure setup automatically. For advanced features like branching,
    transactions, and OLAP queries, access the underlying engine directly.

    Example:
        >>> import rhizo
        >>> import pandas as pd
        >>>
        >>> # Open or create a database
        >>> db = rhizo.open("./mydata")
        >>>
        >>> # Write data
        >>> df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Carol"]})
        >>> db.write("users", df)
        >>>
        >>> # Query with SQL
        >>> result = db.sql("SELECT * FROM users WHERE id > 1")
        >>> print(result.to_pandas())
        >>>
        >>> # Time travel - query old version
        >>> old_result = db.sql("SELECT * FROM users", versions={"users": 1})
        >>>
        >>> # Clean up
        >>> db.close()

    Note:
        Use as a context manager for automatic cleanup:

        >>> with rhizo.open("./mydata") as db:
        ...     db.write("users", df)
        ...     result = db.sql("SELECT * FROM users")
    """

    def __init__(
        self,
        path: str,
        *,
        enable_branches: bool = True,
        enable_transactions: bool = True,
        verify_integrity: bool = _DEFAULT_VERIFY_INTEGRITY,
    ):
        """
        Initialize a Database at the given path.

        Prefer using rhizo.open() instead of calling this directly.

        Args:
            path: Directory path for the database. Created if it doesn't exist.
            enable_branches: Enable git-like branching (default: True)
            enable_transactions: Enable ACID transactions (default: True)
            verify_integrity: Verify chunk hashes on read (default: True for safety).
                             Set to False for faster reads in trusted environments.
                             Override default via RHIZO_VERIFY_INTEGRITY env var.
        """
        self._path = Path(path).resolve()
        self._closed = False

        # Create directory structure
        self._path.mkdir(parents=True, exist_ok=True)
        chunks_dir = self._path / "chunks"
        catalog_dir = self._path / "catalog"
        branches_dir = self._path / "branches"
        transactions_dir = self._path / "transactions"

        chunks_dir.mkdir(exist_ok=True)
        catalog_dir.mkdir(exist_ok=True)

        # Import low-level components
        from _rhizo import PyChunkStore, PyCatalog

        # Initialize core components
        self._store = PyChunkStore(str(chunks_dir))
        self._catalog = PyCatalog(str(catalog_dir))

        # Optional branch manager
        self._branch_manager = None
        if enable_branches:
            branches_dir.mkdir(exist_ok=True)
            from _rhizo import PyBranchManager
            self._branch_manager = PyBranchManager(str(branches_dir))
            # Ensure main branch exists
            try:
                self._branch_manager.get("main")
            except OSError:
                self._branch_manager.create("main")

        # Optional transaction manager
        self._transaction_manager = None
        if enable_transactions:
            transactions_dir.mkdir(exist_ok=True)
            from _rhizo import PyTransactionManager
            self._transaction_manager = PyTransactionManager(
                str(transactions_dir),
                str(catalog_dir),
                str(branches_dir) if enable_branches else None,
                auto_recover=True,
            )

        # Create the DuckDB query engine (fallback/compatibility)
        self._engine = QueryEngine(
            store=self._store,
            catalog=self._catalog,
            branch_manager=self._branch_manager,
            transaction_manager=self._transaction_manager,
            verify_integrity=verify_integrity,
        )

        # Create the DataFusion OLAP engine (primary, if available)
        self._olap_engine = None
        if DATAFUSION_AVAILABLE and OLAPEngine is not None:
            self._olap_engine = OLAPEngine(
                store=self._store,
                catalog=self._catalog,
                branch_manager=self._branch_manager,
                verify_integrity=verify_integrity,
            )

    @property
    def path(self) -> Path:
        """Get the database directory path."""
        return self._path

    @property
    def engine(self) -> QueryEngine:
        """
        Access the underlying QueryEngine for advanced features.

        Use this for:
        - Branching operations (create_branch, checkout, merge_branch)
        - Transaction context (with engine.transaction())
        - OLAP queries (olap_query, query_time_travel)
        - Changelog queries (get_changes, subscribe)

        Example:
            >>> db = rhizo.open("./mydata")
            >>> # Create a feature branch
            >>> db.engine.create_branch("experiment")
            >>> db.engine.checkout("experiment")
        """
        self._check_closed()
        return self._engine

    def sql(
        self,
        query: str,
        versions: Optional[Dict[str, int]] = None,
        params: Optional[List[Any]] = None,
    ) -> QueryResult:
        """
        Execute a SQL query using DataFusion (fast) or DuckDB (fallback).

        Uses the high-performance DataFusion OLAP engine by default.
        Falls back to DuckDB if DataFusion is not installed.

        Args:
            query: SQL query string
            versions: Optional dict mapping table names to specific versions
                     for time travel queries
            params: Optional query parameters (DuckDB fallback only)

        Returns:
            QueryResult with .to_pandas(), .to_arrow(), .to_dict() methods

        Example:
            >>> # Simple query
            >>> result = db.sql("SELECT * FROM users")
            >>>
            >>> # With time travel
            >>> result = db.sql("SELECT * FROM users", versions={"users": 1})
            >>>
            >>> # Convert to pandas
            >>> df = result.to_pandas()

        Note:
            For parameterized queries, use sql_duckdb() which supports params.
        """
        self._check_closed()

        # Use DataFusion if available (26x faster)
        if self._olap_engine is not None:
            arrow_table = self._olap_engine.query(query, versions=versions)
            return QueryResult(
                arrow_table=arrow_table,
                row_count=arrow_table.num_rows,
                column_names=arrow_table.column_names,
            )

        # Fallback to DuckDB
        return self._engine.query(query, versions=versions, params=params)

    def sql_duckdb(
        self,
        query: str,
        versions: Optional[Dict[str, int]] = None,
        params: Optional[List[Any]] = None,
    ) -> QueryResult:
        """
        Execute a SQL query using DuckDB (full SQL compatibility).

        Use this for:
        - Parameterized queries with ? placeholders
        - DuckDB-specific SQL extensions
        - When you need DuckDB's specific SQL dialect

        Args:
            query: SQL query string
            versions: Optional dict mapping table names to specific versions
            params: Optional query parameters for prepared statements

        Returns:
            QueryResult with .to_pandas(), .to_arrow(), .to_dict() methods

        Example:
            >>> # With parameters
            >>> result = db.sql_duckdb("SELECT * FROM users WHERE id = ?", params=[42])
        """
        self._check_closed()
        return self._engine.query(query, versions=versions, params=params)

    def write(
        self,
        table_name: str,
        data: Union["pd.DataFrame", pa.Table],
        metadata: Optional[Dict[str, str]] = None,
    ) -> WriteResult:
        """
        Write data as a new version of a table.

        Args:
            table_name: Name of the table (must be a valid SQL identifier)
            data: pandas DataFrame or PyArrow Table to write
            metadata: Optional key-value metadata for this version

        Returns:
            WriteResult with version info and statistics

        Example:
            >>> import pandas as pd
            >>> df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
            >>> result = db.write("users", df)
            >>> print(f"Wrote version {result.version}")
        """
        self._check_closed()
        return self._engine.write_table(table_name, data, metadata=metadata)

    def read(
        self,
        table_name: str,
        version: Optional[int] = None,
        columns: Optional[List[str]] = None,
    ) -> pa.Table:
        """
        Read a table as an Arrow Table.

        Args:
            table_name: Name of the table to read
            version: Specific version to read (None for latest)
            columns: If specified, only read these columns (faster)

        Returns:
            PyArrow Table containing the data

        Example:
            >>> table = db.read("users")
            >>> df = table.to_pandas()
            >>>
            >>> # Read specific version
            >>> old_table = db.read("users", version=1)
            >>>
            >>> # Read only specific columns (faster)
            >>> table = db.read("users", columns=["name", "age"])
        """
        self._check_closed()
        return self._engine.reader.read_arrow(table_name, version=version, columns=columns)

    def read_pandas(
        self,
        table_name: str,
        version: Optional[int] = None,
    ) -> "pd.DataFrame":
        """
        Read a table as a pandas DataFrame.

        Args:
            table_name: Name of the table to read
            version: Specific version to read (None for latest)

        Returns:
            pandas DataFrame containing the data
        """
        self._check_closed()
        return self._engine.reader.read_pandas(table_name, version=version)

    def tables(self) -> List[str]:
        """
        List all tables in the database.

        Returns:
            List of table names
        """
        self._check_closed()
        return self._engine.list_tables()

    def versions(self, table_name: str) -> List[int]:
        """
        List all versions of a table.

        Args:
            table_name: Name of the table

        Returns:
            List of version numbers
        """
        self._check_closed()
        return self._engine.list_versions(table_name)

    def info(self, table_name: str, version: Optional[int] = None) -> Dict[str, Any]:
        """
        Get information about a table.

        Args:
            table_name: Name of the table
            version: Specific version (None for latest)

        Returns:
            Dict with table metadata including schema, row count, etc.
        """
        self._check_closed()
        return self._engine.get_table_info(table_name, version)

    def close(self) -> None:
        """
        Close the database connection.

        After closing, no further operations are allowed.
        """
        if not self._closed:
            self._engine.close()
            self._closed = True

    def _check_closed(self) -> None:
        """Raise an error if the database has been closed."""
        if self._closed:
            raise RuntimeError("Database has been closed")

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __repr__(self) -> str:
        status = "closed" if self._closed else "open"
        engine = "DataFusion" if self._olap_engine else "DuckDB"
        return f"Database('{self._path}', {status}, engine={engine})"


def open(
    path: str,
    *,
    enable_branches: bool = True,
    enable_transactions: bool = True,
    verify_integrity: bool = _DEFAULT_VERIFY_INTEGRITY,
) -> Database:
    """
    Open or create a Rhizo database at the given path.

    This is the main entry point for using Rhizo. It creates all necessary
    directories and initializes the storage system automatically.

    Args:
        path: Directory path for the database. Created if it doesn't exist.
        enable_branches: Enable git-like branching for data (default: True)
        enable_transactions: Enable ACID transactions (default: True)
        verify_integrity: Verify chunk hashes on every read (default: True for safety).
                         Set to False for faster reads in trusted environments.
                         Override default via RHIZO_VERIFY_INTEGRITY env var.

    Returns:
        Database instance ready for use

    Example:
        >>> import rhizo
        >>> import pandas as pd
        >>>
        >>> # Open database
        >>> db = rhizo.open("./mydata")
        >>>
        >>> # Write some data
        >>> df = pd.DataFrame({
        ...     "id": [1, 2, 3],
        ...     "name": ["Alice", "Bob", "Carol"],
        ...     "score": [85, 92, 78]
        ... })
        >>> db.write("students", df)
        >>>
        >>> # Query with SQL
        >>> result = db.sql("SELECT name, score FROM students WHERE score > 80")
        >>> print(result.to_pandas())
        >>>
        >>> # Close when done
        >>> db.close()

        # Or use as context manager:
        >>> with rhizo.open("./mydata") as db:
        ...     db.write("users", df)
        ...     result = db.sql("SELECT * FROM users")
    """
    return Database(
        path,
        enable_branches=enable_branches,
        enable_transactions=enable_transactions,
        verify_integrity=verify_integrity,
    )
