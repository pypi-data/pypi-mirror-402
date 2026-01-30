"""Tests for the pytest plugin."""

from __future__ import annotations

import pytest

pytest_plugins = ["pytester"]


# Marker registration tests (TC003)


@pytest.mark.testla("TC003")
def test_marker_is_registered(pytester: pytest.Pytester) -> None:
    """Verify the testla marker is registered."""
    result = pytester.runpytest("--markers")
    result.stdout.fnmatch_lines(["*@pytest.mark.testla(*case_ids)*"])


@pytest.mark.testla("TC003")
def test_no_unknown_marker_warning(pytester: pytest.Pytester) -> None:
    """Tests with @pytest.mark.testla should not trigger unknown marker warning."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.testla("TC001")
        def test_with_marker():
            assert True
        """
    )
    result = pytester.runpytest("-W", "error::pytest.PytestUnknownMarkWarning")
    result.assert_outcomes(passed=1)


# Report output tests (TC004)


@pytest.mark.testla("TC004")
def test_report_shows_case_results(pytester: pytest.Pytester) -> None:
    """Report should show case IDs with pass/fail status."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.testla("TC001")
        def test_passing():
            assert True

        @pytest.mark.testla("TC002")
        def test_failing():
            assert False
        """
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*Testla Test Case Report*",
            "*TC001*PASSED*",
            "*TC002*FAILED*",
        ]
    )


@pytest.mark.testla("TC004")
def test_report_multiple_cases_per_test(pytester: pytest.Pytester) -> None:
    """Tests can link to multiple case IDs."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.testla("TC001", "TC002")
        def test_covers_multiple():
            assert True
        """
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*TC001*PASSED*",
            "*TC002*PASSED*",
        ]
    )


@pytest.mark.testla("TC004")
def test_report_multiple_tests_per_case(pytester: pytest.Pytester) -> None:
    """Multiple tests can link to the same case ID."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.testla("TC001")
        def test_first():
            assert True

        @pytest.mark.testla("TC001")
        def test_second():
            assert True
        """
    )
    result = pytester.runpytest("-v")
    # Should show TC001 with 2 passes
    result.stdout.fnmatch_lines(
        [
            "*TC001*PASSED*2*",
        ]
    )


@pytest.mark.testla("TC004")
def test_no_report_without_markers(pytester: pytest.Pytester) -> None:
    """No report section if no tests have testla markers."""
    pytester.makepyfile(
        """
        def test_without_marker():
            assert True
        """
    )
    result = pytester.runpytest("-v")
    assert "Testla Test Case Report" not in result.stdout.str()


@pytest.mark.testla("TC004")
def test_skipped_tests_tracked(pytester: pytest.Pytester) -> None:
    """Skipped tests should be tracked in the report."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.testla("TC001")
        @pytest.mark.skip(reason="not ready")
        def test_skipped():
            assert True
        """
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*TC001*SKIPPED*",
        ]
    )


# Marker filtering tests


def test_filter_by_marker(pytester: pytest.Pytester) -> None:
    """pytest -m testla should run only marked tests."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.testla("TC001")
        def test_with_marker():
            assert True

        def test_without_marker():
            assert True
        """
    )
    result = pytester.runpytest("-m", "testla", "-v")
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(["*test_with_marker*"])
    assert "test_without_marker" not in result.stdout.str()


# Case ID validation tests (TC005)


@pytest.mark.testla("TC005")
def test_warns_on_unknown_case_id(pytester: pytest.Pytester) -> None:
    """Plugin should warn when a case ID doesn't exist in testla/cases/."""
    # Create testla/cases/ structure
    testla_dir = pytester.mkdir("testla")
    cases_dir = testla_dir / "cases"
    cases_dir.mkdir()

    # Create pyproject.toml with [tool.testla]
    pytester.makefile(
        ".toml",
        pyproject="""
[tool.testla]
project_name = "Test"
""",
    )

    # Create one case file
    case_file = cases_dir / "TC001-existing.md"
    case_file.write_text(
        """---
id: TC001
title: Existing case
priority: medium
---

## Description
This case exists.
"""
    )

    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.testla("TC001")
        def test_existing_case():
            assert True

        @pytest.mark.testla("TC999")
        def test_unknown_case():
            assert True
        """
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*Validation warnings*",
            "*unknown case ID 'TC999'*",
        ]
    )
