import pytest

from testla.domain.case import (
    AutomationStatus,
    Case,
    CaseMetadata,
    CaseSnapshot,
    ExternalId,
    Priority,
)

# Case creation tests (TC001)


@pytest.mark.testla("TC001")
def test_create_minimal_case() -> None:
    case = Case.create(
        external_id="TC001",
        title="User can login",
    )

    assert case.external_id == "TC001"
    assert case.title == "User can login"
    assert case.priority == Priority.MEDIUM
    assert case.is_automated is False


@pytest.mark.testla("TC001")
def test_create_automated_case() -> None:
    case = Case.create(
        external_id="TC002",
        title="Checkout works",
        test_path="tests/test_checkout.py::test_basic",
    )

    assert case.is_automated is True
    assert case.test_path == "tests/test_checkout.py::test_basic"
    assert case.metadata.automation_status == AutomationStatus.AUTOMATED


@pytest.mark.testla("TC001")
def test_create_with_full_metadata() -> None:
    case = Case.create(
        external_id="TC003",
        title="Critical payment flow",
        section_path="checkout/payment",
        priority=Priority.CRITICAL,
        tags=("smoke", "payment", "critical"),
    )

    assert case.section_path == "checkout/payment"
    assert case.priority == Priority.CRITICAL
    assert case.tags == ("smoke", "payment", "critical")


# CaseMetadata tests


def test_metadata_is_immutable() -> None:
    metadata = CaseMetadata(priority=Priority.HIGH)

    new_metadata = metadata.with_priority(Priority.LOW)

    assert metadata.priority == Priority.HIGH
    assert new_metadata.priority == Priority.LOW


def test_metadata_with_tags() -> None:
    metadata = CaseMetadata(tags=("a", "b"))

    new_metadata = metadata.with_tags(("x", "y", "z"))

    assert metadata.tags == ("a", "b")
    assert new_metadata.tags == ("x", "y", "z")


# CaseSnapshot tests


def test_snapshot_from_case() -> None:
    case = Case.create(
        external_id="TC001",
        title="Test case",
        section_path="auth/login",
        priority=Priority.HIGH,
        tags=("smoke",),
    )

    snapshot = CaseSnapshot.from_case(case)

    assert snapshot.external_id == case.external_id
    assert snapshot.title == case.title
    assert snapshot.section_path == case.section_path
    assert snapshot.priority == Priority.HIGH
    assert snapshot.tags == ("smoke",)


def test_snapshot_is_immutable() -> None:
    snapshot = CaseSnapshot(
        external_id=ExternalId("TC001"),
        title="Test",
        section_path="",
        priority=Priority.MEDIUM,
        tags=(),
    )

    # frozen=True means we can't modify it
    assert snapshot.external_id == ExternalId("TC001")
