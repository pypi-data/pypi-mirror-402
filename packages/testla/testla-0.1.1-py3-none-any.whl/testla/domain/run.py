"""Test run domain model.

A test run represents a single execution session of test cases.
Runs are created by the pytest plugin, CLI, or API and store
the results of test execution.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import NewType
from uuid import UUID, uuid4

from testla.domain.project import ProjectId

RunId = NewType("RunId", UUID)


class RunStatus(Enum):
    """Status of a test run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TriggerSource(Enum):
    """How the test run was initiated."""

    CLI = "cli"
    API = "api"
    CI = "ci"
    PYTEST_PLUGIN = "pytest_plugin"


@dataclass(frozen=True)
class GitContext:
    """
    Value object capturing git state at run time.

    This allows us to know exactly what code was being tested.
    """

    branch: str | None = None
    commit_sha: str | None = None
    tag: str | None = None
    is_dirty: bool = False

    @property
    def ref(self) -> str:
        """Human-readable git reference."""
        if self.tag:
            return self.tag
        if self.branch:
            short_sha = self.commit_sha[:7] if self.commit_sha else ""
            dirty = " (dirty)" if self.is_dirty else ""
            return f"{self.branch}@{short_sha}{dirty}"
        if self.commit_sha:
            return self.commit_sha[:7]
        return "unknown"


@dataclass(frozen=True)
class CIContext:
    """
    Value object capturing CI environment details.

    Populated when tests run in a CI system.
    """

    provider: str | None = None
    build_id: str | None = None
    build_url: str | None = None
    pr_number: int | None = None
    pr_title: str | None = None


@dataclass
class Run:
    """
    Aggregate root for test runs.

    A test run groups results from a single execution session.
    Results are stored separately but reference the run by ID.
    """

    id: RunId
    project_id: ProjectId
    name: str
    description: str = ""
    status: RunStatus = RunStatus.PENDING
    trigger_source: TriggerSource = TriggerSource.CLI
    git_context: GitContext | None = None
    ci_context: CIContext | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Statistics (denormalized for quick access)
    total_count: int = 0
    passed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    error_count: int = 0

    @classmethod
    def create(
        cls,
        project_id: ProjectId,
        name: str,
        *,
        description: str = "",
        trigger_source: TriggerSource = TriggerSource.CLI,
        git_context: GitContext | None = None,
        ci_context: CIContext | None = None,
    ) -> "Run":
        """
        Factory method for creating new test runs.

        :param project_id: ID of the project this run belongs to
        :param name: Run name (e.g., "Nightly regression", "PR #123")
        :param description: Optional description
        :param trigger_source: How the run was initiated
        :param git_context: Git state at run time
        :param ci_context: CI environment details
        :return: New Run instance
        """
        return cls(
            id=RunId(uuid4()),
            project_id=project_id,
            name=name,
            description=description,
            trigger_source=trigger_source,
            git_context=git_context,
            ci_context=ci_context,
        )

    def start(self) -> None:
        """Mark the run as started."""
        if self.status != RunStatus.PENDING:
            msg = f"Cannot start run in {self.status} status"
            raise ValueError(msg)
        self.status = RunStatus.RUNNING
        self.started_at = datetime.now(UTC)

    def complete(self) -> None:
        """Mark the run as completed."""
        if self.status != RunStatus.RUNNING:
            msg = f"Cannot complete run in {self.status} status"
            raise ValueError(msg)
        self.status = RunStatus.COMPLETED
        self.completed_at = datetime.now(UTC)

    def cancel(self) -> None:
        """Mark the run as cancelled."""
        if self.status == RunStatus.COMPLETED:
            msg = "Cannot cancel a completed run"
            raise ValueError(msg)
        self.status = RunStatus.CANCELLED
        self.completed_at = datetime.now(UTC)

    def record_result_counts(
        self,
        passed: int = 0,
        failed: int = 0,
        skipped: int = 0,
        error: int = 0,
    ) -> None:
        """
        Update the denormalized result counts.

        Called when results are recorded to keep stats current.

        :param passed: Number of passed tests
        :param failed: Number of failed tests
        :param skipped: Number of skipped tests
        :param error: Number of tests with errors
        """
        self.passed_count += passed
        self.failed_count += failed
        self.skipped_count += skipped
        self.error_count += error
        self.total_count = (
            self.passed_count + self.failed_count + self.skipped_count + self.error_count
        )

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate as a percentage."""
        if self.total_count == 0:
            return 0.0
        return (self.passed_count / self.total_count) * 100

    @property
    def duration_seconds(self) -> float | None:
        """Calculate run duration in seconds."""
        if self.started_at is None or self.completed_at is None:
            return None
        delta = self.completed_at - self.started_at
        return delta.total_seconds()

    @property
    def is_passing(self) -> bool:
        """Check if all executed tests passed."""
        return self.failed_count == 0 and self.error_count == 0
