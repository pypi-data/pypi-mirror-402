"""Testla domain models."""

from testla.domain.case import (
    AutomationStatus,
    Case,
    CaseId,
    CaseMetadata,
    CaseSnapshot,
    ExternalId,
    Priority,
)
from testla.domain.project import Project, ProjectId
from testla.domain.result import Result, ResultId, ResultStatus
from testla.domain.run import Run, RunId, RunStatus

__all__ = [
    "AutomationStatus",
    "Case",
    "CaseId",
    "CaseMetadata",
    "CaseSnapshot",
    "ExternalId",
    "Priority",
    "Project",
    "ProjectId",
    "Result",
    "ResultId",
    "ResultStatus",
    "Run",
    "RunId",
    "RunStatus",
]
