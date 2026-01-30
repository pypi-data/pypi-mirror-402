"""Result domain model.

A result represents the outcome of executing a single test case
within a test run. Results are separate aggregates (not embedded
in TestRun) because they're written one-at-a-time as tests complete.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import NewType
from uuid import UUID, uuid4

from testla.domain.case import CaseSnapshot, ExternalId
from testla.domain.run import RunId

ResultId = NewType("ResultId", UUID)


class ResultStatus(Enum):
    """Outcome status of a test execution."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    BLOCKED = "blocked"
    RETEST = "retest"


@dataclass(frozen=True)
class FailureInfo:
    """
    Value object containing failure details.

    Captured when a test fails or errors.
    """

    message: str
    stack_trace: str | None = None
    failure_type: str | None = None

    @classmethod
    def from_exception(cls, exc: BaseException) -> "FailureInfo":
        """Create failure info from an exception."""
        import traceback

        return cls(
            message=str(exc),
            stack_trace="".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            ),
            failure_type=type(exc).__name__,
        )


@dataclass(frozen=True)
class Attachment:
    """
    Value object for result attachments.

    Attachments can be screenshots, logs, or other files
    associated with a test result.
    """

    name: str
    content_type: str
    url: str
    size_bytes: int


@dataclass
class Result:
    """
    Aggregate root for test results.

    Each result captures the outcome of executing a single test case
    within a specific test run. The case_snapshot preserves the state
    of the test case at execution time for historical accuracy.
    """

    id: ResultId
    run_id: RunId
    case_id: ExternalId
    case_snapshot: CaseSnapshot
    status: ResultStatus
    elapsed_ms: int | None = None
    failure_info: FailureInfo | None = None
    comment: str = ""
    attachments: list[Attachment] = field(default_factory=list)
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    recorded_by: str | None = None

    @classmethod
    def create(
        cls,
        run_id: RunId,
        case_snapshot: CaseSnapshot,
        status: ResultStatus,
        *,
        elapsed_ms: int | None = None,
        failure_info: FailureInfo | None = None,
        comment: str = "",
        recorded_by: str | None = None,
    ) -> "Result":
        """
        Factory method for creating new results.

        :param run_id: ID of the test run
        :param case_snapshot: Snapshot of the test case at execution time
        :param status: Outcome of the test
        :param elapsed_ms: Execution duration in milliseconds
        :param failure_info: Failure details if status is FAILED or ERROR
        :param comment: Optional comment about the result
        :param recorded_by: User or system that recorded the result
        :return: New Result instance
        """
        return cls(
            id=ResultId(uuid4()),
            run_id=run_id,
            case_id=case_snapshot.external_id,
            case_snapshot=case_snapshot,
            status=status,
            elapsed_ms=elapsed_ms,
            failure_info=failure_info,
            comment=comment,
            recorded_by=recorded_by,
        )

    @classmethod
    def passed(
        cls,
        run_id: RunId,
        case_snapshot: CaseSnapshot,
        *,
        elapsed_ms: int | None = None,
        recorded_by: str | None = None,
    ) -> "Result":
        """Convenience factory for passed results."""
        return cls.create(
            run_id=run_id,
            case_snapshot=case_snapshot,
            status=ResultStatus.PASSED,
            elapsed_ms=elapsed_ms,
            recorded_by=recorded_by,
        )

    @classmethod
    def failed(
        cls,
        run_id: RunId,
        case_snapshot: CaseSnapshot,
        failure_info: FailureInfo,
        *,
        elapsed_ms: int | None = None,
        recorded_by: str | None = None,
    ) -> "Result":
        """Convenience factory for failed results."""
        return cls.create(
            run_id=run_id,
            case_snapshot=case_snapshot,
            status=ResultStatus.FAILED,
            failure_info=failure_info,
            elapsed_ms=elapsed_ms,
            recorded_by=recorded_by,
        )

    @classmethod
    def skipped(
        cls,
        run_id: RunId,
        case_snapshot: CaseSnapshot,
        *,
        comment: str = "",
        recorded_by: str | None = None,
    ) -> "Result":
        """Convenience factory for skipped results."""
        return cls.create(
            run_id=run_id,
            case_snapshot=case_snapshot,
            status=ResultStatus.SKIPPED,
            comment=comment,
            recorded_by=recorded_by,
        )

    def add_attachment(self, attachment: Attachment) -> None:
        """
        Add an attachment to this result.

        :param attachment: Attachment to add
        """
        self.attachments.append(attachment)

    def add_comment(self, comment: str) -> None:
        """
        Add or update the comment.

        :param comment: Comment text
        """
        self.comment = comment

    @property
    def is_passing(self) -> bool:
        """Check if this result represents a passing test."""
        return self.status == ResultStatus.PASSED

    @property
    def is_failing(self) -> bool:
        """Check if this result represents a failing test."""
        return self.status in (ResultStatus.FAILED, ResultStatus.ERROR)

    @property
    def elapsed_seconds(self) -> float | None:
        """Get elapsed time in seconds."""
        if self.elapsed_ms is None:
            return None
        return self.elapsed_ms / 1000.0
