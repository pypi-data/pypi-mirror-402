"""Navigation bar widget."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Label


class NavBar(Widget):
    """Navigation bar with clickable tabs."""

    DEFAULT_CSS = """
    NavBar {
        dock: top;
        height: 3;
        background: $primary-darken-2;
        padding: 0 1;
    }

    NavBar Horizontal {
        height: 100%;
        align: left middle;
    }

    NavBar .nav-title {
        padding: 0 2;
        text-style: bold;
    }

    NavBar Button {
        min-width: 12;
        margin: 0 1;
    }

    NavBar Button.active {
        background: $primary;
    }

    NavBar .nav-spacer {
        width: 1fr;
    }

    NavBar .git-info {
        color: $text-muted;
        padding: 0 2;
    }
    """

    class TabClicked(Message):
        """Message sent when a tab is clicked."""

        def __init__(self, tab: str) -> None:
            self.tab = tab
            super().__init__()

    def __init__(
        self,
        active: str = "dashboard",
        project_name: str = "Testla",
        git_info: str = "",
    ) -> None:
        super().__init__()
        self._active = active
        self._project_name = project_name
        self._git_info = git_info

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(self._project_name, classes="nav-title")
            yield Button(
                "Dashboard",
                id="nav-dashboard",
                classes="active" if self._active == "dashboard" else "",
            )
            yield Button(
                "Cases",
                id="nav-cases",
                classes="active" if self._active == "cases" else "",
            )
            yield Label("", classes="nav-spacer")
            yield Label(self._git_info, id="nav-git-info", classes="git-info")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle tab button clicks."""
        if event.button.id == "nav-dashboard":
            self.post_message(self.TabClicked("dashboard"))
        elif event.button.id == "nav-cases":
            self.post_message(self.TabClicked("cases"))
