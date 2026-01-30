"""Dashboard screen - Home view with stats and overview."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Label, ProgressBar, Static

from testla.domain.case import AutomationStatus
from testla.tui.widgets.nav import NavBar


class QuickStatsPanel(Static):
    """Panel displaying quick stats about test cases."""

    def compose(self) -> ComposeResult:
        yield Label("Quick Stats", classes="panel-title")
        yield Horizontal(
            Label("Total Cases", classes="stats-label"),
            Label("0", id="stat-total", classes="stats-value"),
        )
        yield Horizontal(
            Label("Automated", classes="stats-label"),
            Label("0", id="stat-automated", classes="stats-value"),
        )
        yield Horizontal(
            Label("Linked Tests", classes="stats-label"),
            Label("0", id="stat-linked", classes="stats-value"),
        )


class CoveragePanel(Static):
    """Panel displaying automation coverage with progress bars."""

    def compose(self) -> ComposeResult:
        yield Label("Automation Coverage", classes="panel-title")
        yield Horizontal(
            Label("Automated", classes="stats-label"),
            ProgressBar(total=100, show_eta=False, id="coverage-automated"),
        )
        yield Horizontal(
            Label("Manual", classes="stats-label"),
            ProgressBar(total=100, show_eta=False, id="coverage-manual"),
        )


class DashboardScreen(Screen[None]):
    """Dashboard home screen with project overview."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("c", "app.cases", "Cases", show=True),
        Binding("r", "refresh", "Refresh", show=True),
    ]

    def compose(self) -> ComposeResult:
        config = self.app.config  # type: ignore[attr-defined]
        git_info = self._get_git_info()
        yield NavBar(
            active="dashboard",
            project_name=config.project_name,
            git_info=git_info,
        )
        yield Container(
            Vertical(
                Horizontal(
                    Container(
                        QuickStatsPanel(classes="panel stats-panel"),
                        classes="dashboard-stats",
                    ),
                    Container(
                        CoveragePanel(classes="panel stats-panel"),
                        classes="dashboard-coverage",
                    ),
                    classes="dashboard-top",
                ),
                classes="dashboard",
            ),
        )
        yield Footer()

    def on_mount(self) -> None:
        """Load and display stats on mount."""
        self._update_stats()

    def on_nav_bar_tab_clicked(self, event: NavBar.TabClicked) -> None:
        """Handle navigation tab clicks."""
        if event.tab == "cases":
            self.app.action_cases()  # type: ignore[attr-defined]

    def action_refresh(self) -> None:
        """Refresh stats from disk."""
        self.app.reload_cases()  # type: ignore[attr-defined]
        self._update_stats()
        self.notify("Cases reloaded")

    def _get_git_info(self) -> str:
        """Get current git branch and short SHA."""
        import subprocess

        try:
            branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

            sha = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ""
        else:
            return f"{branch} @ {sha}"

    def _update_stats(self) -> None:
        """Update statistics display."""
        loader = self.app.case_loader  # type: ignore[attr-defined]
        cases = list(loader)

        total = len(cases)
        automated = sum(
            1 for c in cases if c.metadata.automation_status == AutomationStatus.AUTOMATED
        )
        linked = sum(1 for c in cases if c.test_path)

        # Update quick stats
        self.query_one("#stat-total", Label).update(str(total))
        self.query_one("#stat-automated", Label).update(str(automated))
        self.query_one("#stat-linked", Label).update(str(linked))

        # Update coverage bars
        if total > 0:
            auto_pct = int((automated / total) * 100)
            manual_pct = 100 - auto_pct
        else:
            auto_pct = 0
            manual_pct = 0

        self.query_one("#coverage-automated", ProgressBar).update(progress=auto_pct)
        self.query_one("#coverage-manual", ProgressBar).update(progress=manual_pct)
