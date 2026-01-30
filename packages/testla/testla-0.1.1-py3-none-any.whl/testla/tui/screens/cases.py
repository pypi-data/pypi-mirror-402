"""Case browser screen - Tree view with case details."""

import os
import re
import shlex
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Static, Tree
from textual.widgets.tree import TreeNode

from testla.domain.case import AutomationStatus, Case
from testla.tui.modals.input import InputModal
from testla.tui.widgets.nav import NavBar


class CaseDetailPanel(VerticalScroll):
    """Panel showing details of the selected case."""

    def compose(self) -> ComposeResult:
        yield Static("Select a case to view details", id="case-detail-content")

    def show_case(self, case: Case) -> None:
        """Display details for the given case."""
        content = self.query_one("#case-detail-content", Static)

        # Build the detail view
        auto_indicator = (
            "automated"
            if case.metadata.automation_status == AutomationStatus.AUTOMATED
            else "manual"
        )
        priority_class = f"priority-{case.priority.value}"

        lines = [
            f"[bold]{case.external_id}[/bold] - {case.title}",
            "",
            f"[{priority_class}]Priority: {case.priority.value}[/{priority_class}]",
            f"Status: [{auto_indicator}]{auto_indicator}[/{auto_indicator}]",
        ]

        if case.tags:
            lines.append(f"Tags: {', '.join(case.tags)}")

        if case.description:
            lines.extend(["", "[bold]Description[/bold]", case.description])

        if case.preconditions:
            lines.extend(["", "[bold]Preconditions[/bold]", case.preconditions])

        if case.steps:
            lines.extend(["", "[bold]Steps[/bold]", case.steps])

        if case.expected_result:
            lines.extend(["", "[bold]Expected Result[/bold]", case.expected_result])

        if case.test_path:
            lines.extend(["", "[bold]Linked Test[/bold]", case.test_path])

        content.update("\n".join(lines))

    def clear(self) -> None:
        """Clear the detail panel."""
        content = self.query_one("#case-detail-content", Static)
        content.update("Select a case to view details")


class CaseBrowserScreen(Screen[None]):
    """Case browser with tree view and detail panel."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "app.dashboard", "Dashboard", show=True),
        Binding("n", "new_case", "New", show=True),
        Binding("e", "edit_case", "Edit", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("slash", "focus_filter", "Filter", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._cases_by_id: dict[str, Case] = {}
        self._selected_case: Case | None = None
        self._selected_section: str = ""

    def compose(self) -> ComposeResult:
        config = self.app.config  # type: ignore[attr-defined]
        yield NavBar(
            active="cases",
            project_name=config.project_name,
            git_info=self._get_git_info(),
        )
        yield Container(
            Horizontal(
                Container(
                    Tree("Cases", id="case-tree"),
                    classes="case-tree-container",
                ),
                Container(
                    CaseDetailPanel(classes="case-detail"),
                    classes="case-detail-container",
                ),
                classes="case-browser",
            ),
        )
        yield Footer()

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

    def on_mount(self) -> None:
        """Build the case tree on mount."""
        self._build_tree()

    def on_nav_bar_tab_clicked(self, event: NavBar.TabClicked) -> None:
        """Handle navigation tab clicks."""
        if event.tab == "dashboard":
            self.app.action_dashboard()  # type: ignore[attr-defined]

    def action_refresh(self) -> None:
        """Refresh cases from disk."""
        self.app.reload_cases()  # type: ignore[attr-defined]
        self._build_tree()
        self.query_one(CaseDetailPanel).clear()
        self.notify("Cases reloaded")

    def action_edit_case(self) -> None:
        """Open selected case in external editor."""
        if not self._selected_case or not self._selected_case.file_path:
            self.notify("No case selected", severity="warning")
            return

        editor_cmd = shlex.split(os.environ.get("EDITOR", "vi"))
        file_path = self._selected_case.file_path

        # Suspend TUI and open editor
        with self.app.suspend():
            subprocess.run([*editor_cmd, file_path], check=False)

        # Reload the case after editing
        self.app.reload_cases()  # type: ignore[attr-defined]
        self._build_tree()
        self.notify(f"Edited {self._selected_case.external_id}")

    def action_focus_filter(self) -> None:
        """Focus the filter input."""
        # TODO: Implement filter input
        self.notify("Filter: not yet implemented")

    def _build_tree(self) -> None:
        """Build the case tree from loaded cases."""
        tree = self.query_one("#case-tree", Tree)
        tree.clear()
        tree.root.expand()

        loader = self.app.case_loader  # type: ignore[attr-defined]
        cases = list(loader)
        self._cases_by_id.clear()

        # Group cases by section path
        sections: dict[str, list[Case]] = defaultdict(list)
        for case in cases:
            sections[case.section_path or ""].append(case)

        # Sort sections
        sorted_sections = sorted(sections.keys())

        for section in sorted_sections:
            section_cases = sorted(sections[section], key=lambda c: c.external_id)

            if section:
                # Create folder node
                folder_node = tree.root.add(
                    f"{section}/ ({len(section_cases)})",
                    expand=True,
                )
                parent = folder_node
            else:
                parent = tree.root

            # Add cases to section
            for case in section_cases:
                self._cases_by_id[str(case.external_id)] = case
                indicator = (
                    "[green]●[/green]"
                    if case.metadata.automation_status == AutomationStatus.AUTOMATED
                    else "[dim]○[/dim]"
                )
                label = f"{indicator} {case.external_id} {case.title[:30]}"
                parent.add_leaf(label, data=str(case.external_id))

    def on_tree_node_selected(self, event: Tree.NodeSelected[str]) -> None:
        """Handle case selection in tree."""
        node: TreeNode[str] = event.node

        # Track selected section from folder nodes
        if node.data is None and node.label:
            # It's a folder node - extract section name
            label_text = str(node.label)
            if "/" in label_text:
                self._selected_section = label_text.split("/")[0].strip()
            else:
                self._selected_section = ""
        elif node.data and node.data in self._cases_by_id:
            case = self._cases_by_id[node.data]
            self._selected_case = case
            self._selected_section = case.section_path
            self.query_one(CaseDetailPanel).show_case(case)

    def action_new_case(self) -> None:
        """Create a new test case."""

        def handle_title(title: str | None) -> None:
            if title:
                self._create_case(title)

        self.app.push_screen(
            InputModal("New Case Title:", placeholder="e.g., User can login"),
            handle_title,
        )

    def _create_case(self, title: str) -> None:
        """Create a new case file and open in editor."""
        config = self.app.config  # type: ignore[attr-defined]
        cases_dir = Path.cwd() / config.cases_dir

        # Find next available ID
        loader = self.app.case_loader  # type: ignore[attr-defined]
        existing_ids = {c.external_id for c in loader}
        sequence = 1
        while config.generate_case_id(sequence) in existing_ids:
            sequence += 1
        case_id = config.generate_case_id(sequence)

        # Determine target directory
        if self._selected_section:
            case_dir = cases_dir / self._selected_section
            case_dir.mkdir(parents=True, exist_ok=True)
        else:
            case_dir = cases_dir

        # Create filename
        filename = f"{case_id}-{self._slugify(title)}.md"
        file_path = case_dir / filename

        # Get section names based on configured format
        section_names = config.section_names

        # Create case content
        content = f"""---
id: {case_id}
title: {title}
priority: medium
tags: []
automation:
  status: none
---

## Description

<!-- Describe what this test case verifies -->

## {section_names["preconditions"]}

<!-- List any required state or setup -->

## {section_names["steps"]}

1. <!-- First step -->
2. <!-- Second step -->

## {section_names["expected"]}

<!-- Describe the expected outcome -->
"""

        file_path.write_text(content)
        self.notify(f"Created {case_id}")

        # Open in editor
        editor_cmd = shlex.split(os.environ.get("EDITOR", "vi"))
        with self.app.suspend():
            subprocess.run([*editor_cmd, str(file_path)], check=False)

        # Reload cases
        self.app.reload_cases()  # type: ignore[attr-defined]
        self._build_tree()

    def _slugify(self, text: str) -> str:
        """Convert text to a URL-friendly slug."""
        text = text.lower()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[-\s]+", "-", text)
        return text.strip("-")
