from uuid import uuid4

import pytest

from testla.domain.case import CaseSnapshot, ExternalId, Priority
from testla.domain.project import Project, ProjectId
from testla.domain.result import FailureInfo, Result, ResultStatus
from testla.domain.run import (
    GitContext,
    Run,
    RunId,
    RunStatus,
)

# Project creation tests


def test_create_minimal_project() -> None:
    project = Project.create(name="My Project")

    assert project.name == "My Project"
    assert project.repo_url is None


def test_create_project_with_repo_url() -> None:
    project = Project.create(
        name="My Project",
        repo_url="https://github.com/user/repo",
    )

    assert project.repo_url == "https://github.com/user/repo"


# Run tests (TC002)


@pytest.mark.testla("TC002")
def test_create_run() -> None:
    project_id = ProjectId(uuid4())
    run = Run.create(
        project_id=project_id,
        name="Nightly regression",
    )

    assert run.name == "Nightly regression"
    assert run.status == RunStatus.PENDING
    assert run.total_count == 0


@pytest.mark.testla("TC002")
def test_run_lifecycle() -> None:
    project_id = ProjectId(uuid4())
    run = Run.create(project_id=project_id, name="Test")

    assert run.status == RunStatus.PENDING

    run.start()
    assert run.status == RunStatus.RUNNING  # type: ignore[comparison-overlap]
    assert run.started_at is not None

    run.complete()
    assert run.status == RunStatus.COMPLETED
    assert run.completed_at is not None


@pytest.mark.testla("TC002")
def test_run_with_git_context() -> None:
    project_id = ProjectId(uuid4())
    git_ctx = GitContext(
        branch="main",
        commit_sha="abc1234567890",
        is_dirty=False,
    )

    run = Run.create(
        project_id=project_id,
        name="PR Test",
        git_context=git_ctx,
    )

    assert run.git_context is not None
    assert run.git_context.ref == "main@abc1234"


@pytest.mark.testla("TC002")
def test_run_statistics() -> None:
    project_id = ProjectId(uuid4())
    run = Run.create(project_id=project_id, name="Test")

    run.record_result_counts(passed=8, failed=2)

    assert run.total_count == 10
    assert run.passed_count == 8
    assert run.failed_count == 2
    assert run.pass_rate == 80.0
    assert run.is_passing is False


# Result tests


def test_create_passed_result() -> None:
    run_id = RunId(uuid4())
    snapshot = CaseSnapshot(
        external_id=ExternalId("TC001"),
        title="Test",
        section_path="",
        priority=Priority.MEDIUM,
        tags=(),
    )

    result = Result.passed(
        run_id=run_id,
        case_snapshot=snapshot,
        elapsed_ms=1234,
    )

    assert result.status == ResultStatus.PASSED
    assert result.is_passing is True
    assert result.elapsed_ms == 1234
    assert result.elapsed_seconds == 1.234


def test_create_failed_result() -> None:
    run_id = RunId(uuid4())
    snapshot = CaseSnapshot(
        external_id=ExternalId("TC001"),
        title="Test",
        section_path="",
        priority=Priority.MEDIUM,
        tags=(),
    )
    failure = FailureInfo(
        message="AssertionError: expected True",
        failure_type="AssertionError",
    )

    result = Result.failed(
        run_id=run_id,
        case_snapshot=snapshot,
        failure_info=failure,
    )

    assert result.status == ResultStatus.FAILED
    assert result.is_failing is True
    assert result.failure_info is not None
    assert result.failure_info.message == "AssertionError: expected True"


# GitContext tests


def test_git_context_ref_with_branch_and_sha() -> None:
    ctx = GitContext(branch="feature/test", commit_sha="abc1234567890")
    assert ctx.ref == "feature/test@abc1234"


def test_git_context_ref_with_tag() -> None:
    ctx = GitContext(tag="v1.0.0", commit_sha="abc1234567890")
    assert ctx.ref == "v1.0.0"


def test_git_context_ref_dirty() -> None:
    ctx = GitContext(branch="main", commit_sha="abc1234567890", is_dirty=True)
    assert ctx.ref == "main@abc1234 (dirty)"
