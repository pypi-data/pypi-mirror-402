#!/usr/bin/env python3
"""standardize_branches.py – Repository branch standardization and cleanup utility.

This script analyzes a local Git repository, classifies every branch according to
activity and naming conventions, and prepares a complete migration plan that:

* Archives branches with no commits in the current calendar year
  (moves them to ``archive/<original-name>``)
* Renames legacy essential branches (``master`` → ``main``,
  ``development`` → ``develop``)
* Moves active, un-namespaced branches into one of the four standard prefixes:
  ``feature/``, ``bugfix/``, ``hotfix/``, or ``release/``
* Detects and reports production branches (any branch containing the word
  "production")
* Generates a human-readable text report, an Excel workbook with one worksheet
  per section, and a ready-to-copy execution-plan script containing every
  ``git push`` command needed to apply the changes.

The tool fully supports ``--dry-run`` mode – no remote changes are ever made
unless the user explicitly runs the script without that flag.

Features
--------
* Automatic ``git fetch --all`` to guarantee a complete branch list
* Detailed per-branch metadata (last commit date, hash, committer, author)
* Comprehensive logging via the standard ``logging`` package
* CLI built with ``typer`` for excellent help output and type validation
* All output files are written to a dated directory under ``/tmp/<user>/…``
  (customisable with ``--outdir``)
* Google-style docstrings, type hints, and modular design for maintainability

Usage
-----
.. code-block:: bash

    # Dry-run (default) – only generates reports and plan
    python standardize_branches.py

    # Actually apply the changes to the remote
    python standardize_branches.py --no-dry-run

    # Custom output location
    python standardize_branches.py --outdir /path/to/output

The script prints the absolute paths of the three generated files at the end
of the run and exits with status 0 unless a critical error occurs.

Author
------
Jaideep Sundaram

License
-------
MIT – see ``LICENSE`` file in the repository.
"""
from __future__ import annotations

import getpass
import logging
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, TextIO

import typer
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

APP_NAME = Path(__file__).stem
NOW = datetime.now()
CURRENT_YEAR = NOW.year
TIMESTAMP = NOW.strftime("%Y-%m-%d-%H%M%S")
USER = getpass.getuser()

SAFE_RE = re.compile(r"[^a-zA-Z0-9._/-]+")
app = typer.Typer(help="Standardize Git branches - v1.2.4 (dry-run default)")


@dataclass(frozen=True)
class BranchInfo:
    """Metadata about a Git branch.

    Attributes:
        name: The name of the branch.
        last_commit_date: ISO8601 string of the last commit date.
        last_commit_hash: Short hash of the last commit.
        committer_name: Name of the committer of the last commit.
        committer_email: Email of the committer of the last commit.
        author_name: Name of the author of the last commit.
        author_email: Email of the author of the last commit.
        is_active_this_year: Whether the branch has commits in the current year.
    """

    name: str
    last_commit_date: str
    last_commit_hash: str
    committer_name: str
    committer_email: str
    author_name: str
    author_email: str
    is_active_this_year: bool


@dataclass
class PlannedMove:
    """Planned move for a Git branch.

    Attributes:
        current_name: The current name of the branch.
        planned_name: The planned new name for the branch.
        reason: The reason for the move ("archive", "feature", "bugfix", "hotfix", or "release").
    """

    current_name: str
    planned_name: str
    reason: str  # "archive" | "feature" | "bugfix" | "hotfix" | "release"


@dataclass
class EssentialRename:
    """Planned rename for an essential Git branch.

    Attributes:
        current_name: The current name of the branch.
        target_name: The target new name for the branch.
    """

    current_name: str
    target_name: str


# =============================================================================
# Git Helpers
# =============================================================================


def run_git(cmd: List[str]) -> str:
    """Run a git command and return its output.

    Args:
        cmd: List of git command arguments.

    Returns:
        The standard output from the git command.

    Raises:
        RuntimeError: If the git command fails.
    """
    result = subprocess.run(["git", *cmd], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(cmd)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def git_fetch_all() -> None:
    """Fetch all remote branches and prune deleted ones."""
    logging.info("Fetching all remote branches...")
    run_git(["fetch", "--all", "--prune"])


def get_remote_branches() -> List[str]:
    """Get a list of all remote branches.

    Returns:
        A list of remote branch names.
    """
    out = run_git(["for-each-ref", "--format=%(refname:short)", "refs/remotes/origin"])
    branches = []
    for line in out.splitlines():
        ref = line.strip()
        if "->" in ref or ref == "origin/origin":
            continue
        branch = ref.replace("origin/", "", 1)
        if branch:
            branches.append(branch)
    logging.info("Discovered %d real remote branches", len(branches))
    return sorted(branches)


def get_branch_info(branch: str) -> BranchInfo:
    """Get metadata about a specific branch.

    Args:
        branch: The name of the branch.

    Returns:
        A BranchInfo instance with metadata about the branch.
    """
    fmt = (
        "%(committerdate:iso8601)|%(objectname:short)|"
        "%(committername)|%(committeremail)|%(authorname)|%(authoremail)"
    )
    try:
        out = run_git(["for-each-ref", f"--format={fmt}", f"refs/remotes/origin/{branch}"])
    except RuntimeError:
        out = ""

    if not out:
        return BranchInfo(
            branch, "unknown", "unknown", "unknown", "unknown", "unknown", "unknown", False
        )

    parts = out.split("|", 5)
    if len(parts) != 6:
        return BranchInfo(
            branch, "unknown", "unknown", "unknown", "unknown", "unknown", "unknown", False
        )

    dt_str = parts[0].replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(dt_str)
        active = dt.year == CURRENT_YEAR
    except Exception:
        active = False

    return BranchInfo(
        name=branch,
        last_commit_date=parts[0],
        last_commit_hash=parts[1],
        committer_name=parts[2],
        committer_email=parts[3],
        author_name=parts[4],
        author_email=parts[5],
        is_active_this_year=active,
    )


# =============================================================================
# Classification & Planning
# =============================================================================


def is_namespaced(branch: str) -> bool:
    """Check if a branch is namespaced (e.g., feature/, bugfix/, hotfix/, release/).

    Args:
        branch: The name of the branch.

    Returns:
        True if the branch is namespaced, False otherwise.
    """
    return any(branch.startswith(p) for p in ("feature/", "bugfix/", "hotfix/", "release/"))


def is_archived(branch: str) -> bool:
    """Check if a branch is archived (e.g., starts with archive/).

    Args:
        branch: The name of the branch.

    Returns:
        True if the branch is archived, False otherwise.
    """
    return branch.startswith("archive/")


def classify_for_move(branch: str) -> str:
    """Classify a branch for moving into a namespace.

    Args:
        branch: The name of the branch.

    Returns:
        str: The target namespace: "feature", "bugfix", "hotfix", or "release".
    """
    lower = branch.lower()
    if "hotfix" in lower:
        return "hotfix"
    if any(x in lower for x in ("bug", "fix", "bugfix")):
        return "bugfix"
    if "release" in lower:
        return "release"
    return "feature"


def sanitize_name(name: str) -> str:
    """Sanitize a branch name to be safe for use in a new branch.

    Args:
        name: The original branch name.

    Returns:
        The sanitized branch name.
    """
    return SAFE_RE.sub("-", name).strip("-")


def plan_changes(
    branches: List[str],
    info_map: Dict[str, BranchInfo],
) -> tuple[
    List[BranchInfo],  # namespaced
    List[BranchInfo],  # already archived
    List[BranchInfo],  # production
    List[BranchInfo],  # essential
    List[EssentialRename],
    List[PlannedMove],  # archive
    List[PlannedMove],  # feature
    List[PlannedMove],  # bugfix
    List[PlannedMove],  # hotfix
    List[PlannedMove],  # release
]:
    """Plan the changes needed for branch standardization.

    Args:
        branches: List of all remote branch names.
        info_map: Mapping of branch names to their BranchInfo metadata.

    Returns:
        A tuple containing lists of BranchInfo and PlannedMove objects categorized by their planned actions.
    """
    namespaced: List[BranchInfo] = []
    already_archived: List[BranchInfo] = []
    production: List[BranchInfo] = []
    essential_found: List[BranchInfo] = []
    essential_renames: List[EssentialRename] = []
    archive: List[PlannedMove] = []
    to_feature: List[PlannedMove] = []
    to_bugfix: List[PlannedMove] = []
    to_hotfix: List[PlannedMove] = []
    to_release: List[PlannedMove] = []

    dev_rename = master_rename = None

    for branch in branches:
        if branch in {"origin", "HEAD"}:
            continue

        info = info_map[branch]
        lower = branch.lower()

        if "production" in lower:
            production.append(info)
            continue

        if is_archived(branch):
            already_archived.append(info)
            continue

        if is_namespaced(branch):
            namespaced.append(info)
            continue

        if branch in ("develop", "development", "main", "master"):
            essential_found.append(info)
            if branch == "development":
                dev_rename = EssentialRename("development", "develop")
            elif branch == "master":
                master_rename = EssentialRename("master", "main")
            continue

        if not info.is_active_this_year:
            archive.append(PlannedMove(branch, f"archive/{branch}", "archive"))
            continue

        target = classify_for_move(branch)
        safe = sanitize_name(branch)
        planned = f"{target}/{safe}"
        move = PlannedMove(branch, planned, target)

        if target == "hotfix":
            to_hotfix.append(move)
        elif target == "bugfix":
            to_bugfix.append(move)
        elif target == "release":
            to_release.append(move)
        else:
            to_feature.append(move)

    if dev_rename and "development" in info_map:
        essential_renames.append(dev_rename)
    if master_rename and "master" in info_map:
        essential_renames.append(master_rename)

    return (
        namespaced,
        already_archived,
        production,
        essential_found,
        essential_renames,
        archive,
        to_feature,
        to_bugfix,
        to_hotfix,
        to_release,
    )


# =============================================================================
# Output Writers
# =============================================================================


def banner(section: int, title: str, count: int) -> str:
    """Write a banner for a report section.

    Args:
        section: The section number.
        title: The title of the section.
        count: The number of items in the section.

    Returns:
        A formatted banner string for the section.
    """
    return (
        f"##{'-'*62}\n"
        f"##\n"
        f"## Section {section}: {title}\n"
        f"## count: {count}\n"
        f"##{'-'*62}\n"
    )


def write_vertical_record(f: TextIO, idx: int, info: BranchInfo, planned: str = "") -> None:
    """Write a vertical record of branch info to a file.

    Args:
        f: The file object to write to.
        idx: The index number of the branch.
        info: The BranchInfo instance.
        planned: The planned branch name, if any.
    """
    f.write(f"{idx}.\n")
    f.write(f"Current Branch Name: {info.name}\n")
    if planned:
        if planned.startswith("archive/"):
            f.write(f"Planned Branch Name: {planned}\n")
        else:
            namespace = planned.split("/")[0].capitalize()
            f.write(f"Planned {namespace} Branch Name: {planned}\n")
    f.write(f"Date Last Commit: {info.last_commit_date}\n")
    f.write(f"Hash Last Commit: {info.last_commit_hash}\n")
    f.write(f"Committer: {info.committer_name}\n")
    f.write(f"Committer Email: {info.committer_email}\n")
    f.write(f"Author: {info.author_name}\n")
    f.write(f"Author Email: {info.author_email}\n")
    f.write("\n")


def write_text_report(
    path: Path,
    logfile: Path,
    repo_path: Path,
    stats: Dict[str, str],
    namespaced: List[BranchInfo],
    already_archived: List[BranchInfo],
    production: List[BranchInfo],
    essential: List[BranchInfo],
    archive: List[PlannedMove],
    feature_moves: List[PlannedMove],
    bugfix_moves: List[PlannedMove],
    hotfix_moves: List[PlannedMove],
    release_moves: List[PlannedMove],
) -> None:
    """Write a detailed text report of branch information and planned moves.

    Args:
        path: The file path to write the report to.
        logfile: The path to the log file.
        repo_path: The path to the Git repository.
        stats: A dictionary of statistics to include in the header.
        namespaced: List of namespaced branches.
        already_archived: List of already archived branches.
        production: List of production branches.
        essential: List of essential branches.
        archive: List of planned archive moves.
        feature_moves: List of planned feature moves.
        bugfix_moves: List of planned bugfix moves.
        hotfix_moves: List of planned hotfix moves.
        release_moves: List of planned release moves.
    """
    with path.open("w", encoding="utf-8") as f:
        # Header
        f.write(f"## method-created: {Path(__file__).resolve()}\n")
        f.write(f"## date-created: {NOW.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"## created-by: {USER}\n")
        f.write(f"## logfile: {logfile.resolve()}\n")
        f.write(f"## code-repository: {repo_path.name}\n")
        f.write(f"## current-working-directory: {repo_path.resolve()}\n")
        f.write(f"## log-file: {logfile.resolve()}\n")
        for k, v in stats.items():
            f.write(f"## {k}: {v}\n")
        f.write("\n")

        # Sections 1–4: Namespaced
        sections = [
            (1, "Feature Branches Found", [b for b in namespaced if b.name.startswith("feature/")]),
            (2, "Bugfix Branches Found", [b for b in namespaced if b.name.startswith("bugfix/")]),
            (3, "Hotfix Branches Found", [b for b in namespaced if b.name.startswith("hotfix/")]),
            (
                4,
                "Release Candidate Branches Found",
                [b for b in namespaced if b.name.startswith("release/")],
            ),
        ]
        for num, title, items in sections:
            f.write(banner(num, title, len(items)))
            for idx, b in enumerate(items, 1):
                write_vertical_record(f, idx, get_branch_info(b.name))
            f.write("\n")

        # Section 5: Already Archived
        f.write(banner(5, "Archived Branches Found", len(already_archived)))
        for idx, b in enumerate(already_archived, 1):
            write_vertical_record(f, idx, b)
        f.write("\n")

        # Section 6: Planned Archive
        f.write(banner(6, "Planned Archived Branches", len(archive)))
        for idx, m in enumerate(archive, 1):
            write_vertical_record(f, idx, get_branch_info(m.current_name), m.planned_name)
        f.write("\n")

        # Sections 7–10: Planned moves
        move_sections = [
            (7, "Planned Feature Branches", feature_moves),
            (8, "Planned Bugfix Branches", bugfix_moves),
            (9, "Planned Hotfix Branches", hotfix_moves),
            (10, "Planned Release Branches", release_moves),
        ]
        for num, title, moves in move_sections:
            f.write(banner(num, title, len(moves)))
            for idx, m in enumerate(moves, 1):
                write_vertical_record(f, idx, get_branch_info(m.current_name), m.planned_name)
            f.write("\n")

        # Section 11: Essential
        f.write(banner(11, "Essential Branches", len(essential)))
        for idx, b in enumerate(essential, 1):
            write_vertical_record(f, idx, b)
        f.write("\n")

        # Section 12: Production
        f.write(banner(12, "Production Branches", len(production)))
        for idx, b in enumerate(production, 1):
            write_vertical_record(f, idx, b)
        f.write("\n")


def write_execution_plan(
    path: Path, moves: List[PlannedMove], renames: List[EssentialRename]
) -> None:
    """Write a shell script execution plan for applying branch changes.

    Args:
        path: The file path to write the execution plan to.
        moves: A list of planned branch moves.
        renames: A list of essential branch renames.
    """
    with path.open("w", encoding="utf-8") as f:
        f.write("#!/bin/bash\n")
        f.write(f"# Execution plan generated by {APP_NAME} v1.2.4\n")
        f.write(f"# {NOW.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("# WARNING: This script modifies remote branches!\n\n")
        f.write("set -e\n\n")

        if renames:
            f.write(f"# {'='*70}\n")
            f.write("# ESSENTIAL BRANCH RENAMES\n")
            f.write(f"# {'='*70}\n\n")
            for r in renames:
                f.write(f'echo "Renaming {r.current_name} to {r.target_name}"\n')
                f.write(
                    f"git push origin origin/{r.current_name}:refs/heads/{r.target_name} :{r.current_name}\n\n"
                )

        groups = {
            "archive": [m for m in moves if m.reason == "archive"],
            "feature": [m for m in moves if m.reason == "feature"],
            "bugfix": [m for m in moves if m.reason == "bugfix"],
            "hotfix": [m for m in moves if m.reason == "hotfix"],
            "release": [m for m in moves if m.reason == "release"],
        }

        for kind, items in groups.items():
            if not items:
                continue
            f.write(f"# {'='*70}\n")
            f.write(f"# MOVING TO {kind.upper()}/ ({len(items)} branches)\n")
            f.write(f"# {'='*70}\n\n")
            for m in items:
                f.write(f'echo "Moving {m.current_name} to {m.planned_name}"\n')
                f.write(
                    f"git checkout -b {m.current_name} origin/{m.current_name} 2>/dev/null || true\n"
                )
                f.write(f"git branch -m {m.current_name} {m.planned_name}\n")
                f.write(f"git push origin {m.planned_name}\n")
                f.write(f"git push origin --delete {m.current_name} || true\n")
                f.write("\n")

        f.write('echo "All operations completed successfully."\n')


def write_excel(
    path: Path,
    namespaced: List[BranchInfo],
    already_archived: List[BranchInfo],
    production: List[BranchInfo],
    essential: List[BranchInfo],
    archive: List[PlannedMove],
    feature_moves: List[PlannedMove],
    bugfix_moves: List[PlannedMove],
    hotfix_moves: List[PlannedMove],
    release_moves: List[PlannedMove],
) -> None:
    """Write an Excel workbook summarizing branch information and planned moves.

    Args:
        path: The file path to write the Excel workbook to.
        namespaced: List of namespaced branches.
        already_archived: List of already archived branches.
        production: List of production branches.
        essential: List of essential branches.
        archive: List of planned archive moves.
        feature_moves: List of planned feature moves.
        bugfix_moves: List of planned bugfix moves.
        hotfix_moves: List of planned hotfix moves.
        release_moves: List of planned release moves.
    """
    wb = Workbook()
    wb.remove(wb.active)

    def sheet(name: str, headers: List[str]) -> Worksheet:
        ws = wb.create_sheet(title=name)
        ws.append(headers)
        return ws

    # Existing sheets
    ws_feat = sheet(
        "Feature Branches Found",
        [
            "Current Name",
            "Date Last Commit",
            "Hash Last Commit",
            "Committer",
            "Committer Email",
            "Author",
            "Author Email",
        ],
    )
    ws_bug = sheet(
        "Bugfix Branches Found",
        [
            "Current Name",
            "Date Last Commit",
            "Hash Last Commit",
            "Committer",
            "Committer Email",
            "Author",
            "Author Email",
        ],
    )
    ws_hot = sheet(
        "Hotfix Branches Found",
        [
            "Current Name",
            "Date Last Commit",
            "Hash Last Commit",
            "Committer",
            "Committer Email",
            "Author",
            "Author Email",
        ],
    )
    ws_rel = sheet(
        "Release Candidate Branches Found",
        [
            "Current Name",
            "Date Last Commit",
            "Hash Last Commit",
            "Committer",
            "Committer Email",
            "Author",
            "Author Email",
        ],
    )
    ws_archived = sheet(
        "Archived Branches",
        [
            "Current Name",
            "Date Last Commit",
            "Hash Last Commit",
            "Committer",
            "Committer Email",
            "Author",
            "Author Email",
        ],
    )
    ws_arch = sheet(
        "Planned Archive",
        [
            "Current Name",
            "Planned Name",
            "Date Last Commit",
            "Hash Last Commit",
            "Committer",
            "Committer Email",
            "Author",
            "Author Email",
        ],
    )
    ws_pfeat = sheet(
        "Planned Feature",
        [
            "Current Name",
            "Planned Name",
            "Date Last Commit",
            "Hash Last Commit",
            "Committer",
            "Committer Email",
            "Author",
            "Author Email",
        ],
    )
    ws_pbug = sheet(
        "Planned Bugfix",
        [
            "Current Name",
            "Planned Name",
            "Date Last Commit",
            "Hash Last Commit",
            "Committer",
            "Committer Email",
            "Author",
            "Author Email",
        ],
    )
    ws_phot = sheet(
        "Planned Hotfix",
        [
            "Current Name",
            "Planned Name",
            "Date Last Commit",
            "Hash Last Commit",
            "Committer",
            "Committer Email",
            "Author",
            "Author Email",
        ],
    )
    ws_prel = sheet(
        "Planned Release",
        [
            "Current Name",
            "Planned Name",
            "Date Last Commit",
            "Hash Last Commit",
            "Committer",
            "Committer Email",
            "Author",
            "Author Email",
        ],
    )
    ws_ess = sheet(
        "Essential Branches",
        [
            "Current Name",
            "Planned Name",
            "Date Last Commit",
            "Hash Last Commit",
            "Committer",
            "Committer Email",
            "Author",
            "Author Email",
        ],
    )
    ws_prod = sheet(
        "Production Branches",
        [
            "Current Name",
            "Planned Name",
            "Date Last Commit",
            "Hash Last Commit",
            "Committer",
            "Committer Email",
            "Author",
            "Author Email",
        ],
    )

    # Populate
    for b in namespaced:
        row = [
            b.name,
            b.last_commit_date,
            b.last_commit_hash,
            b.committer_name,
            b.committer_email,
            b.author_name,
            b.author_email,
        ]
        if b.name.startswith("feature/"):
            ws_feat.append(row)
        elif b.name.startswith("bugfix/"):
            ws_bug.append(row)
        elif b.name.startswith("hotfix/"):
            ws_hot.append(row)
        elif b.name.startswith("release/"):
            ws_rel.append(row)

    for b in already_archived:
        ws_archived.append(
            [
                b.name,
                b.last_commit_date,
                b.last_commit_hash,
                b.committer_name,
                b.committer_email,
                b.author_name,
                b.author_email,
            ]
        )

    for m in archive:
        b = get_branch_info(m.current_name)
        ws_arch.append(
            [
                b.name,
                m.planned_name,
                b.last_commit_date,
                b.last_commit_hash,
                b.committer_name,
                b.committer_email,
                b.author_name,
                b.author_email,
            ]
        )

    for m in feature_moves:
        b = get_branch_info(m.current_name)
        ws_pfeat.append(
            [
                b.name,
                m.planned_name,
                b.last_commit_date,
                b.last_commit_hash,
                b.committer_name,
                b.committer_email,
                b.author_name,
                b.author_email,
            ]
        )
    for m in bugfix_moves:
        b = get_branch_info(m.current_name)
        ws_pbug.append(
            [
                b.name,
                m.planned_name,
                b.last_commit_date,
                b.last_commit_hash,
                b.committer_name,
                b.committer_email,
                b.author_name,
                b.author_email,
            ]
        )
    for m in hotfix_moves:
        b = get_branch_info(m.current_name)
        ws_phot.append(
            [
                b.name,
                m.planned_name,
                b.last_commit_date,
                b.last_commit_hash,
                b.committer_name,
                b.committer_email,
                b.author_name,
                b.author_email,
            ]
        )
    for m in release_moves:
        b = get_branch_info(m.current_name)
        ws_prel.append(
            [
                b.name,
                m.planned_name,
                b.last_commit_date,
                b.last_commit_hash,
                b.committer_name,
                b.committer_email,
                b.author_name,
                b.author_email,
            ]
        )

    for b in essential:
        planned = "develop" if b.name == "development" else "main" if b.name == "master" else b.name
        ws_ess.append(
            [
                b.name,
                planned,
                b.last_commit_date,
                b.last_commit_hash,
                b.committer_name,
                b.committer_email,
                b.author_name,
                b.author_email,
            ]
        )

    for b in production:
        ws_prod.append(
            [
                b.name,
                "",
                b.last_commit_date,
                b.last_commit_hash,
                b.committer_name,
                b.committer_email,
                b.author_name,
                b.author_email,
            ]
        )

    wb.save(path)


# =============================================================================
# Logging & Main
# =============================================================================


def configure_logging(logfile: Path) -> None:
    """Configure logging to file and stderr.

    Args:
        logfile: The path to the log file.
    """
    fmt = "%(levelname)s : %(asctime)s : %(pathname)s : %(lineno)d : %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            logging.FileHandler(logfile, encoding="utf-8"),
            logging.StreamHandler(sys.stderr),
        ],
    )
    for h in logging.getLogger().handlers:
        if isinstance(h, logging.StreamHandler) and h.stream is sys.stderr:
            h.setLevel(logging.WARNING)


@app.command()
def main(
    outdir: Optional[Path] = typer.Option(  # noqa: B008
        None, "--outdir", help="Base output directory"
    ),  # noqa: B008
    report_file: Optional[Path] = typer.Option(  # noqa: B008
        None, "--report-file", help="Text report path"
    ),  # noqa: B008
    logfile: Optional[Path] = typer.Option(None, "--logfile", help="Log file path"),  # noqa: B008
    execution_plan: Optional[Path] = typer.Option(  # noqa: B008
        None, "--execution-plan", help="Execution plan path"
    ),
    excel_report_file: Optional[Path] = typer.Option(  # noqa: B008
        None, "--excel-report-file", help="Excel report path"
    ),
    live: bool = typer.Option(  # noqa: B008
        False, "--live", help="Execute git commands (default: dry-run)"
    ),  # noqa: B008
) -> None:
    """Standardize Git branches by generating a migration plan and reports.

    Args:
        outdir: Base output directory for reports and logs.
        report_file: Path to the text report file.
        logfile: Path to the log file.
        execution_plan: Path to the execution plan script.
        excel_report_file: Path to the Excel report file.
        live: Whether to execute git commands (default is dry-run).
    """
    start_time = datetime.now()

    if outdir:
        base_dir = outdir.resolve()
        base_dir.mkdir(parents=True, exist_ok=True)
        logging.info("Using user-specified output directory: %s", base_dir)
    else:
        base_dir = Path(f"/tmp/{USER}/{APP_NAME}/{TIMESTAMP}")
        base_dir.mkdir(parents=True, exist_ok=True)
        logging.info("Using default temporary output directory: %s", base_dir)

    report_path = report_file or (base_dir / f"{APP_NAME}_report.txt")
    log_path = logfile or (base_dir / f"{APP_NAME}.log")
    excel_path = excel_report_file or (base_dir / f"{APP_NAME}_report.xlsx")
    exec_plan_path = execution_plan or (base_dir / f"{APP_NAME}_execution_plan.txt")

    configure_logging(log_path)
    repo_path = Path.cwd()

    if not live:
        typer.echo("Executing DRY-RUN. Use --live to run live.", color=typer.colors.YELLOW)

    logging.info("Starting branch standardization v1.2.4 (live=%s)", live)

    git_fetch_all()
    branches = get_remote_branches()
    info_map = {b: get_branch_info(b) for b in branches}

    (
        namespaced,
        already_archived,
        production,
        essential,
        essential_renames,
        archive,
        to_feature,
        to_bugfix,
        to_hotfix,
        to_release,
    ) = plan_changes(branches, info_map)

    all_moves = archive + to_feature + to_bugfix + to_hotfix + to_release

    end_time = datetime.now()
    duration = end_time - start_time

    stats = {
        "branch-count": str(len(branches)),
        "archived-branch-count": str(len(already_archived)),
        "develop-branch-found": str(any(b.name == "develop" for b in essential)),
        "development-branch-found": str(any(b.name == "development" for b in essential)),
        "main-branch-found": str(any(b.name == "main" for b in essential)),
        "master-branch-found": str(any(b.name == "master" for b in essential)),
        "feature-branch-count": str(len([b for b in namespaced if b.name.startswith("feature/")])),
        "bugfix-branch-count": str(len([b for b in namespaced if b.name.startswith("bugfix/")])),
        "hotfix-branch-count": str(len([b for b in namespaced if b.name.startswith("hotfix/")])),
        "release-branch-count": str(len([b for b in namespaced if b.name.startswith("release/")])),
        "start-time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "end-time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration": str(duration).split(".")[0],
    }

    write_text_report(
        report_path,
        log_path,
        repo_path,
        stats,
        namespaced,
        already_archived,
        production,
        essential,
        archive,
        to_feature,
        to_bugfix,
        to_hotfix,
        to_release,
    )
    write_excel(
        excel_path,
        namespaced,
        already_archived,
        production,
        essential,
        archive,
        to_feature,
        to_bugfix,
        to_hotfix,
        to_release,
    )
    write_execution_plan(exec_plan_path, all_moves, essential_renames)

    print(f"Wrote the execution plan to '{exec_plan_path.resolve()}'")
    print(f"Wrote the Excel report file to '{excel_path.resolve()}'")
    print(f"Wrote the report file to '{report_path.resolve()}'")
    print(f"Wrote the log file to '{log_path.resolve()}'")

    if live and (all_moves or essential_renames):
        if typer.confirm("Execute the plan now? (LIVE MODE)", default=True):
            logging.info("Executing live plan...")
            exec_plan_path.chmod(0o755)
            subprocess.run([str(exec_plan_path)], check=True)
            typer.echo("Execution completed successfully.")
        else:
            typer.echo("Aborted.")
    elif live:
        typer.echo("No changes planned.")
    else:
        typer.echo("Dry-run complete. Re-run with --live to execute.")


if __name__ == "__main__":
    app()
