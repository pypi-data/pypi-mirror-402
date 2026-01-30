"""Pytest plugin for Testla test case linking.

This plugin provides the @pytest.mark.testla() marker for linking
automated tests to test case documentation in .testla/cases/.

Usage:
    @pytest.mark.testla("TC001")
    def test_user_can_login():
        ...

    @pytest.mark.testla("TC001", "TC002")
    def test_covers_multiple_cases():
        ...
"""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest


@dataclass
class CaseResult:
    """Result tracking for a single test case."""

    case_id: str
    test_ids: list[str] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    skipped: int = 0

    @property
    def total(self) -> int:
        """Total number of test runs for this case."""
        return self.passed + self.failed + self.skipped

    @property
    def status(self) -> str:
        """Overall status for this case."""
        if self.failed > 0:
            return "FAILED"
        if self.passed > 0:
            return "PASSED"
        if self.skipped > 0:
            return "SKIPPED"
        return "UNKNOWN"


class TestlaPlugin:
    """
    Pytest plugin for tracking test results by Testla case ID.

    Collects tests marked with @pytest.mark.testla() and tracks
    their outcomes for reporting.
    """

    def __init__(self) -> None:
        self.case_results: dict[str, CaseResult] = {}
        self.known_case_ids: set[str] = set()
        self.root_path: Path | None = None
        self.validation_enabled: bool = True
        self.validation_errors: list[str] = []

    def _discover_cases(self, root_path: Path) -> None:
        """Load known case IDs from .testla/cases/."""
        try:
            from testla.repository.case_loader import CaseLoader

            loader = CaseLoader.discover(root_path)
            self.known_case_ids = {case.external_id for case in loader}
        except Exception:
            # If we can't load cases, disable validation
            self.validation_enabled = False

    def _find_testla_root(self, start_path: Path) -> Path | None:
        """Find the repository root containing testla/ directory."""
        from testla.repository.config import find_testla_root

        return find_testla_root(start_path)

    def _get_case_ids(self, item: pytest.Item) -> list[str]:
        """Extract case IDs from a test item's testla markers."""
        case_ids: list[str] = []
        for marker in item.iter_markers(name="testla"):
            case_ids.extend(marker.args)
        return case_ids

    def _get_or_create_result(self, case_id: str) -> CaseResult:
        """Get or create a CaseResult for a case ID."""
        if case_id not in self.case_results:
            self.case_results[case_id] = CaseResult(case_id=case_id)
        return self.case_results[case_id]

    @pytest.hookimpl
    def pytest_configure(self, config: pytest.Config) -> None:
        """Register the testla marker and initialize the plugin."""
        config.addinivalue_line(
            "markers",
            "testla(*case_ids): link test to Testla test case(s) by ID",
        )

        # Store plugin instance for access in hooks
        config._testla_plugin = self  # type: ignore[attr-defined]

        # Find .testla/ root
        root_path = self._find_testla_root(Path.cwd())
        if root_path:
            self.root_path = root_path
            self._discover_cases(root_path)

    @pytest.hookimpl
    def pytest_collection_modifyitems(
        self,
        config: pytest.Config,
        items: list[pytest.Item],
    ) -> None:
        """Validate case IDs at collection time."""
        del config  # unused but required by hook signature
        if not self.validation_enabled or not self.known_case_ids:
            return

        for item in items:
            case_ids = self._get_case_ids(item)
            for case_id in case_ids:
                if case_id not in self.known_case_ids:
                    self.validation_errors.append(
                        f"{item.nodeid}: unknown case ID '{case_id}'"
                    )

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(
        self,
        item: pytest.Item,
        call: pytest.CallInfo[Any],
    ) -> Generator[None, pytest.TestReport, None]:
        """Track test results per case ID."""
        del call  # unused but required by hook signature
        outcome = yield
        report = outcome.get_result()

        # Track results for the 'call' phase, or 'setup' phase if skipped
        # (skipped tests don't reach the call phase)
        is_call_phase = report.when == "call"
        is_setup_skip = report.when == "setup" and report.skipped

        if not (is_call_phase or is_setup_skip):
            return

        case_ids = self._get_case_ids(item)
        for case_id in case_ids:
            result = self._get_or_create_result(case_id)
            if item.nodeid not in result.test_ids:
                result.test_ids.append(item.nodeid)

            if report.passed:
                result.passed += 1
            elif report.failed:
                result.failed += 1
            elif report.skipped:
                result.skipped += 1

    @pytest.hookimpl
    def pytest_terminal_summary(
        self,
        terminalreporter: pytest.TerminalReporter,
        exitstatus: int,
    ) -> None:
        """Print testla summary report."""
        del exitstatus  # unused but required by hook signature
        if not self.case_results and not self.validation_errors:
            return

        terminalreporter.ensure_newline()
        terminalreporter.section("Testla Test Case Report")

        # Show validation errors first
        if self.validation_errors:
            terminalreporter.write_line("")
            terminalreporter.write_line("Validation warnings:", yellow=True)
            for error in self.validation_errors:
                terminalreporter.write_line(f"  {error}", yellow=True)
            terminalreporter.write_line("")

        if not self.case_results:
            terminalreporter.write_line("No tests with @pytest.mark.testla() found.")
            return

        # Summary table
        terminalreporter.write_line("")
        terminalreporter.write_line(
            f"{'Case ID':<12} {'Status':<8} {'Tests':<6} {'Pass':<6} {'Fail':<6} {'Skip':<6}"
        )
        terminalreporter.write_line("-" * 56)

        passed_cases = 0
        failed_cases = 0

        for case_id in sorted(self.case_results.keys()):
            result = self.case_results[case_id]
            status = result.status

            if status == "PASSED":
                passed_cases += 1
                status_color = {"green": True}
            elif status == "FAILED":
                failed_cases += 1
                status_color = {"red": True}
            else:
                status_color = {"yellow": True}

            line = f"{case_id:<12} "
            terminalreporter.write(line)
            terminalreporter.write(f"{status:<8} ", **status_color)
            terminalreporter.write_line(
                f"{result.total:<6} {result.passed:<6} {result.failed:<6} {result.skipped:<6}"
            )

        terminalreporter.write_line("-" * 56)
        total_cases = len(self.case_results)
        terminalreporter.write_line(
            f"Total: {total_cases} cases ({passed_cases} passed, {failed_cases} failed)"
        )

        # Coverage info if we know about cases
        if self.known_case_ids:
            automated = len(self.known_case_ids & set(self.case_results.keys()))
            total_known = len(self.known_case_ids)
            coverage = (automated / total_known * 100) if total_known > 0 else 0
            terminalreporter.write_line(
                f"Coverage: {automated}/{total_known} cases automated ({coverage:.0f}%)"
            )


# Storage for plugin instance (one per pytest session)
_plugin: TestlaPlugin | None = None


def pytest_configure(config: pytest.Config) -> None:
    """Create and configure a fresh plugin instance for this session."""
    global _plugin
    _plugin = TestlaPlugin()
    _plugin.pytest_configure(config)


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Delegate to plugin instance."""
    if _plugin is not None:
        _plugin.pytest_collection_modifyitems(config, items)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item,
    call: pytest.CallInfo[Any],
) -> Generator[None, pytest.TestReport, None]:
    """Delegate to plugin instance."""
    if _plugin is not None:
        yield from _plugin.pytest_runtest_makereport(item, call)
    else:
        yield


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter,
    exitstatus: int,
) -> None:
    """Delegate to plugin instance."""
    if _plugin is not None:
        _plugin.pytest_terminal_summary(terminalreporter, exitstatus)


def pytest_unconfigure(config: pytest.Config) -> None:
    """Clean up plugin instance at session end."""
    global _plugin
    del config  # unused but required by hook signature
    _plugin = None
