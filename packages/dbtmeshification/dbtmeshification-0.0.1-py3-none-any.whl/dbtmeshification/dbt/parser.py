"""
Functions for parsing dbt project files and artifacts.
"""
import typing as t
import json
from pathlib import Path
import yaml

from .schemas import DbtProjectConfig, DbtManifest


def parse_dbt_project(project_path: t.Union[str, Path]) -> DbtProjectConfig:
    """
    Parse a dbt_project.yml file.

    Args:
        project_path: Path to dbt_project.yml file

    Returns:
        DbtProjectConfig object
    """
    project_path = Path(project_path)
    with open(project_path, "r") as f:
        data = yaml.safe_load(f)
    return DbtProjectConfig.from_dict(data)


def parse_manifest(manifest_path: t.Union[str, Path]) -> DbtManifest:
    """
    Parse a manifest.json file.

    Args:
        manifest_path: Path to manifest.json file

    Returns:
        DbtManifest object
    """
    manifest_path = Path(manifest_path)
    with open(manifest_path, "r") as f:
        data = json.load(f)
    return DbtManifest.from_dict(data)


def get_manifest_path(project_path: t.Union[str, Path]) -> Path:
    """
    Get the path to manifest.json given the dbt_project.yml path.

    Args:
        project_path: Path to dbt_project.yml file

    Returns:
        Path to manifest.json (typically project_root/target/manifest.json)
    """
    project_path = Path(project_path)
    project_config = parse_dbt_project(project_path)
    project_root = project_path.parent
    return project_root / project_config.target_path / "manifest.json"
