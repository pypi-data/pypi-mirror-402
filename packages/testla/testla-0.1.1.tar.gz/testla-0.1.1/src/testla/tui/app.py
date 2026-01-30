"""Testla TUI Application."""

from typing import ClassVar

from textual.app import App
from textual.binding import Binding, BindingType

from testla.repository.case_loader import CaseLoader
from testla.repository.config import TestlaConfig


class TestlaApp(App[None]):
    """Testla TUI Application."""

    CSS_PATH = "styles.tcss"
    TITLE = "Testla"

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("q", "quit", "Quit", show=True, priority=True),
        Binding("question_mark", "help", "Help", show=True),
        Binding("c", "cases", "Cases", show=True),
        Binding("d", "dashboard", "Dashboard", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config = TestlaConfig.load()
        self._case_loader: CaseLoader | None = None

    @property
    def case_loader(self) -> CaseLoader:
        """Lazy-load case loader."""
        if self._case_loader is None:
            self._case_loader = CaseLoader.discover()
        return self._case_loader

    def reload_cases(self) -> None:
        """Reload cases from disk."""
        self._case_loader = CaseLoader.discover()

    def on_mount(self) -> None:
        """Mount the dashboard screen on startup."""
        from testla.tui.screens.dashboard import DashboardScreen

        self.push_screen(DashboardScreen())

    def action_cases(self) -> None:
        """Navigate to case browser."""
        from testla.tui.screens.cases import CaseBrowserScreen

        self.push_screen(CaseBrowserScreen())

    def action_dashboard(self) -> None:
        """Navigate to dashboard."""
        from testla.tui.screens.dashboard import DashboardScreen

        # Pop screens until we reach the dashboard
        while len(self.screen_stack) > 1:
            if isinstance(self.screen, DashboardScreen):
                break
            self.pop_screen()

    def action_help(self) -> None:
        """Show help screen."""
        # TODO: Implement help screen
        self.notify("Help: Press 'c' for cases, 'd' for dashboard, 'q' to quit")


def main() -> None:
    """Entry point for the TUI."""
    app = TestlaApp()
    app.run()
