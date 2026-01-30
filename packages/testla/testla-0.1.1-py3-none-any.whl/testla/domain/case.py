"""Test case domain model.

Test cases are the core entity in Testla. They represent a single test scenario
that can be executed manually or automated. Test case definitions live in the
repository as Markdown files with YAML frontmatter.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import NewType
from uuid import UUID, uuid4

# Type aliases for domain identifiers
CaseId = NewType("CaseId", UUID)
ExternalId = NewType("ExternalId", str)


class Priority(Enum):
    """Test case priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AutomationStatus(Enum):
    """Indicates whether a test case has been automated."""

    NONE = "none"
    AUTOMATED = "automated"
    TO_BE_AUTOMATED = "to_be_automated"


@dataclass(frozen=True)
class CaseMetadata:
    """
    Value object containing test case metadata.

    This is immutable and identified by its values, not by identity.
    """

    priority: Priority = Priority.MEDIUM
    automation_status: AutomationStatus = AutomationStatus.NONE
    tags: tuple[str, ...] = ()
    custom_fields: dict[str, str] = field(default_factory=dict)

    def with_priority(self, priority: Priority) -> "CaseMetadata":
        """Return a new metadata instance with updated priority."""
        return CaseMetadata(
            priority=priority,
            automation_status=self.automation_status,
            tags=self.tags,
            custom_fields=self.custom_fields,
        )

    def with_tags(self, tags: tuple[str, ...]) -> "CaseMetadata":
        """Return a new metadata instance with updated tags."""
        return CaseMetadata(
            priority=self.priority,
            automation_status=self.automation_status,
            tags=tags,
            custom_fields=self.custom_fields,
        )


@dataclass
class Case:
    """
    Aggregate root for test case definitions.

    Test cases are identified internally by a UUID but also have an external_id
    (e.g., "TC001" or "auth.login.success") for referencing from test code
    and CLI commands.

    In Testla's repository-as-source-of-truth model, test cases are stored as
    Markdown files. This domain model represents the parsed/loaded form.
    """

    id: CaseId
    external_id: ExternalId
    title: str
    section_path: str = ""
    description: str = ""
    preconditions: str = ""
    steps: str = ""
    expected_result: str = ""
    metadata: CaseMetadata = field(default_factory=CaseMetadata)
    test_path: str | None = None
    file_path: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        external_id: str,
        title: str,
        *,
        section_path: str = "",
        description: str = "",
        preconditions: str = "",
        steps: str = "",
        expected_result: str = "",
        priority: Priority = Priority.MEDIUM,
        tags: tuple[str, ...] = (),
        test_path: str | None = None,
        file_path: str | None = None,
    ) -> "Case":
        """
        Factory method for creating new test cases.

        :param external_id: Human-readable identifier (e.g., "TC001")
        :param title: Brief description of what the test verifies
        :param section_path: Hierarchical path (e.g., "auth/login")
        :param description: Detailed description of the test
        :param preconditions: Required state before test execution
        :param steps: Steps to execute the test
        :param expected_result: Expected outcome
        :param priority: Test priority level
        :param tags: Categorization tags
        :param test_path: Path to automated test (e.g., "tests/test_auth.py::test_login")
        :param file_path: Path to the case file in repository
        :return: New Case instance
        """
        now = datetime.now(UTC)
        metadata = CaseMetadata(
            priority=priority,
            automation_status=(
                AutomationStatus.AUTOMATED if test_path else AutomationStatus.NONE
            ),
            tags=tags,
        )
        return cls(
            id=CaseId(uuid4()),
            external_id=ExternalId(external_id),
            title=title,
            section_path=section_path,
            description=description,
            preconditions=preconditions,
            steps=steps,
            expected_result=expected_result,
            metadata=metadata,
            test_path=test_path,
            file_path=file_path,
            created_at=now,
            updated_at=now,
        )

    @property
    def is_automated(self) -> bool:
        """Check if this test case has automation."""
        return self.metadata.automation_status == AutomationStatus.AUTOMATED

    @property
    def priority(self) -> Priority:
        """Shortcut to access priority from metadata."""
        return self.metadata.priority

    @property
    def tags(self) -> tuple[str, ...]:
        """Shortcut to access tags from metadata."""
        return self.metadata.tags

    def link_to_test(self, test_path: str) -> None:
        """
        Link this case to an automated test.

        :param test_path: Full pytest node ID (e.g., "tests/test_auth.py::test_login")
        """
        self.test_path = test_path
        self.metadata = CaseMetadata(
            priority=self.metadata.priority,
            automation_status=AutomationStatus.AUTOMATED,
            tags=self.metadata.tags,
            custom_fields=self.metadata.custom_fields,
        )
        self.updated_at = datetime.now(UTC)

    def update_metadata(self, metadata: CaseMetadata) -> None:
        """
        Update the test case metadata.

        :param metadata: New metadata values
        """
        self.metadata = metadata
        self.updated_at = datetime.now(UTC)


@dataclass(frozen=True)
class CaseSnapshot:
    """
    Immutable snapshot of test case metadata at execution time.

    When a result is recorded, we capture the state of the test case
    at that moment for historical accuracy. This allows us to know
    what the test case looked like when it was executed, even if
    the case definition changes later.
    """

    external_id: ExternalId
    title: str
    section_path: str
    priority: Priority
    tags: tuple[str, ...]

    @classmethod
    def from_case(cls, test_case: Case) -> "CaseSnapshot":
        """Create a snapshot from a test case."""
        return cls(
            external_id=test_case.external_id,
            title=test_case.title,
            section_path=test_case.section_path,
            priority=test_case.priority,
            tags=test_case.tags,
        )
