# Testla TUI Design Specification

This document defines the design and implementation specifications for Testla's Terminal User Interface (TUI), built with the [Textual](https://textual.textualize.io/) framework.

## Philosophy

Testla offers three interaction modes forming an experience spectrum:

```
testla <command>          testla tui              Web UI (future/optional)
─────────────────         ─────────────           ───────────────────────
Quick, scriptable         Interactive workflow    Full reporting/dashboards
CI/automation             Daily tester workflow   Stakeholder views
Single operations         Browsing, exploring     Build-your-own (Wagtail-style)
```

The TUI bridges CLI efficiency with rich visual feedback—think **lazygit**, **k9s**, or **htop** energy. It's the primary interface for testers doing daily work.

---

## Screen Specifications

### 1. Dashboard (Home Screen)

The dashboard provides an at-a-glance overview of project health and recent activity.

```
┌─ Testla ─────────────────────────────────────────────────────────────────┐
│ 🔬 myproject                                            main ⎇  abc123  │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─ Recent Runs ──────────────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  ● Run #42 - PR #187 smoke tests              2 min ago    ✓ 100%  │  │
│  │  ● Run #41 - Nightly regression               6 hrs ago    ✗  94%  │  │
│  │  ○ Run #40 - PR #185 auth changes            12 hrs ago    ✓ 100%  │  │
│  │  ○ Run #39 - Manual exploratory               1 day ago    ✓  87%  │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Quick Stats ────────────┐  ┌─ Case Coverage ─────────────────────┐  │
│  │                          │  │                                     │  │
│  │  Total Cases      156    │  │  Automated    ████████████░░  78%   │  │
│  │  Automated        122    │  │  Manual       ██░░░░░░░░░░░░  12%   │  │
│  │  Passing          149    │  │  Pending      █░░░░░░░░░░░░░  10%   │  │
│  │  Flaky              3    │  │                                     │  │
│  │                          │  │                                     │  │
│  └──────────────────────────┘  └─────────────────────────────────────┘  │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│ [r] Runs  [c] Cases  [n] New Run  [s] Sync  [?] Help           [q] Quit │
└──────────────────────────────────────────────────────────────────────────┘
```

**Components:**

- `ProjectHeader` - Shows project name, git branch, commit SHA
- `RecentRunsPanel` - DataTable of recent test runs with status indicators
- `QuickStatsPanel` - Key metrics (total cases, automated, passing, flaky)
- `CoveragePanel` - Progress bars showing automation coverage breakdown

**Key Bindings:**
| Key | Action |
|-----|--------|
| `r` | Navigate to Runs screen |
| `c` | Navigate to Cases screen |
| `n` | Create new run (modal) |
| `s` | Sync cases from repository |
| `?` | Show help |
| `q` | Quit application |

---

### 2. Case Browser

The case browser allows exploring and filtering test cases with a tree/detail split view.

```
┌─ Testla ─ Cases ─────────────────────────────────────────────────────────┐
│ Filter: automated:yes priority:high                          156 cases  │
├────────────────────────────┬─────────────────────────────────────────────┤
│                            │                                             │
│  ▼ auth/ (24)              │  TC001 - Valid credentials login            │
│    ▼ login/ (12)           │  ═══════════════════════════════════════    │
│      ● TC001 Valid cred... │                                             │
│      ● TC002 Invalid pa... │  Priority:  ██░░ high                       │
│      ○ TC003 Account lo... │  Type:      functional                      │
│      ● TC004 Remember me   │  Status:    ✓ automated                     │
│    ▶ logout/ (4)           │  Tags:      auth, smoke, regression         │
│    ▶ password-reset/ (8)   │                                             │
│  ▶ checkout/ (18)          │  ─────────────────────────────────────────  │
│  ▶ inventory/ (32)         │                                             │
│  ▶ reporting/ (14)         │  Preconditions:                             │
│                            │  • User account exists                      │
│                            │  • User is not authenticated                │
│                            │                                             │
│                            │  Steps:                                     │
│                            │  1. Navigate to /login                      │
│                            │  2. Enter valid username                    │
│                            │  3. Enter valid password                    │
│                            │  4. Click "Sign In"                         │
│                            │                                             │
│                            │  Expected:                                  │
│                            │  • Redirected to dashboard                  │
│                            │  • Welcome message shown                    │
│                            │                                             │
│                            │  ─────────────────────────────────────────  │
│                            │  Linked Test:                               │
│                            │  tests/test_auth.py::test_valid_login       │
│                            │                                             │
│                            │  Last 5 Results:  ✓ ✓ ✓ ✗ ✓                 │
│                            │                                             │
├────────────────────────────┴─────────────────────────────────────────────┤
│ [/] Search  [f] Filter  [e] Edit  [t] Run Test  [h] History    [←] Back │
└──────────────────────────────────────────────────────────────────────────┘
```

**Components:**

- `FilterBar` - Shows active filters and case count
- `CaseTree` - Collapsible tree view organized by section path
- `CaseDetailPanel` - Markdown-rendered case details with metadata

**Tree Node Indicators:**

- `●` = Automated test case
- `○` = Manual/not automated
- `▼` = Expanded folder
- `▶` = Collapsed folder

**Key Bindings:**
| Key | Action |
|-----|--------|
| `/` | Focus search/filter input |
| `f` | Open filter modal |
| `e` | Edit case file in `$EDITOR` |
| `t` | Run the linked test |
| `h` | Show result history for case |
| `Enter` | Expand/collapse folder or select case |
| `Esc` | Go back to dashboard |

---

### 3. Run Viewer

Shows details and results of a specific test run.

```
┌─ Testla ─ Run #41 ───────────────────────────────────────────────────────┐
│ Nightly regression                                      6 hours ago     │
│ ⎇ main @ abc1234 • CI: GitHub Actions • Duration: 12m 34s               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─ Summary ─────────────────────────────────────────────────────────┐   │
│  │  ✓ Passed   147  ████████████████████████████████████████░░░  94% │   │
│  │  ✗ Failed     6  ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   4% │   │
│  │  ○ Skipped    3  █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   2% │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─ Failed Tests ────────────────────────────────────────────────────┐   │
│  │                                                                   │   │
│  │  ✗ TC045 Checkout with expired coupon                    1.2s    │   │
│  │    AssertionError: Expected 'Invalid coupon' message             │   │
│  │                                                                   │   │
│  │  ✗ TC046 Checkout with negative quantity                 0.8s    │   │
│  │    ValidationError: quantity must be positive                    │   │
│  │                                                                   │   │
│  │  ✗ TC089 Report generation timeout                      30.1s    │   │
│  │    TimeoutError: Report did not complete in 30s                  │   │
│  │                                                                   │   │
│  │  ▶ Show 3 more failed tests...                                   │   │
│  │                                                                   │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  [Enter] View Details  [a] Show All  [f] Filter  [x] Export   [←] Back  │
└──────────────────────────────────────────────────────────────────────────┘
```

**Components:**

- `RunHeader` - Run name, git context, CI info, duration
- `ResultSummaryPanel` - Pass/fail/skip counts with progress bars
- `FailedTestsList` - Scrollable list of failures with brief error messages

**Key Bindings:**
| Key | Action |
|-----|--------|
| `Enter` | View failure details (opens modal) |
| `a` | Show all results (not just failures) |
| `f` | Filter results |
| `x` | Export run report |
| `Esc` | Go back |

---

### 4. Failure Detail Modal

Modal overlay showing full details of a failed test.

```
┌─ TC045 - Checkout with expired coupon ───────────────────────────────────┐
│                                                                          │
│  Status:    ✗ FAILED                                                     │
│  Duration:  1.234s                                                       │
│  Run:       #41 Nightly regression                                       │
│                                                                          │
│  ┌─ Error ───────────────────────────────────────────────────────────┐   │
│  │ AssertionError: Expected 'Invalid coupon' message to appear       │   │
│  │                                                                   │   │
│  │ > assert "Invalid coupon" in page.content()                       │   │
│  │ E AssertionError: assert 'Invalid coupon' in '<!DOCTYPE html>...' │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─ Stack Trace ─────────────────────────────────────────────────────┐   │
│  │ tests/test_checkout.py:145 in test_expired_coupon                 │   │
│  │   > assert "Invalid coupon" in page.content()                     │   │
│  │ tests/conftest.py:34 in checkout_page                             │   │
│  │   > return page.goto("/checkout")                                 │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  History: ✓ ✓ ✓ ✓ ✗ ✗ ✗ ✓ ✓ ✗  (last 10 runs)                           │
│           Flaky score: 30% - Consider investigating                      │
│                                                                          │
│  [o] Open in Editor  [r] Rerun  [c] View Case  [g] GitHub    [Esc] Close │
└──────────────────────────────────────────────────────────────────────────┘
```

**Components:**

- `FailureMetadata` - Status, duration, run reference
- `ErrorPanel` - Formatted error message
- `StackTracePanel` - Collapsible stack trace with syntax highlighting
- `HistoryIndicator` - Visual pass/fail history with flaky detection

**Key Bindings:**
| Key | Action |
|-----|--------|
| `o` | Open test file in `$EDITOR` at failing line |
| `r` | Rerun this specific test |
| `c` | View the test case definition |
| `g` | Open in GitHub (if configured) |
| `Esc` | Close modal |

---

## Implementation Architecture

### File Structure

```
src/testla/tui/
├── __init__.py
├── app.py              # Main TestlaApp class
├── styles.tcss         # Textual CSS styling
├── screens/
│   ├── __init__.py
│   ├── dashboard.py    # DashboardScreen
│   ├── cases.py        # CaseBrowserScreen
│   ├── runs.py         # RunsScreen
│   └── run_detail.py   # RunDetailScreen
├── widgets/
│   ├── __init__.py
│   ├── case_tree.py    # CaseTree widget
│   ├── case_detail.py  # CaseDetailPanel widget
│   ├── run_summary.py  # ResultSummaryPanel widget
│   ├── stats.py        # QuickStatsPanel, CoveragePanel
│   └── header.py       # ProjectHeader widget
└── modals/
    ├── __init__.py
    ├── failure.py      # FailureDetailModal
    ├── new_run.py      # NewRunModal
    └── filter.py       # FilterModal
```

### App Entry Point

```python
# src/testla/tui/app.py
from textual.app import App
from textual.binding import Binding

from testla.repository.case_loader import CaseLoader
from testla.repository.config import TestlaConfig
from testla.tui.screens.dashboard import DashboardScreen


class TestlaApp(App):
    """Testla TUI Application."""

    CSS_PATH = "styles.tcss"
    TITLE = "Testla"

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("?", "help", "Help", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config = TestlaConfig.load()
        self.case_loader = CaseLoader.discover()

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen())


def main() -> None:
    app = TestlaApp()
    app.run()
```

### Screen Base Pattern

Each screen should follow this pattern:

```python
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer


class ExampleScreen(Screen):
    """Screen docstring."""

    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        # Screen-specific bindings...
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        # Screen content...
        yield Footer()

    async def on_mount(self) -> None:
        # Load data, initialize state
        pass
```

### Styling Guidelines

Use Textual CSS (`.tcss`) for styling:

```css
/* styles.tcss */

Screen {
  background: $surface;
}

.panel-title {
  text-style: bold;
  color: $primary;
  padding-bottom: 1;
  border-bottom: solid $primary-darken-2;
  margin-bottom: 1;
}

/* Status colors */
.status-passed {
  color: $success;
}
.status-failed {
  color: $error;
}
.status-skipped {
  color: $warning-darken-1;
}

/* Tree indicators */
.automated {
  color: $success;
}
.manual {
  color: $text-muted;
}
```

---

## User Workflows

### Workflow 1: Daily Tester Check-in

```
$ testla tui
→ Dashboard shows last night's regression failed
→ Press 'r' to see runs
→ Select failed run, see 6 failures
→ Press Enter on failure, review stack trace
→ Press 'o' to open in editor
→ Fix issue, press 't' to rerun test
```

### Workflow 2: Exploring Test Coverage

```
$ testla tui
→ Press 'c' for cases
→ Press 'f' to filter: "automated:no priority:high"
→ See high-priority cases without automation
→ Select case, press 'e' to add automation link
```

### Workflow 3: Creating a Manual Run

```
$ testla tui
→ Press 'n' for new run
→ Enter name: "Release 2.1 smoke test"
→ Select cases to include
→ Execute tests, record results via CLI/API
→ View run summary in TUI
```

---

## Dependencies

The TUI requires:

- `textual>=0.50.0` - TUI framework
- `rich>=13.0.0` - Terminal formatting (included with Textual)

These are already in `pyproject.toml`.

---

## Future Enhancements

- **Live updates**: WebSocket connection to backend for real-time result streaming
- **Themes**: Light/dark mode, custom color schemes
- **Mouse support**: Click navigation (Textual supports this)
- **Split panes**: Resizable panels
- **Vim keybindings**: Optional vim-style navigation mode
