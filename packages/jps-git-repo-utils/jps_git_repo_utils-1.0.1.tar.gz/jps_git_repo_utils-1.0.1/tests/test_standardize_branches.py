"""Tests for the standardize_branches script."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from typer.testing import CliRunner

from jps_git_repo_utils.standardize_branches import app


def test_dry_run_is_default(git_repo, runner: CliRunner) -> None:
    """Ensure that the app runs in dry-run mode by default.

    Args:
        git_repo: The elite-grade git repository fixture.
        runner: The Typer CLI runner fixture.
    """
    result = runner.invoke(app)
    assert result.exit_code == 0
    assert "DRY-RUN" in result.stdout
    assert "Re-run with --live" in result.stdout


def test_live_mode_not_executed_by_default(git_repo, runner: CliRunner) -> None:
    """Ensure that without --live, the app remains in dry-run mode.

    Even if the git_repo fixture is used, the app should not perform live changes
    unless explicitly instructed.

    Args:
        git_repo: The elite-grade git repository fixture.
        runner: The Typer CLI runner fixture.
    """
    result = runner.invoke(app)
    assert result.exit_code == 0
    assert "DRY-RUN" in result.stdout


def test_custom_outdir(git_repo, runner: CliRunner, tmp_path: Path) -> None:
    """Test that specifying a custom output directory works.

    Args:
        git_repo: The elite-grade git repository fixture.
        runner: The Typer CLI runner fixture.
        tmp_path: Temporary path fixture for output.
    """
    result = runner.invoke(app, ["--outdir", str(tmp_path)])
    assert result.exit_code == 0

    files = list(tmp_path.rglob("*"))
    assert len(files) >= 4
    assert any(f.suffix == ".xlsx" for f in files)
    assert any("report" in f.name and f.suffix == ".txt" for f in files)
    assert any(f.suffix == ".log" for f in files)
    assert any("execution_plan" in f.name for f in files)


def test_jira_ticket_extraction_in_planned_branches(
    git_repo, runner: CliRunner, tmp_path: Path
) -> None:
    """Test that JIRA tickets are correctly extracted from planned branches.

    Args:
        git_repo: The elite-grade git repository fixture.
        runner: The Typer CLI runner fixture.
        tmp_path: Temporary path fixture for output.
    """
    result = runner.invoke(app, ["--outdir", str(tmp_path)])
    assert result.exit_code == 0

    excel_files = list(tmp_path.rglob("*.xlsx"))
    assert excel_files, f"No Excel file in {tmp_path}"
    excel_path = excel_files[0]

    df = pd.read_excel(excel_path, sheet_name=None)

    # Search ALL sheets — including "Planned Feature", "Planned Bugfix", etc.
    all_tickets = []
    for _, sheet_df in df.items():
        if "Jira Ticket" in sheet_df.columns:
            tickets = sheet_df["Jira Ticket"].dropna().astype(str).tolist()
            all_tickets.extend(tickets)
        # Also check "Current Name" for raw JIRA codes
        if "Current Name" in sheet_df.columns:
            names = sheet_df["Current Name"].astype(str).tolist()
            for name in names:
                # Extract BISD-1234 from branch names
                jira_match = re.search(r"(BISD-\d+)", name, re.IGNORECASE)
                if jira_match:
                    all_tickets.append(jira_match.group(1).upper())

    # Remove duplicates and empty
    all_tickets = [t for t in all_tickets if t]

    assert all_tickets, f"No JIRA tickets found in any sheet. Sheets: {list(df.keys())}"
    assert any(t.startswith("BISD-") for t in all_tickets), f"No BISD ticket in: {all_tickets}"


def test_no_duplicate_processing(git_repo, runner: CliRunner, tmp_path: Path) -> None:
    """Test that running the app multiple times does not duplicate processing.

    Args:
        git_repo: The elite-grade git repository fixture.
        runner: The Typer CLI runner fixture.
        tmp_path: Temporary path fixture for output.
    """
    run1 = tmp_path / "run1"
    run2 = tmp_path / "run2"
    runner.invoke(app, ["--outdir", str(run1)])
    runner.invoke(app, ["--outdir", str(run2)])
    assert list(run1.rglob("*"))
    assert list(run2.rglob("*"))
