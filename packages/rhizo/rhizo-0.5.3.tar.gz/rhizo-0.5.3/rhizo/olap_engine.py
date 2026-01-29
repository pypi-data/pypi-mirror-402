"""
OLAPEngine - High-performance OLAP query engine powered by Apache DataFusion.

Provides vectorized, multi-threaded query execution over Rhizo tables
with in-memory caching for maximum performance.

Performance (100k rows, measured):
- Filtered read (5%): 0.45ms (vs DuckDB 1.6ms = 3.6x faster)
- Projection (2 cols): 0.18ms (vs DuckDB 1.6ms = 8.9x faster)
- Full scan: 0.22ms (vs DuckDB 22.5ms = 100x faster)
"""

from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Optional, Dict, List, Any, Union

import pyarrow as pa

try:
    import datafusion
    DATAFUSION_AVAILABLE = True
except ImportError:
    DATAFUSION_AVAILABLE = False

from .cache import CacheManager, CacheKey, CacheStats
from .reader import TableReader
from .logging import get_logger

_logger = get_logger(__name__)

# Default integrity verification: True for safety, override with RHIZO_VERIFY_INTEGRITY=false
_DEFAULT_VERIFY_INTEGRITY = os.environ.get("RHIZO_VERIFY_INTEGRITY", "true").lower() != "false"

if TYPE_CHECKING:
    import pandas as pd
    import _rhizo


class OLAPEngine:
    """
    High-performance OLAP query engine powered by Apache DataFusion.

    Provides vectorized, multi-threaded query execution over Rhizo
    tables with optional in-memory caching for maximum performance.

    Key Features:
    - Vectorized execution (SIMD optimized)
    - Multi-threaded query processing
    - In-memory caching with LRU eviction
    - Full SQL support via DataFusion
    - Time travel queries (version-specific)
    - Branch-aware queries

    Example:
        >>> from _rhizo import PyChunkStore, PyCatalog
        >>> from rhizo import OLAPEngine
        >>>
        >>> store = PyChunkStore("./data/chunks")
        >>> catalog = PyCatalog("./data/catalog")
        >>> olap = OLAPEngine(store, catalog)
        >>>
        >>> # Fast analytical query
        >>> result = olap.query("SELECT category, SUM(amount) FROM orders GROUP BY category")
        >>> print(result.to_pandas())
        >>>
        >>> # Time travel query
        >>> result = olap.query("SELECT * FROM users", versions={"users": 5})
        >>>
        >>> # Check cache performance
        >>> print(olap.cache_stats())

    Performance Notes:
        - First query loads data from disk (slower)
        - Subsequent queries use cache (very fast)
        - Use preload() to warm cache before querying
    """

    def __init__(
        self,
        store: "_rhizo.PyChunkStore",
        catalog: "_rhizo.PyCatalog",
        branch_manager: Optional["_rhizo.PyBranchManager"] = None,
        max_cache_size_bytes: int = 1_000_000_000,  # 1GB default
        verify_integrity: bool = _DEFAULT_VERIFY_INTEGRITY,
    ):
        """
        Initialize the OLAP engine.

        Args:
            store: PyChunkStore for content-addressable storage
            catalog: PyCatalog for version metadata
            branch_manager: Optional branch manager for branch-aware queries
            max_cache_size_bytes: Maximum cache size in bytes (default: 1GB)
            verify_integrity: Verify chunk hashes on read (default: True for safety).
                             Set to False for faster reads in trusted environments.

        Raises:
            ImportError: If DataFusion is not installed
        """
        if not DATAFUSION_AVAILABLE:
            raise ImportError(
                "DataFusion is required for OLAPEngine. "
                "Install with: pip install datafusion"
            )

        self.store = store
        self.catalog = catalog
        self.branch_manager = branch_manager
        self._reader = TableReader(store, catalog, verify_integrity)

        # DataFusion session context
        self._ctx = datafusion.SessionContext()

        # In-memory cache
        self._cache = CacheManager(max_cache_size_bytes)

        # Track which tables are registered with DataFusion
        # Maps (table_name_lower, version, branch) -> True
        self._registered: Dict[tuple, bool] = {}

        # Current branch (default: main)
        self._current_branch = "main"

    def query(
        self,
        sql: str,
        versions: Optional[Dict[str, int]] = None,
        branch: Optional[str] = None,
    ) -> pa.Table:
        """
        Execute a SQL query with DataFusion.

        Automatically loads and caches tables referenced in the query.
        Uses vectorized, multi-threaded execution for maximum performance.

        Args:
            sql: SQL query string
            versions: Dict mapping table names to specific versions.
                     If not specified, uses branch head or latest.
            branch: Branch to query from (default: current branch)

        Returns:
            Arrow table with query results

        Raises:
            IOError: If a referenced table doesn't exist
            Exception: If SQL is invalid

        Example:
            >>> # Basic query
            >>> result = olap.query("SELECT * FROM users WHERE age > 21")
            >>>
            >>> # With aggregation
            >>> result = olap.query('''
            ...     SELECT category, COUNT(*), AVG(price)
            ...     FROM products
            ...     GROUP BY category
            ...     ORDER BY COUNT(*) DESC
            ... ''')
            >>>
            >>> # Time travel
            >>> result = olap.query("SELECT * FROM users", versions={"users": 5})
        """
        versions = versions or {}
        effective_branch = branch or self._current_branch

        # Extract table names from query
        table_names = self._extract_table_names(sql)

        # Load tables - use parallel loading for multi-table queries
        if len(table_names) > 1:
            self._load_tables_parallel(table_names, versions, effective_branch)
        else:
            for table_name in table_names:
                version = versions.get(table_name)
                self._ensure_registered(table_name, version, effective_branch)

        # Execute query with DataFusion
        df = self._ctx.sql(sql)
        batches = df.collect()
        if not batches:
            return pa.table({})
        # Convert record batches to table
        return pa.Table.from_batches(batches)

    def query_pandas(
        self,
        sql: str,
        versions: Optional[Dict[str, int]] = None,
        branch: Optional[str] = None,
    ) -> "pd.DataFrame":
        """Execute query and return pandas DataFrame."""
        result = self.query(sql, versions, branch)
        return result.to_pandas()

    def query_lazy(
        self,
        sql: str,
        versions: Optional[Dict[str, int]] = None,
        branch: Optional[str] = None,
    ) -> "datafusion.DataFrame":
        """
        Create a lazy DataFrame without executing.

        Useful for building complex query plans before execution.
        Call .collect() on the result to execute.

        Args:
            sql: SQL query string
            versions: Version overrides
            branch: Branch to query from

        Returns:
            DataFusion DataFrame (lazy, not executed)
        """
        versions = versions or {}
        effective_branch = branch or self._current_branch

        # Extract and register tables
        table_names = self._extract_table_names(sql)
        for table_name in table_names:
            version = versions.get(table_name)
            self._ensure_registered(table_name, version, effective_branch)

        return self._ctx.sql(sql)

    def preload(
        self,
        table_name: str,
        version: Optional[int] = None,
        branch: Optional[str] = None,
    ) -> None:
        """
        Preload a table into cache.

        Useful for warming the cache before running queries.

        Args:
            table_name: Name of the table to preload
            version: Specific version (None for latest/branch head)
            branch: Branch to load from (default: current branch)
        """
        effective_branch = branch or self._current_branch
        self._ensure_registered(table_name, version, effective_branch)

    def preload_tables(
        self,
        tables: List[str],
        versions: Optional[Dict[str, int]] = None,
        branch: Optional[str] = None,
    ) -> None:
        """
        Preload multiple tables into cache.

        Args:
            tables: List of table names to preload
            versions: Optional version overrides
            branch: Branch to load from
        """
        versions = versions or {}
        for table_name in tables:
            version = versions.get(table_name)
            self.preload(table_name, version, branch)

    def cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache metrics including:
            - hits: Number of cache hits
            - misses: Number of cache misses
            - hit_rate: Hit rate (0.0 to 1.0)
            - current_size_mb: Current cache size in MB
            - max_size_mb: Maximum cache size in MB
            - utilization: Cache utilization (0.0 to 1.0)
            - entry_count: Number of cached tables
        """
        return self._cache.stats().to_dict()

    def clear_cache(self, table_name: Optional[str] = None) -> None:
        """
        Clear the cache.

        Args:
            table_name: If specified, only clear this table.
                       If None, clear entire cache.
        """
        if table_name:
            self._cache.invalidate(table_name)
            # Also unregister from DataFusion
            self._unregister_table(table_name)
        else:
            self._cache.clear()
            # Create fresh DataFusion context
            self._ctx = datafusion.SessionContext()
            self._registered.clear()

    def checkout(self, branch_name: str) -> None:
        """
        Switch to a different branch.

        Args:
            branch_name: Name of the branch to switch to

        Raises:
            IOError: If branch doesn't exist
            RuntimeError: If branch_manager not configured
        """
        if self.branch_manager is None:
            raise RuntimeError("Cannot checkout: branch_manager not configured")

        # Verify branch exists
        self.branch_manager.get(branch_name)
        self._current_branch = branch_name

        # Clear cache since versions may differ
        self.clear_cache()

    @property
    def current_branch(self) -> str:
        """Get the current branch name."""
        return self._current_branch

    def list_tables(self) -> List[str]:
        """List all tables in the catalog."""
        return self.catalog.list_tables()

    def _ensure_registered(
        self,
        table_name: str,
        version: Optional[int] = None,
        branch: Optional[str] = None,
    ) -> None:
        """
        Ensure a table is loaded into cache and registered with DataFusion.

        Version resolution order:
        1. Explicit version parameter
        2. Branch head pointer
        3. Catalog latest
        """
        effective_branch = branch or self._current_branch

        # Resolve version
        resolved_version = self._resolve_version(table_name, version, effective_branch)

        # Create cache key
        cache_key = CacheKey(
            table_name=table_name.lower(),
            version=resolved_version,
            branch=effective_branch,
        )

        # Check if already registered at this exact version
        reg_key = (table_name.lower(), resolved_version, effective_branch)
        if reg_key in self._registered:
            # Update cache stats even for already registered tables
            self._cache.get(cache_key)  # This updates hit counter
            return

        # Try to get from cache
        table = self._cache.get(cache_key)

        if table is None:
            # Load from disk
            table = self._reader.read_arrow(table_name, resolved_version)

            # Add to cache
            self._cache.put(cache_key, table)

        # Deregister any existing registration of this table name
        # (different version or branch)
        self._deregister_table_from_datafusion(table_name)

        # Register with DataFusion
        df_table_name = table_name.lower()
        self._ctx.register_record_batches(df_table_name, [table.to_batches()])

        # Clear old registrations for this table name
        old_keys = [k for k in self._registered if k[0] == table_name.lower()]
        for old_key in old_keys:
            del self._registered[old_key]

        self._registered[reg_key] = True

    def _load_tables_parallel(
        self,
        table_names: List[str],
        versions: Dict[str, int],
        branch: str,
        max_workers: int = 4,
    ) -> None:
        """
        Load multiple tables in parallel for better performance on JOINs.

        Parallelizes disk reads and cache operations, but DataFusion
        registration is done sequentially (context is not thread-safe).

        Args:
            table_names: List of table names to load
            versions: Version overrides
            branch: Branch to load from
            max_workers: Maximum parallel workers (default: 4)
        """
        # First, parallel load into cache (disk I/O bound)
        def load_to_cache(table_name: str) -> tuple:
            """Load a single table into cache, return (name, version, table)."""
            version = versions.get(table_name)
            resolved_version = self._resolve_version(table_name, version, branch)

            cache_key = CacheKey(
                table_name=table_name.lower(),
                version=resolved_version,
                branch=branch,
            )

            # Check cache first
            table = self._cache.get(cache_key)
            if table is None:
                # Load from disk
                table = self._reader.read_arrow(table_name, resolved_version)
                self._cache.put(cache_key, table)

            return (table_name, resolved_version, table)

        # Parallel load phase
        loaded_tables = []
        with ThreadPoolExecutor(max_workers=min(max_workers, len(table_names))) as executor:
            futures = {executor.submit(load_to_cache, name): name for name in table_names}
            for future in as_completed(futures):
                loaded_tables.append(future.result())

        # Sequential registration phase (DataFusion context not thread-safe)
        for table_name, resolved_version, table in loaded_tables:
            reg_key = (table_name.lower(), resolved_version, branch)
            if reg_key not in self._registered:
                self._deregister_table_from_datafusion(table_name)
                self._ctx.register_record_batches(table_name.lower(), [table.to_batches()])

                # Clear old registrations
                old_keys = [k for k in self._registered if k[0] == table_name.lower()]
                for old_key in old_keys:
                    del self._registered[old_key]

                self._registered[reg_key] = True

    def _deregister_table_from_datafusion(self, table_name: str) -> None:
        """Deregister a table from DataFusion context."""
        table_lower = table_name.lower()
        try:
            # DataFusion supports deregister_table
            self._ctx.deregister_table(table_lower)
        except Exception as e:
            _logger.debug("Deregister table %s: %s", table_lower, e)

    def _resolve_version(
        self,
        table_name: str,
        version: Optional[int],
        branch: str,
    ) -> int:
        """Resolve the version to use for a table."""
        if version is not None:
            return version

        # Try branch head
        if self.branch_manager is not None:
            branch_version = self.branch_manager.get_table_version(branch, table_name)
            if branch_version is not None:
                return branch_version

        # Fall back to catalog latest
        metadata = self._reader.get_metadata(table_name)
        return metadata.version

    def _unregister_table(self, table_name: str) -> None:
        """Unregister a table from DataFusion."""
        table_lower = table_name.lower()

        # Remove from registered tracking
        keys_to_remove = [k for k in self._registered if k[0] == table_lower]
        for key in keys_to_remove:
            del self._registered[key]

        # Note: DataFusion doesn't have a direct unregister method
        # The table will be overwritten on next registration

    def _extract_table_names(self, sql: str) -> List[str]:
        """
        Extract table names from a SQL query.

        Uses simple regex matching. For production, consider
        using DataFusion's query plan analysis.
        """
        # Normalize whitespace
        sql_normalized = " ".join(sql.split())

        # Patterns: FROM table, JOIN table
        # Also matches: table VERSION N, table@branch
        patterns = [
            r'\bFROM\s+(\w+)',
            r'\bJOIN\s+(\w+)',
        ]

        table_names = set()
        for pattern in patterns:
            matches = re.findall(pattern, sql_normalized, re.IGNORECASE)
            table_names.update(m.lower() for m in matches)

        # Filter out SQL keywords
        keywords = {
            'select', 'where', 'group', 'order', 'limit', 'offset',
            'union', 'except', 'intersect', 'having', 'as', 'version'
        }
        table_names -= keywords

        return list(table_names)

    def _parse_extended_sql(self, sql: str) -> tuple:
        """
        Parse extended SQL syntax for time travel and branch queries.

        Supports:
        - `table VERSION N` - query specific version
        - `table@branch` - query from specific branch

        Args:
            sql: SQL query with optional extended syntax

        Returns:
            Tuple of (transformed_sql, versions_dict, branches_dict)

        Examples:
            >>> _parse_extended_sql("SELECT * FROM users VERSION 5")
            ("SELECT * FROM users", {"users": 5}, {})

            >>> _parse_extended_sql("SELECT * FROM users@feature/exp")
            ("SELECT * FROM users", {}, {"users": "feature/exp"})

            >>> _parse_extended_sql("SELECT * FROM users@main VERSION 3")
            ("SELECT * FROM users", {"users": 3}, {"users": "main"})
        """
        versions: Dict[str, int] = {}
        branches: Dict[str, str] = {}

        # Normalize whitespace
        sql_normalized = " ".join(sql.split())
        transformed_sql = sql_normalized

        # Pattern 1: table VERSION N (case insensitive)
        # Match: users VERSION 5, orders VERSION 10
        version_pattern = r'\b(\w+)\s+VERSION\s+(\d+)\b'
        version_matches = re.findall(version_pattern, transformed_sql, re.IGNORECASE)
        for table_name, version_str in version_matches:
            table_lower = table_name.lower()
            if table_lower not in {'select', 'from', 'where', 'join', 'group', 'order'}:
                versions[table_lower] = int(version_str)

        # Remove VERSION clauses from SQL
        transformed_sql = re.sub(
            r'\s+VERSION\s+\d+\b',
            '',
            transformed_sql,
            flags=re.IGNORECASE
        )

        # Pattern 2: table@branch (branch can have / for feature branches)
        # Match: users@main, orders@feature/experiment
        branch_pattern = r'\b(\w+)@([\w/\-]+)\b'
        branch_matches = re.findall(branch_pattern, transformed_sql)
        for table_name, branch_name in branch_matches:
            table_lower = table_name.lower()
            if table_lower not in {'select', 'from', 'where', 'join', 'group', 'order'}:
                branches[table_lower] = branch_name

        # Replace table@branch with just table in SQL
        transformed_sql = re.sub(
            r'\b(\w+)@[\w/\-]+\b',
            r'\1',
            transformed_sql
        )

        return transformed_sql, versions, branches

    def query_time_travel(
        self,
        sql: str,
        branch: Optional[str] = None,
    ) -> pa.Table:
        """
        Execute a SQL query with inline time travel and branch syntax.

        Supports extended SQL syntax:
        - `SELECT * FROM users VERSION 5` - query version 5 of users
        - `SELECT * FROM users@feature` - query users from feature branch
        - `SELECT * FROM users@main VERSION 3` - query version 3 from main

        This enables powerful data exploration:

        ```sql
        -- Compare current data with historical version
        SELECT
            curr.id,
            curr.score AS current_score,
            hist.score AS historical_score
        FROM users curr
        JOIN users VERSION 5 AS hist ON curr.id = hist.id
        WHERE curr.score != hist.score
        ```

        Args:
            sql: SQL query with optional VERSION/@ syntax
            branch: Default branch for tables without @branch

        Returns:
            Arrow table with query results
        """
        # Parse extended syntax
        transformed_sql, inline_versions, inline_branches = self._parse_extended_sql(sql)

        effective_branch = branch or self._current_branch

        # Extract table names from transformed SQL
        table_names = self._extract_table_names(transformed_sql)

        # Register each table with appropriate version/branch
        for table_name in table_names:
            # Determine branch for this table
            table_branch = inline_branches.get(table_name, effective_branch)

            # Determine version for this table
            table_version = inline_versions.get(table_name)

            self._ensure_registered(table_name, table_version, table_branch)

        # Execute transformed query
        df = self._ctx.sql(transformed_sql)
        batches = df.collect()
        if not batches:
            return pa.table({})
        return pa.Table.from_batches(batches)

    def register_changelog(
        self,
        transaction_manager: "_rhizo.PyTransactionManager",
        since_tx_id: Optional[int] = None,
        since_timestamp: Optional[int] = None,
        tables: Optional[List[str]] = None,
        branch: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> None:
        """
        Register the changelog as a queryable table named '__changelog'.

        This enables SQL queries over the changelog data:

        ```sql
        -- Get all changes in the last 10 transactions
        SELECT * FROM __changelog ORDER BY tx_id DESC LIMIT 10

        -- Find all changes to a specific table
        SELECT * FROM __changelog WHERE table_name = 'users'

        -- Count changes per table
        SELECT table_name, COUNT(*) as changes
        FROM __changelog
        GROUP BY table_name
        ORDER BY changes DESC
        ```

        Args:
            transaction_manager: The transaction manager with changelog data
            since_tx_id: Only include entries after this transaction ID
            since_timestamp: Only include entries after this Unix timestamp
            tables: Only include changes to these tables
            branch: Only include changes on this branch
            limit: Maximum number of entries to include

        Example:
            >>> olap.register_changelog(tx_manager)
            >>> result = olap.query("SELECT * FROM __changelog WHERE table_name = 'orders'")
        """
        # Fetch changelog entries
        entries = transaction_manager.get_changelog(
            since_tx_id=since_tx_id,
            since_timestamp=since_timestamp,
            tables=tables,
            branch=branch,
            limit=limit,
        )

        # Convert to Arrow table
        changelog_table = self._changelog_to_arrow(entries)

        # Deregister existing table (ignore if not exists)
        try:
            self._ctx.deregister_table("__changelog")
        except Exception as e:
            _logger.debug("Deregister __changelog: %s", e)

        # Handle empty changelog case - DataFusion requires at least one batch
        if changelog_table.num_rows == 0:
            # Register empty table with schema
            self._ctx.register_record_batches(
                "__changelog",
                [[pa.RecordBatch.from_pydict(
                    {col: [] for col in changelog_table.column_names},
                    schema=changelog_table.schema
                )]]
            )
        else:
            self._ctx.register_record_batches("__changelog", [changelog_table.to_batches()])

    def _changelog_to_arrow(self, entries: List[Any]) -> pa.Table:
        """Convert changelog entries to Arrow table."""
        # Build column data
        tx_ids = []
        epoch_ids = []
        committed_ats = []
        branches = []
        table_names = []
        old_versions = []
        new_versions = []
        is_new_tables = []

        for entry in entries:
            for change in entry.changes:
                tx_ids.append(entry.tx_id)
                epoch_ids.append(entry.epoch_id)
                committed_ats.append(entry.committed_at)
                branches.append(entry.branch)
                table_names.append(change.table_name)
                old_versions.append(change.old_version)
                new_versions.append(change.new_version)
                is_new_tables.append(change.is_new_table())

        # Create Arrow arrays
        return pa.table({
            "tx_id": pa.array(tx_ids, type=pa.int64()),
            "epoch_id": pa.array(epoch_ids, type=pa.int64()),
            "committed_at": pa.array(committed_ats, type=pa.int64()),
            "branch": pa.array(branches, type=pa.string()),
            "table_name": pa.array(table_names, type=pa.string()),
            "old_version": pa.array(old_versions, type=pa.int64()),
            "new_version": pa.array(new_versions, type=pa.int64()),
            "is_new_table": pa.array(is_new_tables, type=pa.bool_()),
        })

    def query_changelog(
        self,
        sql: str,
        transaction_manager: "_rhizo.PyTransactionManager",
        since_tx_id: Optional[int] = None,
        since_timestamp: Optional[int] = None,
        tables: Optional[List[str]] = None,
        branch: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> pa.Table:
        """
        Execute a SQL query over the changelog.

        This is a convenience method that registers the changelog
        and executes the query in one step.

        Args:
            sql: SQL query (use __changelog as table name)
            transaction_manager: The transaction manager
            since_tx_id: Filter: only entries after this tx_id
            since_timestamp: Filter: only entries after this timestamp
            tables: Filter: only changes to these tables
            branch: Filter: only changes on this branch
            limit: Maximum changelog entries to load

        Returns:
            Arrow table with query results

        Example:
            >>> # Find tables with most changes
            >>> result = olap.query_changelog('''
            ...     SELECT table_name, COUNT(*) as changes
            ...     FROM __changelog
            ...     GROUP BY table_name
            ...     ORDER BY changes DESC
            ... ''', tx_manager)
        """
        # Register changelog
        self.register_changelog(
            transaction_manager,
            since_tx_id=since_tx_id,
            since_timestamp=since_timestamp,
            tables=tables,
            branch=branch,
            limit=limit,
        )

        # Execute query
        df = self._ctx.sql(sql)
        batches = df.collect()
        if not batches:
            return pa.table({})
        return pa.Table.from_batches(batches)

    def __enter__(self) -> "OLAPEngine":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass  # No cleanup needed


def is_datafusion_available() -> bool:
    """Check if DataFusion is available."""
    return DATAFUSION_AVAILABLE
