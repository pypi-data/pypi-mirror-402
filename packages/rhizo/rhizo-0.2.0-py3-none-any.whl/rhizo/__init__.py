"""
Rhizo - Data, connected. SQL queries over versioned, content-addressable data.

This module provides:
- TableWriter: Write DataFrames as chunked Parquet files
- TableReader: Read and assemble tables from chunks
- QueryEngine: SQL interface with time travel support (DuckDB-based)
- OLAPEngine: High-performance analytical queries (DataFusion-based)
- CacheManager: LRU cache for Arrow tables
- TransactionContext: ACID transactions across multiple tables
- Subscriber: Stream changelog events with polling or callbacks
- ChangeEvent: Individual table change within a transaction
- Filter: Predicate filter builder for pushdown optimization

Low-level types (from _rhizo):
- PyChunkStore: Content-addressable chunk storage
- PyCatalog: Table version catalog
- PyBranchManager: Git-like branching
- PyTransactionManager: Cross-table ACID transactions
- PyMerkleConfig, merkle_build_tree, merkle_diff_trees, merkle_verify_tree: Merkle tree operations
- PyParquetEncoder, PyParquetDecoder: High-performance Parquet I/O
- PyPredicateFilter: Predicate pushdown filters
- PyOpType, PyAlgebraicValue: Algebraic merge types
- PyTableAlgebraicSchema, PyAlgebraicSchemaRegistry: Schema-level merge configuration
"""

from .writer import TableWriter
from .database import Database, open
from .reader import TableReader, Filter
from .engine import QueryEngine
from .transaction import TransactionContext
from .subscriber import Subscriber, ChangeEvent
from .cache import CacheManager, CacheKey, CacheStats
from .olap_engine import OLAPEngine, is_datafusion_available

# Re-export low-level types from _rhizo for convenience
from _rhizo import (
    PyChunkStore,
    PyCatalog,
    PyBranchManager,
    PyTransactionManager,
    PyTableVersion,
    PyBranch,
    PyBranchDiff,
    PyMerkleConfig,
    PyMerkleTree,
    PyMerkleDiff,
    PyDataChunk,
    PyMerkleNode,
    merkle_build_tree,
    merkle_diff_trees,
    merkle_verify_tree,
    PyParquetEncoder,
    PyParquetDecoder,
    PyPredicateFilter,
    PyFilterOp,
    PyScalarValue,
    PyChangelogEntry,
    PyTableChange,
    PyTransactionInfo,
    PyRecoveryReport,
    # Algebraic types
    PyOpType,
    PyAlgebraicValue,
    PyTableAlgebraicSchema,
    PyAlgebraicSchemaRegistry,
    PyMergeAnalysis,
    PyMergeOutcome,
    algebraic_merge,
    # Distributed types (coordination-free transactions)
    PyNodeId,
    PyCausalOrder,
    PyVectorClock,
    # Local commit protocol (coordination-free transactions)
    PyAlgebraicOperation,
    PyAlgebraicTransaction,
    PyVersionedUpdate,
    PyLocalCommitProtocol,
    # Simulation types (multi-node convergence testing)
    PyNetworkCondition,
    PySimulationConfig,
    PySimulationStats,
    PySimulatedNode,
    PySimulatedCluster,
    PySimulationBuilder,
)

__version__ = "0.4.0"
__all__ = [
    # High-level API
    "open",
    "Database",
    "TableWriter",
    "TableReader",
    "QueryEngine",
    "OLAPEngine",
    "CacheManager",
    "CacheKey",
    "CacheStats",
    "is_datafusion_available",
    "TransactionContext",
    "Subscriber",
    "ChangeEvent",
    "Filter",
    # Low-level types
    "PyChunkStore",
    "PyCatalog",
    "PyBranchManager",
    "PyTransactionManager",
    "PyTableVersion",
    "PyBranch",
    "PyBranchDiff",
    "PyMerkleConfig",
    "PyMerkleTree",
    "PyMerkleDiff",
    "PyDataChunk",
    "PyMerkleNode",
    "merkle_build_tree",
    "merkle_diff_trees",
    "merkle_verify_tree",
    "PyParquetEncoder",
    "PyParquetDecoder",
    "PyPredicateFilter",
    "PyFilterOp",
    "PyScalarValue",
    "PyChangelogEntry",
    "PyTableChange",
    "PyTransactionInfo",
    "PyRecoveryReport",
    # Algebraic types
    "PyOpType",
    "PyAlgebraicValue",
    "PyTableAlgebraicSchema",
    "PyAlgebraicSchemaRegistry",
    "PyMergeAnalysis",
    "PyMergeOutcome",
    "algebraic_merge",
    # Distributed types
    "PyNodeId",
    "PyCausalOrder",
    "PyVectorClock",
    # Local commit protocol
    "PyAlgebraicOperation",
    "PyAlgebraicTransaction",
    "PyVersionedUpdate",
    "PyLocalCommitProtocol",
    # Simulation types
    "PyNetworkCondition",
    "PySimulationConfig",
    "PySimulationStats",
    "PySimulatedNode",
    "PySimulatedCluster",
    "PySimulationBuilder",
]
