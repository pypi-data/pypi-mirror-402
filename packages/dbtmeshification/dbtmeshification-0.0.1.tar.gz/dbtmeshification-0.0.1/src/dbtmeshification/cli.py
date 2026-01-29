import argparse
import sys
import typing as t
from pathlib import Path

from dbtmeshification.dbt.compile import get_compiled_sql
from dbtmeshification.specifications.parser import parse_spec_file, find_spec_files
from dbtmeshification.sqlglot.parser import parse_model
from dbtmeshification.sqlglot.builder import build_test_query
from dbtmeshification import runner


def run_tests(inputs: argparse.Namespace) -> int:
    """Execute unit tests for dbt models."""
    project_path = Path(inputs.project_dir) / "dbt_project.yml"
    specs_dir = Path(inputs.specs_dir)

    if not project_path.exists():
        print(f"Error: dbt_project.yml not found at {project_path}")
        return 1

    if not specs_dir.exists():
        print(f"Error: specs directory not found at {specs_dir}")
        return 1

    # Find all spec files
    spec_files = find_spec_files(specs_dir)
    if not spec_files:
        print(f"No spec files found in {specs_dir}")
        return 0

    # Filter by model if specified
    if inputs.model:
        spec_files = [
            f for f in spec_files
            if parse_spec_file(f).model == inputs.model
        ]

    print(f"Found {len(spec_files)} spec file(s) to run\n")

    # Track results
    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    # Run tests for each spec file
    for spec_file in spec_files:
        spec = parse_spec_file(spec_file)
        print(f"Testing model: {spec.model}")

        # Get compiled SQL for the model
        try:
            compiled_sql = get_compiled_sql(project_path, spec.model)
        except Exception as e:
            print(f"  Error getting compiled SQL: {e}")
            continue

        # Parse the model
        parsed_model = parse_model(spec.model, compiled_sql)

        # Create DuckDB connection
        conn = runner.create_connection(inputs.db_file)

        # Run each test case
        for test_case in spec.tests:
            total_tests += 1
            test_name = test_case.name

            try:
                # Load mocks into DuckDB
                for mock in test_case.mocks:
                    if mock.format == "inline":
                        runner.load_mock(conn, mock.name, mock.content)

                # Build test query
                test_case_dict = {
                    "target": test_case.target,
                    "mocks": [{"name": m.name} for m in test_case.mocks],
                }
                query = build_test_query(parsed_model, test_case_dict)

                # Execute query
                actual_results = runner.execute_query(conn, query)

                # Compare with expected results
                if test_case.expect.format == "inline":
                    expected_results = test_case.expect.content
                    if runner.compare_results(actual_results, expected_results):
                        print(f"  ✓ {test_name}")
                        passed_tests += 1
                    else:
                        print(f"  ✗ {test_name}")
                        print(f"    Expected: {expected_results}")
                        print(f"    Actual:   {actual_results}")
                        failed_tests += 1
                else:
                    print(f"  ⚠ {test_name} - unsupported expect format: {test_case.expect.format}")

            except Exception as e:
                print(f"  ✗ {test_name} - Error: {e}")
                failed_tests += 1

        conn.close()
        print()

    # Summary
    print(f"{'='*60}")
    print(f"Total: {total_tests} | Passed: {passed_tests} | Failed: {failed_tests}")
    print(f"{'='*60}")

    return 0 if failed_tests == 0 else 1


def cli(argvs: t.Optional[list[str]] = None) -> None:
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="mesh",
        description="A dbt companion for unit testing and column-level lineage."
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    test_parser = subparsers.add_parser("test", help="Run unit tests on dbt models")
    test_parser.add_argument(
        "--model",
        type=str,
        help="Specify a dbt model to test (e.g., my_model)",
    )
    test_parser.add_argument(
        "--select",
        type=str,
        help="dbt-style selector for models (e.g., 'tag:unit_test')",
    )
    test_parser.add_argument(
        "--db-file",
        type=str,
        help="Path to a persistent DuckDB file for test execution",
    )
    test_parser.add_argument(
        "--project-dir",
        type=str,
        default=".",
        help="Path to dbt project directory (default: current directory)",
    )
    test_parser.add_argument(
        "--specs-dir",
        type=str,
        default="specs",
        help="Path to specs directory (default: ./specs)",
    )
    test_parser.set_defaults(func=run_tests)

    return parser.parse_args(argvs or sys.argv[1:])

