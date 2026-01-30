"""Test case loader for parsing Markdown case files.

This module discovers and parses test case files from the repository.
Case files are Markdown with YAML frontmatter in the testla/cases/ directory.
"""

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import frontmatter

from testla.domain.case import (
    AutomationStatus,
    Case,
    CaseId,
    CaseMetadata,
    ExternalId,
    Priority,
)
from testla.repository.config import SECTION_ALIASES, TestlaConfig


class CaseParseError(Exception):
    """Raised when a case file cannot be parsed."""

    def __init__(self, file_path: Path, message: str) -> None:
        self.file_path = file_path
        super().__init__(f"{file_path}: {message}")


class CaseLoader:
    """
    Loads and parses test case files from the repository.

    Case files are expected to be Markdown files with YAML frontmatter
    located in the configured cases directory (default: testla/cases/).
    """

    def __init__(self, config: TestlaConfig, root_path: Path | None = None) -> None:
        """
        Initialize the case loader.

        :param config: Testla configuration
        :param root_path: Repository root path (defaults to current directory)
        """
        self.config = config
        self.root_path = root_path or Path.cwd()
        self._cases: dict[ExternalId, Case] = {}

    @classmethod
    def discover(cls, root_path: Path | None = None) -> "CaseLoader":
        """
        Create a loader and discover all cases.

        Convenience factory that loads config and discovers cases in one call.

        :param root_path: Repository root path
        :return: CaseLoader with discovered cases
        """
        config = TestlaConfig.load(root_path)
        loader = cls(config, root_path)
        loader.load_all()
        return loader

    @property
    def cases_dir(self) -> Path:
        """Get the full path to the cases directory."""
        return self.root_path / self.config.cases_dir

    def load_all(self) -> list[Case]:
        """
        Load all test cases from the cases directory.

        :return: List of loaded test cases
        """
        self._cases.clear()

        if not self.cases_dir.exists():
            return []

        cases = []
        for case_file in self.cases_dir.rglob("*.md"):
            # Skip template files
            if case_file.name.startswith("_"):
                continue

            try:
                case = self._load_case_file(case_file)
                self._cases[case.external_id] = case
                cases.append(case)
            except CaseParseError:
                # Log warning but continue loading other cases
                # TODO: Add proper logging
                pass

        return cases

    def get(self, external_id: str) -> Case | None:
        """
        Get a test case by its external ID.

        :param external_id: The case ID (e.g., "TC001")
        :return: Case if found, None otherwise
        """
        return self._cases.get(ExternalId(external_id))

    def __iter__(self) -> Iterator[Case]:
        """Iterate over all loaded cases."""
        return iter(self._cases.values())

    def __len__(self) -> int:
        """Return the number of loaded cases."""
        return len(self._cases)

    def _load_case_file(self, file_path: Path) -> Case:
        """
        Load a single test case from a Markdown file.

        :param file_path: Path to the case file
        :return: Parsed Case
        :raises CaseParseError: If the file cannot be parsed
        """
        try:
            post = frontmatter.load(file_path)
        except Exception as e:
            raise CaseParseError(file_path, f"Failed to parse frontmatter: {e}") from e

        metadata = post.metadata
        content = post.content

        # Extract required fields
        external_id = self._extract_external_id(file_path, metadata)
        title = metadata.get("title", self._title_from_filename(file_path))

        # Extract optional metadata
        priority = self._parse_priority(metadata.get("priority", "medium"))
        automation = metadata.get("automation", {})
        automation_status = self._parse_automation_status(
            automation.get("status", "none")
        )
        test_path = automation.get("test_path")
        tags = tuple(metadata.get("tags", []))

        # Parse content sections
        sections = self._parse_content_sections(content)

        # Calculate section path from file location
        section_path = self._calculate_section_path(file_path)

        case_metadata = CaseMetadata(
            priority=priority,
            automation_status=automation_status,
            tags=tags,
            custom_fields=metadata.get("custom", {}),
        )

        return Case(
            id=CaseId(self._generate_uuid_from_id(external_id)),
            external_id=ExternalId(external_id),
            title=title,
            section_path=section_path,
            description=sections.get("description", ""),
            preconditions=sections.get("preconditions", ""),
            steps=sections.get("steps", ""),
            expected_result=sections.get("expected", ""),
            metadata=case_metadata,
            test_path=test_path,
            file_path=str(file_path.relative_to(self.root_path)),
        )

    def _extract_external_id(self, file_path: Path, metadata: dict[str, Any]) -> str:
        """Extract the external ID from metadata or filename."""
        if "id" in metadata:
            return str(metadata["id"])

        # Try to extract from filename (e.g., "TC001-valid-login.md")
        match = re.match(r"^([A-Z]+\d+)", file_path.stem)
        if match:
            return match.group(1)

        raise CaseParseError(
            file_path, "No 'id' in frontmatter and cannot extract from filename"
        )

    def _title_from_filename(self, file_path: Path) -> str:
        """Generate a title from the filename."""
        # Remove ID prefix if present (e.g., "TC001-valid-login" -> "valid-login")
        name = re.sub(r"^[A-Z]+\d+-?", "", file_path.stem)
        # Convert kebab-case to title case
        return name.replace("-", " ").title()

    def _parse_priority(self, value: str) -> Priority:
        """Parse priority string to enum."""
        try:
            return Priority(value.lower())
        except ValueError:
            return Priority.MEDIUM

    def _parse_automation_status(self, value: str) -> AutomationStatus:
        """Parse automation status string to enum."""
        mapping = {
            "none": AutomationStatus.NONE,
            "automated": AutomationStatus.AUTOMATED,
            "to_be_automated": AutomationStatus.TO_BE_AUTOMATED,
            "to-be-automated": AutomationStatus.TO_BE_AUTOMATED,
            "planned": AutomationStatus.TO_BE_AUTOMATED,
        }
        return mapping.get(value.lower(), AutomationStatus.NONE)

    def _parse_content_sections(self, content: str) -> dict[str, str]:
        """
        Parse Markdown content into named sections.

        Looks for headers like "## Given", "## When", "## Then" (BDD format),
        "## Arrange", "## Act", "## Assert" (AAA format), or
        "## Preconditions", "## Steps", "## Expected Result" (Classic format).

        All format aliases are recognized regardless of configuration to ensure
        interoperability between different section format styles.
        """
        sections: dict[str, str] = {}
        current_section: str | None = None
        current_content: list[str] = []

        # Build mapping from all aliases to canonical section keys
        # This allows parsing any format regardless of project configuration
        section_mapping: dict[str, str] = {}
        for canonical_key, aliases in SECTION_ALIASES.items():
            for alias in aliases:
                section_mapping[alias] = canonical_key

        # Add non-format-specific sections
        section_mapping["description"] = "description"
        section_mapping["notes"] = "notes"
        section_mapping["prerequisites"] = "preconditions"
        section_mapping["test steps"] = "steps"

        for line in content.split("\n"):
            # Check for section header
            header_match = re.match(r"^##\s+(.+)$", line)
            if header_match:
                # Save previous section
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()

                # Start new section
                header_text = header_match.group(1).lower().strip()
                current_section = section_mapping.get(header_text)
                current_content = []
            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        # If no sections found, treat entire content as description
        if not sections and content.strip():
            sections["description"] = content.strip()

        return sections

    def _calculate_section_path(self, file_path: Path) -> str:
        """Calculate the section path from file location."""
        try:
            relative = file_path.relative_to(self.cases_dir)
            # Get parent directories as section path
            if relative.parent != Path():
                return str(relative.parent)
        except ValueError:
            pass
        return ""

    def _generate_uuid_from_id(self, external_id: str) -> Any:
        """Generate a deterministic UUID from the external ID."""
        import uuid

        # Use UUID5 with a namespace to generate deterministic IDs
        namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # URL namespace
        return uuid.uuid5(namespace, external_id)
