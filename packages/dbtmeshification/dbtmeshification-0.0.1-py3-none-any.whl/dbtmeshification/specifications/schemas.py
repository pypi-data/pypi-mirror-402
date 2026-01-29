"""
Schema definitions for test specification files.
"""
import typing as t
from dataclasses import dataclass


@dataclass
class MockData:
    """Represents mock data for a test."""
    name: str
    format: str  # "inline", "csv", "fixture", etc.
    content: t.Any  # Could be list of dicts, string, etc.

    @classmethod
    def from_dict(cls, data: dict) -> "MockData":
        """Parse mock data from spec dictionary."""
        return cls(
            name=data["name"],
            format=data.get("format", "inline"),
            content=data["content"],
        )


@dataclass
class ExpectedData:
    """Represents expected output for a test."""
    format: str  # "inline", "fixture", etc.
    content: t.Any

    @classmethod
    def from_dict(cls, data: dict) -> "ExpectedData":
        """Parse expected data from spec dictionary."""
        return cls(
            format=data.get("format", "inline"),
            content=data["content"],
        )


@dataclass
class TestCase:
    """Represents a single test case."""
    name: str
    target: str
    mocks: list[MockData]
    expect: ExpectedData

    @classmethod
    def from_dict(cls, data: dict) -> "TestCase":
        """Parse test case from spec dictionary."""
        mocks = [MockData.from_dict(m) for m in data.get("mocks", [])]
        expect = ExpectedData.from_dict(data["expect"])

        return cls(
            name=data["name"],
            target=data["target"],
            mocks=mocks,
            expect=expect,
        )


@dataclass
class TestSpec:
    """Represents a test specification file for a dbt model."""
    model: str
    tests: list[TestCase]

    @classmethod
    def from_dict(cls, data: dict) -> "TestSpec":
        """Parse test spec from YAML dictionary."""
        tests = [TestCase.from_dict(t) for t in data.get("tests", [])]

        return cls(
            model=data["model"],
            tests=tests,
        )
