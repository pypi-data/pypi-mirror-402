"""
Functions for parsing test specification files.
"""
import typing as t
from pathlib import Path
import yaml

from .schemas import TestSpec


def parse_spec_file(spec_path: t.Union[str, Path]) -> TestSpec:
    """
    Parse a test specification YAML file.

    Args:
        spec_path: Path to the spec file

    Returns:
        TestSpec object containing all test cases for the model
    """
    spec_path = Path(spec_path)

    with open(spec_path, "r") as f:
        data = yaml.safe_load(f)

    return TestSpec.from_dict(data)


def find_spec_files(specs_dir: t.Union[str, Path]) -> list[Path]:
    """
    Find all test spec files in a directory (recursively).

    Args:
        specs_dir: Directory to search for spec files

    Returns:
        List of paths to .yml/.yaml files
    """
    specs_dir = Path(specs_dir)

    if not specs_dir.exists():
        return []

    # Find all .yml and .yaml files recursively
    spec_files = []
    spec_files.extend(specs_dir.glob("**/*.yml"))
    spec_files.extend(specs_dir.glob("**/*.yaml"))

    return sorted(spec_files)
