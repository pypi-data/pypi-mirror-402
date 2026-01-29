"""
Tests for the high-level Database API.

These tests verify the simple rhizo.open() interface that users expect.
"""

import tempfile
import shutil
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pytest

import rhizo


@pytest.fixture
def temp_db_path():
    """Create a temporary directory for the database."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


class TestDatabaseOpen:
    """Tests for rhizo.open() function."""

    def test_open_creates_directory(self, temp_db_path):
        """Opening a database creates the directory structure."""
        db_path = Path(temp_db_path) / "newdb"
        assert not db_path.exists()

        db = rhizo.open(str(db_path))
        try:
            assert db_path.exists()
            assert (db_path / "chunks").exists()
            assert (db_path / "catalog").exists()
            assert (db_path / "branches").exists()
            assert (db_path / "transactions").exists()
        finally:
            db.close()

    def test_open_existing_database(self, temp_db_path):
        """Can reopen an existing database."""
        # Create and write
        db1 = rhizo.open(temp_db_path)
        df = pd.DataFrame({"id": [1, 2], "value": ["a", "b"]})
        db1.write("test", df)
        db1.close()

        # Reopen and read
        db2 = rhizo.open(temp_db_path)
        result = db2.sql("SELECT * FROM test")
        assert result.row_count == 2
        db2.close()

    def test_context_manager(self, temp_db_path):
        """Database can be used as context manager."""
        with rhizo.open(temp_db_path) as db:
            df = pd.DataFrame({"x": [1, 2, 3]})
            db.write("data", df)
            result = db.sql("SELECT SUM(x) as total FROM data")
            assert result.to_pandas()["total"][0] == 6


class TestDatabaseWrite:
    """Tests for Database.write() method."""

    def test_write_pandas_dataframe(self, temp_db_path):
        """Can write a pandas DataFrame."""
        with rhizo.open(temp_db_path) as db:
            df = pd.DataFrame({
                "id": [1, 2, 3],
                "name": ["Alice", "Bob", "Carol"],
                "score": [85.5, 92.0, 78.5]
            })
            result = db.write("students", df)

            assert result.table_name == "students"
            assert result.version == 1
            assert result.total_rows == 3

    def test_write_arrow_table(self, temp_db_path):
        """Can write a PyArrow Table."""
        with rhizo.open(temp_db_path) as db:
            table = pa.table({
                "x": [1, 2, 3],
                "y": ["a", "b", "c"]
            })
            result = db.write("arrow_data", table)

            assert result.version == 1
            assert result.total_rows == 3

    def test_write_creates_versions(self, temp_db_path):
        """Each write creates a new version."""
        with rhizo.open(temp_db_path) as db:
            df1 = pd.DataFrame({"v": [1]})
            df2 = pd.DataFrame({"v": [2]})
            df3 = pd.DataFrame({"v": [3]})

            r1 = db.write("data", df1)
            r2 = db.write("data", df2)
            r3 = db.write("data", df3)

            assert r1.version == 1
            assert r2.version == 2
            assert r3.version == 3

            versions = db.versions("data")
            assert versions == [1, 2, 3]


class TestDatabaseSQL:
    """Tests for Database.sql() method."""

    def test_simple_query(self, temp_db_path):
        """Can execute simple SQL queries."""
        with rhizo.open(temp_db_path) as db:
            df = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
            db.write("data", df)

            result = db.sql("SELECT * FROM data")
            assert result.row_count == 3

    def test_query_with_filter(self, temp_db_path):
        """Can execute queries with WHERE clause."""
        with rhizo.open(temp_db_path) as db:
            df = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
            db.write("data", df)

            result = db.sql("SELECT * FROM data WHERE value > 15")
            assert result.row_count == 2

    def test_query_with_aggregation(self, temp_db_path):
        """Can execute aggregate queries."""
        with rhizo.open(temp_db_path) as db:
            df = pd.DataFrame({"category": ["A", "A", "B"], "amount": [10, 20, 30]})
            db.write("sales", df)

            result = db.sql("SELECT category, SUM(amount) as total FROM sales GROUP BY category ORDER BY category")
            pandas_result = result.to_pandas()

            assert len(pandas_result) == 2
            assert pandas_result[pandas_result["category"] == "A"]["total"].values[0] == 30
            assert pandas_result[pandas_result["category"] == "B"]["total"].values[0] == 30

    def test_query_result_conversions(self, temp_db_path):
        """QueryResult supports multiple output formats."""
        with rhizo.open(temp_db_path) as db:
            df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
            db.write("users", df)

            result = db.sql("SELECT * FROM users")

            # to_pandas
            pandas_df = result.to_pandas()
            assert isinstance(pandas_df, pd.DataFrame)
            assert len(pandas_df) == 2

            # to_arrow
            arrow_table = result.to_arrow()
            assert isinstance(arrow_table, pa.Table)
            assert arrow_table.num_rows == 2

            # to_dict
            dict_list = result.to_dict()
            assert isinstance(dict_list, list)
            assert len(dict_list) == 2


class TestTimeTravel:
    """Tests for time travel functionality."""

    def test_query_specific_version(self, temp_db_path):
        """Can query a specific historical version."""
        with rhizo.open(temp_db_path) as db:
            # Version 1
            db.write("data", pd.DataFrame({"value": [1]}))
            # Version 2
            db.write("data", pd.DataFrame({"value": [2]}))
            # Version 3
            db.write("data", pd.DataFrame({"value": [3]}))

            # Query each version
            v1 = db.sql("SELECT * FROM data", versions={"data": 1})
            v2 = db.sql("SELECT * FROM data", versions={"data": 2})
            v3 = db.sql("SELECT * FROM data", versions={"data": 3})

            assert v1.to_pandas()["value"][0] == 1
            assert v2.to_pandas()["value"][0] == 2
            assert v3.to_pandas()["value"][0] == 3

    def test_read_specific_version(self, temp_db_path):
        """Can read a specific version directly."""
        with rhizo.open(temp_db_path) as db:
            db.write("data", pd.DataFrame({"x": [10]}))
            db.write("data", pd.DataFrame({"x": [20]}))

            v1 = db.read("data", version=1)
            v2 = db.read("data", version=2)

            assert v1.to_pandas()["x"][0] == 10
            assert v2.to_pandas()["x"][0] == 20


class TestDatabaseRead:
    """Tests for Database.read() method."""

    def test_read_arrow(self, temp_db_path):
        """read() returns PyArrow Table."""
        with rhizo.open(temp_db_path) as db:
            df = pd.DataFrame({"id": [1, 2, 3]})
            db.write("data", df)

            table = db.read("data")
            assert isinstance(table, pa.Table)
            assert table.num_rows == 3

    def test_read_pandas(self, temp_db_path):
        """read_pandas() returns pandas DataFrame."""
        with rhizo.open(temp_db_path) as db:
            df = pd.DataFrame({"id": [1, 2, 3]})
            db.write("data", df)

            result = db.read_pandas("data")
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 3

    def test_read_with_columns(self, temp_db_path):
        """Can read specific columns only."""
        with rhizo.open(temp_db_path) as db:
            df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
            db.write("data", df)

            table = db.read("data", columns=["a", "c"])
            assert table.column_names == ["a", "c"]


class TestDatabaseInfo:
    """Tests for Database.info() and metadata methods."""

    def test_tables_list(self, temp_db_path):
        """tables() returns list of table names."""
        with rhizo.open(temp_db_path) as db:
            db.write("users", pd.DataFrame({"id": [1]}))
            db.write("orders", pd.DataFrame({"id": [1]}))

            tables = db.tables()
            assert "users" in tables
            assert "orders" in tables

    def test_versions_list(self, temp_db_path):
        """versions() returns list of version numbers."""
        with rhizo.open(temp_db_path) as db:
            db.write("data", pd.DataFrame({"v": [1]}))
            db.write("data", pd.DataFrame({"v": [2]}))

            versions = db.versions("data")
            assert versions == [1, 2]

    def test_info_returns_metadata(self, temp_db_path):
        """info() returns table metadata."""
        with rhizo.open(temp_db_path) as db:
            df = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})
            db.write("users", df)

            info = db.info("users")

            assert info["table_name"] == "users"
            assert info["version"] == 1
            assert info["row_count"] == 3
            assert "id" in info["schema"]
            assert "name" in info["schema"]


class TestDatabaseClose:
    """Tests for database closing behavior."""

    def test_close_prevents_operations(self, temp_db_path):
        """Operations on closed database raise error."""
        db = rhizo.open(temp_db_path)
        db.write("data", pd.DataFrame({"x": [1]}))
        db.close()

        with pytest.raises(RuntimeError, match="closed"):
            db.sql("SELECT * FROM data")

        with pytest.raises(RuntimeError, match="closed"):
            db.write("data", pd.DataFrame({"x": [2]}))

    def test_double_close_is_safe(self, temp_db_path):
        """Closing twice doesn't raise error."""
        db = rhizo.open(temp_db_path)
        db.close()
        db.close()  # Should not raise


class TestDatabaseEngine:
    """Tests for accessing the underlying engine."""

    def test_engine_access(self, temp_db_path):
        """Can access underlying QueryEngine."""
        with rhizo.open(temp_db_path) as db:
            engine = db.engine
            assert engine is not None

            # Engine should work
            db.write("data", pd.DataFrame({"x": [1]}))
            result = engine.query("SELECT * FROM data")
            assert result.row_count == 1
