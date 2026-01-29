import typing as t
import duckdb
from sqlglot import exp


def create_connection(db_path: t.Optional[str] = None) -> duckdb.DuckDBPyConnection:
    """
    Create and setup a DuckDB connection for test execution.

    Args:
        db_path: Path to a persistent DuckDB file, or None for in-memory

    Returns:
        Configured DuckDB connection with mock schema created
    """
    conn = duckdb.connect(db_path or ":memory:")
    conn.execute("CREATE SCHEMA IF NOT EXISTS dbtmesh_mocks")
    return conn


def load_mock(
    conn: duckdb.DuckDBPyConnection,
    mock_name: str,
    mock_data: list[dict[str, t.Any]],
    schema: str = "dbtmesh_mocks"
) -> None:
    """
    Load mock data into a DuckDB table.

    Args:
        conn: DuckDB connection
        mock_name: Name of the mock (will be used as table name)
        mock_data: List of dictionaries representing rows of data
        schema: Schema name to create the table in (default: dbtmesh_mocks)
    """
    if not mock_data:
        raise ValueError(f"Mock data for '{mock_name}' cannot be empty")

    table_name = f"{schema}.{mock_name}"
    conn.execute(f"DROP TABLE IF EXISTS {table_name}")

    # Get column names from first row
    columns = list(mock_data[0].keys())
    col_list = ", ".join(columns)

    # Build VALUES clause: (?, ?), (?, ?), ...
    placeholders_per_row = ", ".join(["?" for _ in columns])
    values_clause = ", ".join([f"({placeholders_per_row})" for _ in mock_data])

    # Flatten all row values into a single list for parameter binding
    all_values = []
    for row in mock_data:
        all_values.extend([row[col] for col in columns])

    # CREATE TABLE using VALUES
    sql = f"CREATE TABLE {table_name} AS SELECT * FROM (VALUES {values_clause}) AS t({col_list})"
    conn.execute(sql, all_values)


def execute_query(
    conn: duckdb.DuckDBPyConnection,
    query: t.Union[str, exp.Expression]
) -> list[dict[str, t.Any]]:
    """
    Translate SQL query to duckdb dialect.
    Execute SQL query and return results as a list of dictionaries.

    Args:
        conn: DuckDB connection
        query: SQL string or sqlglot Expression to execute

    Returns:
        List of dictionaries representing query results
    """
    if isinstance(query, exp.Expression):
        query_str = query.sql(dialect="duckdb")
    else:
        query_str = query

    result = conn.execute(query_str).fetchall()
    columns = [desc[0] for desc in conn.description]

    return [dict(zip(columns, row)) for row in result]


def compare_results(
    actual: list[dict[str, t.Any]],
    expected: list[dict[str, t.Any]]
) -> bool:
    """
    Compare actual and expected query results.

    Args:
        actual: Actual query results
        expected: Expected query results

    Returns:
        True if results match, False otherwise
    """
    # Simple equality check for now
    # Future: could add fuzzy matching, column order independence, etc.
    return actual == expected
