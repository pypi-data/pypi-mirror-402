"""Tests for the TUI application."""

import pytest

from testla.tui.app import TestlaApp
from testla.tui.screens.cases import CaseBrowserScreen, CaseDetailPanel
from testla.tui.screens.dashboard import DashboardScreen


@pytest.mark.testla("TC006")
async def test_app_launches_with_dashboard() -> None:
    """Test that the app launches and shows the dashboard screen."""
    async with TestlaApp().run_test() as pilot:
        # Wait for mount to complete
        await pilot.pause()

        app = pilot.app

        # Verify app is running
        assert app.is_running

        # Verify dashboard is shown (it's pushed on mount)
        assert isinstance(app.screen, DashboardScreen)


@pytest.mark.testla("TC010")
async def test_dashboard_shows_stats() -> None:
    """Test that the dashboard displays case statistics."""
    async with TestlaApp().run_test() as pilot:
        # Wait for mount to complete
        await pilot.pause()

        screen = pilot.app.screen

        # Query stats labels from the screen
        total_label = screen.query_one("#stat-total")
        auto_label = screen.query_one("#stat-automated")
        linked_label = screen.query_one("#stat-linked")

        # Stats should be rendered (values depend on test case files)
        assert total_label is not None
        assert auto_label is not None
        assert linked_label is not None


@pytest.mark.testla("TC007")
async def test_navigate_to_cases() -> None:
    """Test navigation from dashboard to case browser."""
    async with TestlaApp().run_test() as pilot:
        await pilot.pause()

        # Press 'c' to navigate to cases
        await pilot.press("c")
        await pilot.pause()

        assert isinstance(pilot.app.screen, CaseBrowserScreen)


async def test_navigate_back_to_dashboard() -> None:
    """Test navigation from case browser back to dashboard."""
    async with TestlaApp().run_test() as pilot:
        await pilot.pause()

        # Navigate to cases first
        await pilot.press("c")
        await pilot.pause()
        assert isinstance(pilot.app.screen, CaseBrowserScreen)

        # Press 'd' to go to dashboard (escape triggers app.dashboard action)
        await pilot.press("d")
        await pilot.pause()

        assert isinstance(pilot.app.screen, DashboardScreen)


@pytest.mark.testla("TC007")
async def test_case_browser_shows_tree() -> None:
    """Test that the case browser displays a tree of cases."""
    async with TestlaApp().run_test() as pilot:
        await pilot.pause()

        # Navigate to cases
        await pilot.press("c")
        await pilot.pause()

        # Query the case tree widget
        from textual.widgets import Tree

        tree = pilot.app.screen.query_one("#case-tree", Tree)
        assert tree is not None

        # Tree should have root expanded
        assert tree.root.is_expanded


@pytest.mark.testla("TC008")
async def test_case_browser_shows_detail_panel() -> None:
    """Test that the case browser has a detail panel."""
    async with TestlaApp().run_test() as pilot:
        await pilot.pause()

        # Navigate to cases
        await pilot.press("c")
        await pilot.pause()

        # Query the detail panel
        detail_panel = pilot.app.screen.query_one(CaseDetailPanel)
        assert detail_panel is not None


async def test_app_quits_on_q() -> None:
    """Test that pressing 'q' quits the app."""
    async with TestlaApp().run_test() as pilot:
        await pilot.pause()
        await pilot.press("q")

        # App should be exiting
        assert not pilot.app.is_running


async def test_dashboard_refresh() -> None:
    """Test that pressing 'r' on dashboard triggers refresh."""
    async with TestlaApp().run_test() as pilot:
        await pilot.pause()

        # Press 'r' to refresh
        await pilot.press("r")
        await pilot.pause()

        # Should still be on dashboard and show notification
        assert isinstance(pilot.app.screen, DashboardScreen)


async def test_case_browser_refresh() -> None:
    """Test that pressing 'r' on case browser triggers refresh."""
    async with TestlaApp().run_test() as pilot:
        await pilot.pause()

        # Navigate to cases
        await pilot.press("c")
        await pilot.pause()

        # Press 'r' to refresh
        await pilot.press("r")
        await pilot.pause()

        # Should still be on case browser
        assert isinstance(pilot.app.screen, CaseBrowserScreen)
