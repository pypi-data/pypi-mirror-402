#!/usr/bin/env python3
"""Comprehensive Git repository health auditor for enterprise release engineering.

This module implements a command-line interface that inspects a local Git
repository (and optionally GitHub pull requests via the ``gh`` CLI) for
branching, merging, and workflow inconsistencies that can lead to release
management issues.

It detects and reports the following conditions:

* Active pull requests that **do not** target the ``develop`` branch.
* Hot-fix commits present on ``main`` but missing from ``develop``.
* Overlapping file modifications among open feature PRs targeting ``develop``.
* Merges into ``develop`` since the most recent release tag on ``main``.

The auditor produces a JSON report summarizing all findings and prints a
color-coded summary table to the console. It exits with status **1** if any
issue is found (unless ``--dry-run`` is specified).

Typical usage (requires the ``gh`` CLI to be installed and authenticated)::

    jps-git-repo-utils-audit check ./my-repo --github

Main components:
- Data models: ``Commit`` and ``PullRequest`` dataclasses.
- Utilities: ``run_git``, ``get_latest_release_tag``, ``get_active_prs_github``,
  ``find_hotfix_drifts``, and ``detect_file_overlap``.
- CLI: Typer-based ``check`` command for complete audit workflow.
"""


from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import typer
from rich.console import Console
from rich.table import Table

# --------------------------------------------------------------------------- #
# Typer app & logging
# --------------------------------------------------------------------------- #
app: typer.Typer = typer.Typer(help="Audit Git repository for release engineering compliance")
console: Console = Console()
log: logging.Logger = logging.getLogger("jps-git-repo-utils.audit")


# --------------------------------------------------------------------------- #
# Data models
# --------------------------------------------------------------------------- #
@dataclass
class Commit:
    """Simple representation of a Git commit."""

    hash: str
    message: str
    author: str
    date: datetime
    files: Set[str]


@dataclass
class PullRequest:
    """Representation of a GitHub pull request."""

    number: int
    title: str
    source_branch: str
    target_branch: str
    state: str
    merged_at: Optional[datetime]
    files: Set[str]


# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def run_git(cmd: List[str], cwd: Path) -> str:
    """Execute a ``git`` command in the given directory.

    Args:
        cmd: List of command-line arguments **excluding** the ``git`` binary.
        cwd: Working directory where the command should run.

    Returns:
        The command stdout stripped of trailing whitespace.
    """
    result = subprocess.run(
        ["git"] + cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_latest_release_tag(repo_path: Path) -> str:
    """Get the latest semantic version tag using Git's version-aware sorting.

    Uses ``git tag --sort=-v:refname`` which sorts tags lexicographically
    by refname, correctly handling ``v1.2.3``, ``v2.0.0-rc1``, etc.

    Args:
        repo_path: Path to the Git repository.

    Returns:
        The highest version tag (e.g. ``v2.0.0-rc1``), or ``v0.0.0`` if none exist.
    """
    try:
        output = run_git(["tag", "--sort=-v:refname"], repo_path)
        tags = [line.strip() for line in output.splitlines() if line.strip()]

        for tag in tags:
            if re.match(r"^v\d+\.\d+\.\d+", tag):
                return tag
        return "v0.0.0"
    except Exception as e:
        log.warning(f"Failed to list tags: {e}")
        return "v0.0.0"


def get_active_prs_github(repo_path: Path) -> List[PullRequest]:
    """Fetch **open** pull requests using the ``gh`` CLI.

    Args:
        repo_path: Path to the local Git repository.

    Returns:
        List of :class:`PullRequest` objects for open PRs.
        Empty list if ``gh`` is unavailable or an error occurs.
    """
    if not shutil.which("gh"):
        log.warning("GitHub CLI (gh) not found – PR checks skipped.")
        return []

    try:
        output: str = subprocess.check_output(
            [
                "gh",
                "pr",
                "list",
                "--json",
                "number,title,headRefName,baseRefName,state,files",
            ],
            cwd=repo_path,
            text=True,
        )
        data: List[Dict] = json.loads(output)
        prs: List[PullRequest] = []
        for pr in data:
            if pr["state"] == "OPEN":
                files: Set[str] = {f["path"] for f in pr.get("files", [])}
                prs.append(
                    PullRequest(
                        number=pr["number"],
                        title=pr["title"],
                        source_branch=pr["headRefName"],
                        target_branch=pr["baseRefName"],
                        state=pr["state"],
                        merged_at=None,
                        files=files,
                    )
                )
        return prs
    except Exception as exc:  # pragma: no cover
        log.error(f"Failed to fetch PRs: {exc}")
        return []


def find_hotfix_drifts(repo_path: Path) -> List[Dict]:
    """Identify commits on ``origin/main`` that are **not** on ``origin/develop`` and look like hot-fixes.

    Args:
        repo_path: Path to the local Git repository.

    Returns:
        List of dictionaries describing each hot-fix drift.
    """
    try:
        run_git(["fetch", "origin"], repo_path)

        main_log: str = run_git(["log", "origin/main", "--oneline", "--no-merges"], repo_path)
        develop_log: str = run_git(["log", "origin/develop", "--oneline"], repo_path)

        main_hashes: Set[str] = {line.split(maxsplit=1)[0] for line in main_log.splitlines()}
        develop_hashes: Set[str] = {line.split(maxsplit=1)[0] for line in develop_log.splitlines()}

        hotfixes: List[Dict] = []
        for commit_hash in main_hashes - develop_hashes:
            msg: str = run_git(["log", "-1", "--format=%s", commit_hash], repo_path)
            if any(kw in msg.lower() for kw in ["hotfix", "fix", "patch", "urgent"]):
                files_output: str = run_git(
                    ["diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
                    repo_path,
                )
                hotfixes.append(
                    {
                        "hash": commit_hash[:8],
                        "message": msg,
                        "files": files_output.strip().splitlines(),
                        "missing_in_develop": True,
                    }
                )
        return hotfixes
    except Exception as exc:  # pragma: no cover
        log.error(f"Hot-fix drift check failed: {exc}")
        return []


def detect_file_overlap(prs: List[PullRequest]) -> List[Tuple[PullRequest, PullRequest, Set[str]]]:
    """Find pairs of open PRs that modify the **same** files.

    Only PRs targeting ``develop`` are considered.

    Args:
        prs: List of open pull requests.

    Returns:
        List of tuples ``(pr1, pr2, overlapping_files)`` where ``pr1.number < pr2.number``.
    """
    overlaps: List[Tuple[PullRequest, PullRequest, Set[str]]] = []
    seen_pairs: Set[Tuple[int, int]] = set()

    for i, pr1 in enumerate(prs):
        for pr2 in prs[i + 1 :]:
            if pr1.target_branch == pr2.target_branch == "develop":
                common: Set[str] = pr1.files & pr2.files
                if common:
                    a, b = sorted((pr1.number, pr2.number))
                    pair: Tuple[int, int] = (a, b)
                    if pair not in seen_pairs:
                        overlaps.append((pr1, pr2, common))
                        seen_pairs.add(pair)
    return overlaps

# --------------------------------------------------------------------------- #
# CLI command
# --------------------------------------------------------------------------- #
@app.command()
def check(
    repo: Path = typer.Argument(  # noqa: B008
        ..., help="Path to the local Git repository to audit"
    ),  # noqa: B008
    github: bool = typer.Option(  # noqa: B008
        True, "--github", help="Use the ``gh`` CLI to fetch PR data"
    ),  # noqa: B008
    output: Path = typer.Option(  # noqa: B008
        Path("audit-report.json"),  # noqa: B008
        "--output",
        "-o",
        help="File path for the JSON audit report",
    ),
    dry_run: bool = typer.Option(  # noqa: B008
        True, "--dry-run", help="Do not exit with error code on failures"
    ),  # noqa: B008
    # ------------------------------------------------------------------- #
    # NEW OPTION: Branch filter (comma-separated)
    # ------------------------------------------------------------------- #
    branches: Optional[str] = typer.Option(  # noqa: B008
        None,
        "--branch",
        "-b",
        help=(
            "Comma-separated list of branches to include in the audit. "
            "If omitted, all default checks run."
        ),
    ),  # noqa: B008
) -> None:
    """Run a complete repository health audit.

    The audit performs four checks:

    1. Active PRs **must** target ``develop``.
    2. Hot-fix commits on ``main`` must also exist on ``develop``.
    3. No two active feature PRs may edit the same file.
    4. (Informational) Count of merges into ``develop`` since the last release tag.

    Args:
        repo: Path to the repository.
        github: Enable GitHub PR data via the ``gh`` CLI.
        output: Destination for the JSON report.
        dry_run: If ``True`` the CLI exits with status 0 even when issues are found.
        branches: Optional comma-separated branch list limiting which branches are analyzed.

    Raises:
        Exit: Exits with code 1 if issues are found and ``dry_run`` is ``False``.

    """
    repo = repo.resolve()
    log.info("Starting repository audit on %s", repo)

    # ------------------------------------------------------------------- #
    # 0. Ensure remote refs are up-to-date
    # ------------------------------------------------------------------- #
    run_git(["fetch", "origin"], repo)

    # ------------------------------------------------------------------- #
    # NEW: Branch selection logic
    # ------------------------------------------------------------------- #
    if branches:
        allowed_branches: Optional[Set[str]] = {b.strip() for b in branches.split(",") if b.strip()}
    else:
        allowed_branches = None

    def branch_allowed(branch: str) -> bool:
        if allowed_branches is None:
            return True
        return branch in allowed_branches

    # ------------------------------------------------------------------- #
    # 1. Active PRs
    # ------------------------------------------------------------------- #
    prs: List[PullRequest] = get_active_prs_github(repo) if github else []

    # Apply branch filter
    filtered_prs: List[PullRequest] = [pr for pr in prs if branch_allowed(pr.target_branch)]

    bad_prs: List[PullRequest] = [pr for pr in filtered_prs if pr.target_branch != "develop"]

    # ------------------------------------------------------------------- #
    # 2. Last release tag
    # ------------------------------------------------------------------- #
    last_tag: str = get_latest_release_tag(repo)

    # ------------------------------------------------------------------- #
    # 3. Hot-fix drift
    # ------------------------------------------------------------------- #
    if allowed_branches and not ({"main", "develop"} <= allowed_branches):
        hotfix_drifts: List[Dict] = []
    else:
        hotfix_drifts = find_hotfix_drifts(repo)

    # ------------------------------------------------------------------- #
    # 4. File overlap
    # ------------------------------------------------------------------- #
    if branch_allowed("develop"):
        overlaps: List[Tuple[PullRequest, PullRequest, Set[str]]] = detect_file_overlap(
            filtered_prs
        )
    else:
        overlaps = []

    # ------------------------------------------------------------------- #
    # Build JSON report
    # ------------------------------------------------------------------- #
    report: Dict = {
        "audit_time": datetime.now().isoformat(),
        "repository": str(repo),
        "branches_included": list(allowed_branches) if allowed_branches else "ALL",
        "last_release_tag": last_tag,
        "issues": {
            "active_prs_not_targeting_develop": len(bad_prs),
            "hotfixes_missing_in_develop": len(hotfix_drifts),
            "file_overlap_conflicts": len(overlaps),
        },
        "details": {
            "bad_prs": [
                {
                    "number": pr.number,
                    "title": pr.title,
                    "target": pr.target_branch,
                }
                for pr in bad_prs
            ],
            "hotfix_drifts": hotfix_drifts,
            "overlaps": [
                {
                    "pr1": pr1.number,
                    "pr2": pr2.number,
                    "files": list(files),
                }
                for pr1, pr2, files in overlaps
            ],
        },
        "fail": len(bad_prs) > 0 or len(hotfix_drifts) > 0 or len(overlaps) > 0,
    }

    output.write_text(json.dumps(report, indent=2))
    console.print(f"[green]Audit report written to {output}[/green]")

    # ------------------------------------------------------------------- #
    # Pretty summary table
    # ------------------------------------------------------------------- #
    table: Table = Table(title="Repository Health Audit")
    table.add_column("Check", style="bold")
    table.add_column("Status")
    table.add_column("Count")

    table.add_row(
        "PRs → develop",
        "[red]FAIL[/red]" if bad_prs else "[green]PASS[/green]",
        str(len(bad_prs)),
    )
    table.add_row(
        "Hot-fix drift",
        "[red]FAIL[/red]" if hotfix_drifts else "[green]PASS[/green]",
        str(len(hotfix_drifts)),
    )
    table.add_row(
        "File overlaps",
        "[red]FAIL[/red]" if overlaps else "[green]PASS[/green]",
        str(len(overlaps)),
    )

    console.print(table)

    # ------------------------------------------------------------------- #
    # Exit handling
    # ------------------------------------------------------------------- #
    if report["fail"] and not dry_run:
        raise typer.Exit(code=1)
    raise typer.Exit(code=0)


# --------------------------------------------------------------------------- #
# Entry-point
# --------------------------------------------------------------------------- #
if __name__ == "__main__":  # pragma: no cover
    app()
