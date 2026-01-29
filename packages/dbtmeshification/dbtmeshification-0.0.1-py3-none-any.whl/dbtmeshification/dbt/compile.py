"""
Functions for compiling dbt models programmatically.
"""
import typing as t
from pathlib import Path

from dbt.cli.main import dbtRunner, dbtRunnerResult

from .parser import parse_manifest, get_manifest_path


def compile_model(
    project_path: t.Union[str, Path],
    model_name: t.Optional[str] = None,
) -> dbtRunnerResult:
    """
    Run dbt compile for a specific model or all models.

    Args:
        project_path: Path to dbt_project.yml file
        model_name: Name of the model to compile (if None, compiles all models)

    Returns:
        dbtRunnerResult object with success status and exception info

    Raises:
        Exception: If dbt compile fails
    """
    project_path = Path(project_path)
    project_root = project_path.parent

    # Build the dbt compile command arguments
    args = ["compile", "--project-dir", str(project_root)]
    if model_name:
        args.extend(["--select", model_name])

    # Run dbt compile using dbtRunner
    dbt = dbtRunner()
    result = dbt.invoke(args)

    # Check if compilation succeeded
    if not result.success:
        raise Exception(f"dbt compile failed: {result.exception}")

    return result


def get_compiled_sql(
    project_path: t.Union[str, Path],
    model_name: str,
) -> str:
    """
    Get the compiled SQL for a specific model.

    This function reads from the manifest.json file, so you must run
    compile_model() first to ensure the manifest is up to date.

    Args:
        project_path: Path to dbt_project.yml file
        model_name: Name of the model

    Returns:
        Compiled SQL string for the model

    Raises:
        ValueError: If model not found in manifest
    """
    project_path = Path(project_path)
    manifest_path = get_manifest_path(project_path)

    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Manifest not found at {manifest_path}. "
            "Run dbt compile first or call compile_model()."
        )

    manifest = parse_manifest(manifest_path)
    node = manifest.get_node_by_name(model_name)

    if node is None:
        raise ValueError(f"Model '{model_name}' not found in manifest")

    if node.compiled_sql is None:
        raise ValueError(f"Model '{model_name}' has no compiled SQL")

    return node.compiled_sql
