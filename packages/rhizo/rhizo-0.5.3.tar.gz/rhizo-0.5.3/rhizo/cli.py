"""
Rhizo command-line interface.

Provides read-only database inspection and verification commands.

Usage:
    rhizo info <path>              Show database information
    rhizo tables <path>            List all tables
    rhizo versions <path> <table>  List versions of a table
    rhizo verify <path>            Verify database integrity

Environment Variables:
    RHIZO_VERIFY_INTEGRITY: Set to 'false' for faster reads (default: true)
    RHIZO_LOG_LEVEL: Set logging level (default: WARNING)
"""

import argparse
import sys
from pathlib import Path

import rhizo


def cmd_info(args: argparse.Namespace) -> int:
    """Show database information."""
    path = Path(args.path).resolve()
    if not path.exists():
        print(f"Error: Database not found: {path}", file=sys.stderr)
        return 1

    try:
        # Use verify_integrity=False for faster info lookup
        with rhizo.open(str(path), verify_integrity=False) as db:
            tables = db.tables()
            print(f"Database: {path}")
            print(f"Tables: {len(tables)}")
            print()
            if tables:
                print("Table details:")
                for table_name in sorted(tables):
                    versions = db.versions(table_name)
                    info = db.info(table_name)
                    rows = info.get("row_count", "?") if info else "?"
                    print(f"  {table_name}: {len(versions)} version(s), {rows} rows")
            else:
                print("  (no tables)")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_tables(args: argparse.Namespace) -> int:
    """List all tables."""
    path = Path(args.path).resolve()
    if not path.exists():
        print(f"Error: Database not found: {path}", file=sys.stderr)
        return 1

    try:
        with rhizo.open(str(path), verify_integrity=False) as db:
            tables = db.tables()
            for table_name in sorted(tables):
                print(table_name)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_versions(args: argparse.Namespace) -> int:
    """List versions of a table."""
    path = Path(args.path).resolve()
    if not path.exists():
        print(f"Error: Database not found: {path}", file=sys.stderr)
        return 1

    try:
        with rhizo.open(str(path), verify_integrity=False) as db:
            tables = db.tables()
            if args.table not in tables:
                print(f"Error: Table '{args.table}' not found", file=sys.stderr)
                print(f"Available tables: {', '.join(sorted(tables)) or '(none)'}", file=sys.stderr)
                return 1

            versions = db.versions(args.table)
            print(f"Table: {args.table}")
            print(f"Versions: {len(versions)}")
            print()
            for v in versions:
                info = db.info(args.table, version=v)
                rows = info.get("row_count", "?") if info else "?"
                chunks = info.get("chunk_count", "?") if info else "?"
                print(f"  v{v}: {rows} rows, {chunks} chunks")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_verify(args: argparse.Namespace) -> int:
    """Verify database integrity."""
    path = Path(args.path).resolve()
    if not path.exists():
        print(f"Error: Database not found: {path}", file=sys.stderr)
        return 1

    try:
        # Force integrity verification
        with rhizo.open(str(path), verify_integrity=True) as db:
            tables = db.tables()
            if not tables:
                print("Database is empty (no tables to verify)")
                return 0

            print(f"Verifying {len(tables)} table(s)...")
            print()
            errors = 0
            for table_name in sorted(tables):
                try:
                    # Reading with verify_integrity=True triggers hash verification
                    db.read(table_name)
                    print(f"  OK: {table_name}")
                except Exception as e:
                    print(f"  FAIL: {table_name} - {e}")
                    errors += 1

            print()
            if errors:
                print(f"Verification FAILED: {errors} table(s) with errors")
                return 1
            else:
                print(f"Verification passed: {len(tables)} table(s) OK")
                return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="rhizo",
        description="Rhizo database command-line interface",
        epilog="For more information, see: https://github.com/rhizodata/rhizo",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {rhizo.__version__}",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        metavar="<command>",
    )

    # info command
    p_info = subparsers.add_parser(
        "info",
        help="Show database information",
        description="Display summary information about a Rhizo database.",
    )
    p_info.add_argument("path", help="Path to database directory")
    p_info.set_defaults(func=cmd_info)

    # tables command
    p_tables = subparsers.add_parser(
        "tables",
        help="List all tables",
        description="List all tables in a Rhizo database.",
    )
    p_tables.add_argument("path", help="Path to database directory")
    p_tables.set_defaults(func=cmd_tables)

    # versions command
    p_versions = subparsers.add_parser(
        "versions",
        help="List versions of a table",
        description="List all versions of a specific table.",
    )
    p_versions.add_argument("path", help="Path to database directory")
    p_versions.add_argument("table", help="Table name")
    p_versions.set_defaults(func=cmd_versions)

    # verify command
    p_verify = subparsers.add_parser(
        "verify",
        help="Verify database integrity",
        description="Verify all chunks using BLAKE3 hash verification.",
    )
    p_verify.add_argument("path", help="Path to database directory")
    p_verify.set_defaults(func=cmd_verify)

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
