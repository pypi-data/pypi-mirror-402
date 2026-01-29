import typing as t
from dataclasses import dataclass, field
from sqlglot import exp

@dataclass
class CTE:
    """Represents a single Common Table Expression in a dbt model."""
    name: str
    expression: exp.CTE

@dataclass
class ParsedModel:
    """Represents a parsed dbt model and its constituent parts."""
    model_name: str
    raw_sql: str
    ctes: t.Dict[str, CTE] = field(default_factory=dict)
    # We can add subqueries and other components here later
    final_select: t.Optional[exp.Select] = None
