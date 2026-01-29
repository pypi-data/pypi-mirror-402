"""Type stubs for the rhizo package."""

from typing import List, Dict, Optional, Tuple, Union

# High-level API
from .writer import TableWriter as TableWriter
from .reader import TableReader as TableReader, Filter as Filter
from .engine import QueryEngine as QueryEngine
from .transaction import TransactionContext as TransactionContext
from .subscriber import Subscriber as Subscriber, ChangeEvent as ChangeEvent
from .cache import CacheManager as CacheManager, CacheKey as CacheKey, CacheStats as CacheStats
from .olap_engine import OLAPEngine as OLAPEngine, is_datafusion_available as is_datafusion_available

# Re-exports from _rhizo
from _rhizo import (
    PyChunkStore as PyChunkStore,
    PyCatalog as PyCatalog,
    PyBranchManager as PyBranchManager,
    PyTransactionManager as PyTransactionManager,
    PyTableVersion as PyTableVersion,
    PyBranch as PyBranch,
    PyBranchDiff as PyBranchDiff,
    PyMerkleConfig as PyMerkleConfig,
    PyMerkleTree as PyMerkleTree,
    PyMerkleDiff as PyMerkleDiff,
    PyDataChunk as PyDataChunk,
    PyMerkleNode as PyMerkleNode,
    merkle_build_tree as merkle_build_tree,
    merkle_diff_trees as merkle_diff_trees,
    merkle_verify_tree as merkle_verify_tree,
    PyParquetEncoder as PyParquetEncoder,
    PyParquetDecoder as PyParquetDecoder,
    PyPredicateFilter as PyPredicateFilter,
    PyFilterOp as PyFilterOp,
    PyScalarValue as PyScalarValue,
    PyChangelogEntry as PyChangelogEntry,
    PyTableChange as PyTableChange,
    PyTransactionInfo as PyTransactionInfo,
    PyRecoveryReport as PyRecoveryReport,
    # Algebraic types
    PyOpType as PyOpType,
    PyAlgebraicValue as PyAlgebraicValue,
    PyTableAlgebraicSchema as PyTableAlgebraicSchema,
    PyAlgebraicSchemaRegistry as PyAlgebraicSchemaRegistry,
    PyMergeAnalysis as PyMergeAnalysis,
    PyMergeOutcome as PyMergeOutcome,
    algebraic_merge as algebraic_merge,
)

__version__: str
__all__: List[str]
