# rhizo

Query layer for [Rhizo](https://rhizodata.dev) - versioned data with SQL, time travel, and cross-table ACID transactions.

## Installation

```bash
pip install rhizo
```

## Quick Start

```python
import rhizo
import pandas as pd

# Open or create a database
db = rhizo.open("./mydata")

# Write data
df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})
db.write("users", df)

# SQL queries
result = db.sql("SELECT * FROM users WHERE id > 1")
print(result.to_pandas())

# Time travel to any version
result_v1 = db.sql("SELECT * FROM users", versions={"users": 1})

# Close when done
db.close()
```

Or use as a context manager:

```python
with rhizo.open("./mydata") as db:
    db.write("users", df)
    result = db.sql("SELECT * FROM users")
```

## Features

- **Simple API**: `rhizo.open()` handles all setup automatically
- **SQL Queries**: DuckDB-powered analytical queries
- **Time Travel**: Query any historical version
- **Cross-Table ACID**: Atomic transactions across multiple tables
- **Git-like Branching**: Zero-copy branches for experimentation
- **Change Tracking**: Subscribe to data changes

## Advanced Usage

For advanced features like branching, transactions, and OLAP queries, access the underlying engine:

```python
db = rhizo.open("./mydata")

# Branching
db.engine.create_branch("experiment")
db.engine.checkout("experiment")

# Transactions
with db.engine.transaction() as tx:
    tx.write_table("users", updated_users)
    tx.write_table("orders", new_orders)
    # Atomic commit

# OLAP queries (DataFusion)
result = db.engine.olap_query("SELECT * FROM users")
```

## Documentation

See [rhizodata.dev](https://rhizodata.dev) for full documentation.

## License

MIT
