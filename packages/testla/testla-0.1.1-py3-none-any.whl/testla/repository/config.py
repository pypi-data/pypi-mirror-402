"""Testla configuration loading and management.

Configuration is stored in pyproject.toml under [tool.testla].
Test cases are stored in testla/cases/ directory.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class SectionFormat(Enum):
    """Test case section format styles."""

    BDD = "bdd"
    AAA = "aaa"
    CLASSIC = "classic"


# Section names for each format
SECTION_FORMATS: dict[SectionFormat, dict[str, str]] = {
    SectionFormat.BDD: {
        "preconditions": "Given",
        "steps": "When",
        "expected": "Then",
    },
    SectionFormat.AAA: {
        "preconditions": "Arrange",
        "steps": "Act",
        "expected": "Assert",
    },
    SectionFormat.CLASSIC: {
        "preconditions": "Preconditions",
        "steps": "Steps",
        "expected": "Expected Result",
    },
}

# All recognized aliases for each section (used by parser)
SECTION_ALIASES: dict[str, list[str]] = {
    "preconditions": ["given", "arrange", "preconditions", "setup", "pre-conditions"],
    "steps": ["when", "act", "steps", "action", "actions"],
    "expected": ["then", "assert", "expected", "expected result", "expected results"],
}


@dataclass
class TestlaConfig:
    """
    Configuration loaded from pyproject.toml [tool.testla] section.

    This defines project-level settings that control how Testla
    behaves for this repository.
    """

    project_name: str = "Untitled Project"
    cases_dir: str = "testla/cases"
    case_id_prefix: str = "TC"
    case_id_digits: int = 3
    default_priority: str = "medium"
    default_tags: list[str] = field(default_factory=list)
    section_format: SectionFormat = SectionFormat.BDD

    # GitHub integration
    github_repo: str | None = None
    github_status_checks: bool = True
    github_pr_comments: bool = True

    # Backend connection (optional)
    backend_url: str | None = None
    api_key: str | None = None

    @classmethod
    def load(cls, root_path: Path | None = None) -> TestlaConfig:
        """
        Load configuration from pyproject.toml [tool.testla] section.

        :param root_path: Repository root path (defaults to current directory)
        :return: Loaded configuration or defaults
        """
        if root_path is None:
            root_path = Path.cwd()

        pyproject_path = root_path / "pyproject.toml"

        if not pyproject_path.exists():
            return cls()

        with pyproject_path.open("rb") as f:
            pyproject = tomllib.load(f)

        testla_config = pyproject.get("tool", {}).get("testla", {})

        if not testla_config:
            return cls()

        return cls.from_dict(testla_config)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TestlaConfig:
        """
        Create configuration from a dictionary.

        :param data: Configuration dictionary
        :return: TestlaConfig instance
        """
        github = data.get("github", {})

        # Parse section format
        section_format_str = data.get("section_format", "bdd").lower()
        try:
            section_format = SectionFormat(section_format_str)
        except ValueError:
            section_format = SectionFormat.BDD

        return cls(
            project_name=data.get("project_name", "Untitled Project"),
            cases_dir=data.get("cases_dir", "testla/cases"),
            case_id_prefix=data.get("case_id_prefix", "TC"),
            case_id_digits=data.get("case_id_digits", 3),
            default_priority=data.get("default_priority", "medium"),
            default_tags=data.get("default_tags", []),
            section_format=section_format,
            github_repo=github.get("repo"),
            github_status_checks=github.get("status_checks", True),
            github_pr_comments=github.get("pr_comments", True),
            backend_url=data.get("backend_url"),
            api_key=data.get("api_key"),
        )

    def to_toml_section(self) -> str:
        """
        Generate TOML content for [tool.testla] section.

        :return: TOML-formatted string
        """
        lines = ["[tool.testla]"]
        lines.append(f'project_name = "{self.project_name}"')

        if self.cases_dir != "testla/cases":
            lines.append(f'cases_dir = "{self.cases_dir}"')

        if self.case_id_prefix != "TC":
            lines.append(f'case_id_prefix = "{self.case_id_prefix}"')

        if self.case_id_digits != 3:
            lines.append(f"case_id_digits = {self.case_id_digits}")

        if self.default_priority != "medium":
            lines.append(f'default_priority = "{self.default_priority}"')

        if self.section_format != SectionFormat.BDD:
            lines.append(f'section_format = "{self.section_format.value}"')

        if self.default_tags:
            tags = ", ".join(f'"{tag}"' for tag in self.default_tags)
            lines.append(f"default_tags = [{tags}]")

        if self.github_repo:
            lines.append("")
            lines.append("[tool.testla.github]")
            lines.append(f'repo = "{self.github_repo}"')
            if not self.github_status_checks:
                lines.append("status_checks = false")
            if not self.github_pr_comments:
                lines.append("pr_comments = false")

        if self.backend_url:
            lines.append("")
            lines.append(f'backend_url = "{self.backend_url}"')

        return "\n".join(lines)

    @property
    def section_names(self) -> dict[str, str]:
        """Get section names for the configured format."""
        return SECTION_FORMATS[self.section_format]

    @property
    def cases_path(self) -> Path:
        """Get the cases directory as a Path."""
        return Path(self.cases_dir)

    def generate_case_id(self, sequence: int) -> str:
        """
        Generate a case ID from a sequence number.

        :param sequence: Sequence number
        :return: Formatted case ID (e.g., "TC001")
        """
        return f"{self.case_id_prefix}{sequence:0{self.case_id_digits}d}"


def find_testla_root(start_path: Path | None = None) -> Path | None:
    """
    Find the repository root containing testla/ directory.

    Walks up from start_path looking for a directory containing
    either testla/ or pyproject.toml with [tool.testla].

    :param start_path: Starting path (defaults to current directory)
    :return: Root path or None if not found
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    while current != current.parent:
        # Check for testla/ directory
        if (current / "testla").is_dir():
            return current

        # Check for pyproject.toml with [tool.testla]
        pyproject = current / "pyproject.toml"
        if pyproject.exists():
            try:
                with pyproject.open("rb") as f:
                    data = tomllib.load(f)
                if data.get("tool", {}).get("testla"):
                    return current
            except Exception:
                pass

        current = current.parent

    return None
