import sqlglot
from sqlglot import exp

from .schemas import CTE, ParsedModel


def parse_model(model_name: str, raw_sql: str) -> ParsedModel:
    """
    Parses a raw SQL string into a ParsedModel object, identifying CTEs
    and other components.
    """
    expression = sqlglot.parse_one(raw_sql)

    ctes = {}
    if expression:
        # Recursively find all CTEs in the expression tree
        for cte_expr in expression.find_all(exp.CTE):
            # Use the 'alias_or_name' property, which is the robust way to get the CTE name
            cte_name = cte_expr.alias_or_name
            ctes[cte_name] = CTE(name=cte_name, expression=cte_expr)

    return ParsedModel(
        model_name=model_name,
        raw_sql=raw_sql,
        ctes=ctes,
        final_select=expression,
    )



