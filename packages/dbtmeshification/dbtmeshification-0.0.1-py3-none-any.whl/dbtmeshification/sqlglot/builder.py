import typing as t
from sqlglot import exp
from copy import deepcopy

from .schemas import ParsedModel


def _find_dependencies(cte_name: str, all_ctes: t.Dict[str, exp.CTE]) -> t.Set[str]:
    """Recursively find all upstream CTE dependencies for a given CTE."""

    # If the cte_name is not in all_ctes, it's likely a real table, so it has no upstream CTE dependencies.
    if cte_name not in all_ctes:
        return set()

    deps = set()
    cte_expression = all_ctes[cte_name].expression

    # Find all tables (which could be other CTEs) that this CTE selects from
    for source in cte_expression.find_all(exp.Table):
        source_name = source.name
        if source_name not in deps:
            deps.add(source_name)
            # Recursively find dependencies of this source
            deps.update(_find_dependencies(source_name, all_ctes))

    return deps


def _rewrite_table_references(
    expression: exp.Expression,
    mocks: t.Set[str],
    mock_schema: str = "dbtmesh_mocks"
) -> exp.Expression:
    """
    Replaces table references in the expression with references to mock tables.

    For any table that's in the mocks set, rewrites it to {mock_schema}.{table_name}

    Args:
        expression: The sqlglot expression to rewrite
        mocks: Set of table/CTE names that should be replaced with mock references
        mock_schema: Schema name where mock tables are stored

    Returns:
        A new expression with rewritten table references
    """
    cloned = deepcopy(expression)

    for table_node in cloned.find_all(exp.Table):
        table_name = table_node.name
        if table_name in mocks:
            # Replace with schema-qualified reference to mock table
            table_node.set("db", exp.to_identifier(mock_schema))

    return cloned


def build_test_query(
    parsed_model: ParsedModel,
    test_case: dict,
    mock_schema: str = "dbtmesh_mocks"
) -> exp.Expression:
    """
    Constructs a runnable sqlglot Expression for a given test case by
    rewriting references to mocked tables/CTEs to point to the mock schema.

    This function assumes that mock data has already been loaded into tables
    in the specified mock schema (e.g., dbtmesh_mocks.cte_one).

    Args:
        parsed_model: The parsed dbt model
        test_case: Test case dict with 'target' and optional 'mocks'
        mock_schema: Schema name where mock tables are stored (default: 'dbtmesh_mocks')

    Returns:
        A sqlglot Expression representing the test query
    """
    target_cte_name = test_case["target"]
    mock_names = {mock["name"] for mock in test_case.get("mocks", [])}
    all_ctes = parsed_model.ctes

    # Get all CTEs required for the target (including the target itself)
    required_cte_names = {target_cte_name}.union(_find_dependencies(target_cte_name, all_ctes))

    # Filter out mocked CTEs - we won't include them in the final query
    # since they're replaced with references to the mock schema
    # Preserve the original order from all_ctes (which is the definition order)
    unmocked_cte_names = [name for name in all_ctes if name in required_cte_names and name not in mock_names]

    # Start with the final select statement
    final_query = exp.select("*").from_(target_cte_name)

    # Add unmocked CTEs in order, rewriting any references to mocked tables
    for cte_name in unmocked_cte_names:
        # Get the CTE body and rewrite table references
        cte_body = all_ctes[cte_name].expression.this
        rewritten_body = _rewrite_table_references(cte_body, mock_names, mock_schema)
        final_query = final_query.with_(cte_name, as_=rewritten_body)

    return final_query


