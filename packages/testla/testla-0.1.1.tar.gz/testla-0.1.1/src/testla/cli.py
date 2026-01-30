"""Testla CLI - Git-native test case management."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from testla.repository.case_loader import CaseLoader
from testla.repository.config import TestlaConfig

app = typer.Typer(
    name="testla",
    help="Git-native test case management for modern development workflows.",
    no_args_is_help=True,
)
console = Console()

# Sub-command groups
case_app = typer.Typer(help="Manage test cases")
run_app = typer.Typer(help="Manage test runs")
config_app = typer.Typer(help="Manage configuration")

app.add_typer(case_app, name="case")
app.add_typer(run_app, name="run")
app.add_typer(config_app, name="config")


@app.command()
def init(
    project_name: str = typer.Option(None, "--name", "-n", help="Project name"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing configuration"
    ),
) -> None:
    """Initialize Testla in the current repository."""
    testla_dir = Path.cwd() / "testla"
    cases_dir = testla_dir / "cases"
    pyproject_path = Path.cwd() / "pyproject.toml"

    # Check if already initialized
    if testla_dir.exists() and not force:
        console.print(
            "[yellow]Testla is already initialized. Use --force to overwrite.[/]"
        )
        raise typer.Exit(1)

    # Create directory structure
    testla_dir.mkdir(exist_ok=True)
    cases_dir.mkdir(exist_ok=True)

    # Determine project name
    if project_name is None:
        project_name = Path.cwd().name

    # Create or update pyproject.toml
    config = TestlaConfig(project_name=project_name)
    toml_section = config.to_toml_section()

    if pyproject_path.exists():
        # Append to existing pyproject.toml if [tool.testla] not present
        content = pyproject_path.read_text()
        if "[tool.testla]" in content:
            if not force:
                console.print(
                    "[yellow][tool.testla] already exists in pyproject.toml. "
                    "Use --force to overwrite.[/]"
                )
                raise typer.Exit(1)
            # For simplicity, we don't modify existing config - user should edit manually
            console.print(
                "[yellow]Note: Existing [tool.testla] config preserved. "
                "Edit pyproject.toml to update settings.[/]"
            )
        else:
            # Append the new section
            content = content.rstrip() + "\n\n" + toml_section + "\n"
            pyproject_path.write_text(content)
            console.print(f"  Updated: {pyproject_path}")
    else:
        # Create minimal pyproject.toml
        content = toml_section + "\n"
        pyproject_path.write_text(content)
        console.print(f"  Created: {pyproject_path}")

    console.print(f"[green]✓[/] Initialized Testla for [bold]{project_name}[/]")
    console.print(f"  Created: {cases_dir}/")
    console.print()
    console.print("Next steps:")
    console.print("  1. Add test cases: [bold]testla case new[/]")
    console.print("  2. Run tests with: [bold]pytest -m testla[/]")


@app.command()
def tui() -> None:
    """Launch the interactive TUI."""
    from testla.tui.app import main as tui_main

    tui_main()


@case_app.command("list")
def case_list(
    section: str = typer.Option(None, "--section", "-s", help="Filter by section"),
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    automated: bool = typer.Option(None, "--automated", help="Filter automated only"),
) -> None:
    """List all test cases."""
    try:
        loader = CaseLoader.discover()
    except FileNotFoundError:
        console.print("[red]Testla not initialized. Run 'testla init' first.[/]")
        raise typer.Exit(1) from None

    cases = list(loader)

    # Apply filters
    if section:
        cases = [c for c in cases if c.section_path.startswith(section)]
    if tag:
        cases = [c for c in cases if tag in c.tags]
    if automated is not None:
        cases = [c for c in cases if c.is_automated == automated]

    if not cases:
        console.print("[yellow]No test cases found.[/]")
        return

    table = Table(title=f"Test Cases ({len(cases)})")
    table.add_column("ID", style="cyan")
    table.add_column("Title")
    table.add_column("Section", style="dim")
    table.add_column("Priority")
    table.add_column("Auto", justify="center")

    for case in sorted(cases, key=lambda c: c.external_id):
        auto_icon = "✓" if case.is_automated else ""
        priority_style = {
            "critical": "red bold",
            "high": "red",
            "medium": "yellow",
            "low": "dim",
        }.get(case.priority.value, "")

        table.add_row(
            case.external_id,
            case.title[:50],
            case.section_path or "-",
            f"[{priority_style}]{case.priority.value}[/]",
            auto_icon,
        )

    console.print(table)


@case_app.command("show")
def case_show(
    case_id: str = typer.Argument(..., help="Case ID to show"),
) -> None:
    """Show details of a test case."""
    try:
        loader = CaseLoader.discover()
    except FileNotFoundError:
        console.print("[red]Testla not initialized. Run 'testla init' first.[/]")
        raise typer.Exit(1) from None

    case = loader.get(case_id)
    if not case:
        console.print(f"[red]Case '{case_id}' not found.[/]")
        raise typer.Exit(1)

    console.print(f"[bold cyan]{case.external_id}[/] - {case.title}")
    console.print()

    if case.section_path:
        console.print(f"[dim]Section:[/] {case.section_path}")
    console.print(f"[dim]Priority:[/] {case.priority.value}")
    console.print(f"[dim]Tags:[/] {', '.join(case.tags) or 'none'}")
    console.print(f"[dim]Automation:[/] {case.metadata.automation_status.value}")
    if case.test_path:
        console.print(f"[dim]Test:[/] {case.test_path}")
    if case.file_path:
        console.print(f"[dim]File:[/] {case.file_path}")

    if case.description:
        console.print()
        console.print("[bold]Description[/]")
        console.print(case.description)

    if case.preconditions:
        console.print()
        console.print("[bold]Preconditions[/]")
        console.print(case.preconditions)

    if case.steps:
        console.print()
        console.print("[bold]Steps[/]")
        console.print(case.steps)

    if case.expected_result:
        console.print()
        console.print("[bold]Expected Result[/]")
        console.print(case.expected_result)


@case_app.command("new")
def case_new(
    section: str = typer.Argument(
        None, help="Section path, use / for nesting (e.g., 'auth/login')"
    ),
    title: str = typer.Option(None, "--title", "-t", help="Case title"),
    priority: str = typer.Option("medium", "--priority", "-p", help="Priority level"),
) -> None:
    """Create a new test case."""
    config = TestlaConfig.load()
    cases_dir = Path.cwd() / config.cases_dir

    if not cases_dir.exists():
        console.print("[red]No cases directory. Run 'testla init' first.[/]")
        raise typer.Exit(1)

    # Interactive prompts if not provided
    if title is None:
        title = typer.prompt("Title")

    if section is None:
        section = typer.prompt(
            "Section path (use / for nesting, optional - press Enter to skip)",
            default="",
        )

    # Find next available ID
    loader = CaseLoader.discover()
    existing_ids = {c.external_id for c in loader}
    sequence = 1
    while config.generate_case_id(sequence) in existing_ids:
        sequence += 1
    case_id = config.generate_case_id(sequence)

    # Create file
    if section:
        case_dir = cases_dir / section
        case_dir.mkdir(parents=True, exist_ok=True)
    else:
        case_dir = cases_dir

    filename = f"{case_id}-{_slugify(title)}.md"
    file_path = case_dir / filename

    # Get section names based on configured format
    section_names = config.section_names

    content = f"""---
id: {case_id}
title: {title}
priority: {priority}
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
    console.print(f"[green]✓[/] Created {file_path.relative_to(Path.cwd())}")


@run_app.command("list")
def run_list() -> None:
    """List recent test runs."""
    console.print("[yellow]Backend not yet configured. Run list coming soon![/]")


@run_app.command("create")
def run_create(
    name: str = typer.Option(None, "--name", "-n", help="Run name"),
) -> None:
    """Create a new test run."""
    del name  # unused until backend is implemented
    console.print("[yellow]Backend not yet configured. Run creation coming soon![/]")


@config_app.command("show")
def config_show() -> None:
    """Show current configuration."""
    config = TestlaConfig.load()
    if config.project_name == "Untitled Project" and not (Path.cwd() / "testla").exists():
        console.print("[red]Testla not initialized. Run 'testla init' first.[/]")
        raise typer.Exit(1)

    console.print("[bold]Testla Configuration[/]")
    console.print()
    console.print(f"  Project: [cyan]{config.project_name}[/]")
    console.print(f"  Cases dir: {config.cases_dir}")
    console.print(f"  ID prefix: {config.case_id_prefix}")
    console.print(f"  ID digits: {config.case_id_digits}")
    console.print(f"  Default priority: {config.default_priority}")
    console.print(f"  Section format: {config.section_format.value}")

    if config.github_repo:
        console.print()
        console.print("[bold]GitHub Integration[/]")
        console.print(f"  Repository: {config.github_repo}")
        console.print(f"  Status checks: {config.github_status_checks}")
        console.print(f"  PR comments: {config.github_pr_comments}")

    if config.backend_url:
        console.print()
        console.print("[bold]Backend[/]")
        console.print(f"  URL: {config.backend_url}")


def _slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    import re

    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
