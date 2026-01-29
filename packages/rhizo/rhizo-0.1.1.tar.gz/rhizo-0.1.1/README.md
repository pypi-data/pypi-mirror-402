# rhizo

Query layer for [Rhizo](https://rhizodata.dev) - versioned data with SQL, time travel, and cross-table ACID transactions.

## Installation

```bash
pip install rhizo
```

### From Source

```bash
git clone https://github.com/rhizodata/rhizo.git
cd rhizo/python
pip install -e .
```

Note: Requires `rhizo-core` (Rust) to be built first. See the main [README](https://github.com/rhizodata/rhizo) for full build instructions.

## Quick Start

```python
import rhizo
from rhizo import QueryEngine
import pandas as pd

# Initialize storage
store = rhizo.PyChunkStore("./data/chunks")
catalog = rhizo.PyCatalog("./data/catalog")
engine = QueryEngine(store, catalog)

# Write data
df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})
engine.write_table("users", df)

# SQL queries with DuckDB
result = engine.query("SELECT * FROM users WHERE id > 1")
print(result.to_pandas())

# Time travel to any version
result_v1 = engine.query("SELECT * FROM users", versions={"users": 1})
```

## Features

- **SQL Queries**: DuckDB-powered analytical queries
- **Time Travel**: Query any historical version
- **Cross-Table ACID**: Atomic transactions across multiple tables
- **Git-like Branching**: Zero-copy branches for experimentation
- **Change Tracking**: Subscribe to data changes

## Documentation

See [rhizodata.dev](https://rhizodata.dev) for full documentation.

## License

MIT
