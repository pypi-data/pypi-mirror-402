"""Simple input modal."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class InputModal(ModalScreen[str | None]):
    """Modal for getting text input from user."""

    DEFAULT_CSS = """
    InputModal {
        align: center middle;
    }

    InputModal > Vertical {
        width: 60;
        height: auto;
        padding: 1 2;
        background: $surface;
        border: solid $primary;
    }

    InputModal Label {
        margin-bottom: 1;
    }

    InputModal Input {
        margin-bottom: 1;
    }

    InputModal Button {
        margin-top: 1;
        width: 100%;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, prompt: str, placeholder: str = "") -> None:
        super().__init__()
        self._prompt = prompt
        self._placeholder = placeholder

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self._prompt)
            yield Input(placeholder=self._placeholder, id="input-field")
            yield Button("Create", variant="primary", id="submit-btn")

    def on_mount(self) -> None:
        """Focus the input field on mount."""
        self.query_one("#input-field", Input).focus()

    def on_input_submitted(self, _event: Input.Submitted) -> None:
        """Handle Enter key in input field."""
        self._submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button click."""
        if event.button.id == "submit-btn":
            self._submit()

    def _submit(self) -> None:
        """Submit the input value."""
        value = self.query_one("#input-field", Input).value.strip()
        if value:
            self.dismiss(value)
        else:
            self.notify("Please enter a value", severity="warning")

    def action_cancel(self) -> None:
        """Cancel the modal."""
        self.dismiss(None)
