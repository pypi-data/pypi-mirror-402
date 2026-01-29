#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Derive and report a repository's history (branches, commits, merges, and tags).

This will report a repository's full history into a timestamped text report, with
structured logging and a CLI.

Version: v1.2.0
Changes:
- Restored full reporting (Section 1 timeline + Section 2 per-branch summary)
- Remote-only analysis (use origin/<branch> for all git operations)
- Robust tag handling: derive tags via `git tag --list`, resolve with `rev-list`,
  and parse annotated metadata via `git cat-file -p` (works for lightweight tags too)
- Event classification: 'tagged' vs 'committed' vs 'merged' (no dup events)
- Optional --global-tags (default False) to include all tags or only those
  reachable from analyzed remote branches
- Filtering of invalid remote refs (origin/HEAD, origin/origin, and similar)
- Graceful handling when a branch's git commands fail (warn and continue)
"""

from __future__ import annotations

import getpass
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import typer

# -------------------------------------------------------------
# Configuration
# -------------------------------------------------------------

DEFAULT_PRIMARY_BRANCHES: List[str] = [
    "main",
    "master",
    "develop",
    "development",
    "production",
]

REMOTE_NAME: str = "origin"


# -------------------------------------------------------------
# Data models
# -------------------------------------------------------------


@dataclass
class CommitInfo:
    """Lightweight commit information container."""

    commit_hash: str
    commit_date: str  # ISO 8601 string
    committer_name: str
    committer_email: str


@dataclass
class BranchCreationInfo:
    """Information we can infer about branch creation."""

    branch: str
    created_when: Optional[str]  # ISO 8601 string or None if unknown
    created_by_name: Optional[str]
    created_by_email: Optional[str]
    source_branch: Optional[str]  # heuristic (remote-ref style when known)


@dataclass
class MergeEvent:
    """Represents a detected merge event likely involving the branch."""

    branch: str  # subject branch (short name)
    merged_into: Optional[str]  # if we can parse target from message
    merged_when: str  # ISO 8601
    merged_by_name: str
    merged_by_email: str
    merge_commit: str
    raw_message_first_line: str


@dataclass
class TagEvent:
    """Represents a tagging event observed on a commit contained in the branch."""

    branch: str  # short branch name for reporting
    tag: str
    tag_when: Optional[str]  # ISO 8601, None if lightweight tag with no date
    tagged_by_name: Optional[str]
    tagged_by_email: Optional[str]
    tag_commit: str  # commit hash the tag points to


@dataclass
class BranchRecord:
    """Complete record for a single branch across categories."""

    name: str  # short branch name for display
    remote_ref: str  # origin/<short>
    creation: BranchCreationInfo
    commits: List[CommitInfo] = field(default_factory=list)
    merges: List[MergeEvent] = field(default_factory=list)
    tags: List[TagEvent] = field(default_factory=list)


# -------------------------------------------------------------
# Utility functions
# -------------------------------------------------------------


def run_git(args: Sequence[str], cwd: Optional[Path] = None) -> str:
    """Run a git command and return stdout as text.

    Args:
        args: Arguments after the `git` command.
        cwd: The directory to execute in.

    Returns:
        The command's stdout as text.

    Raises:
        RuntimeError: if git command fails.
    """
    cmd = ["git", "--no-pager", *args]
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def fetch_all() -> None:
    """Fetch all refs and prune using the remote configuration."""
    logging.info("Fetching from all remotes with prune")
    run_git(["fetch", "--all", "--prune"])


def detect_repo_root() -> Path:
    """Detect the repository root directory.

    Returns:
        The Path to the repository root.
    """
    out = run_git(["rev-parse", "--show-toplevel"]).strip()
    return Path(out).resolve()


def _looks_like_invalid_remote_ref(short_or_full: str) -> bool:
    """Filter out pseudo-branches such as origin/HEAD, origin/origin, etc.

    Args:
        short_or_full: Short or full remote ref string.

    Returns:
        True if it looks invalid, False otherwise.
    """
    s = short_or_full.strip()
    if not s:
        return True
    # full refs come as 'origin/foo'; short names as 'foo'
    if s.endswith("/HEAD") or s.endswith("/origin"):
        return True
    if s.count("/") <= 1 and s == "origin":
        return True
    if "/origin/" in s:
        # e.g., origin/origin or origin/origin/HEAD
        return True
    return False


def list_remote_branches() -> List[Tuple[str, str]]:
    """List all remote branches as (short_name, full_remote_ref).

    Returns:
        A list of tuples containing short branch names and their full remote references.
    """
    remotes_raw = run_git(
        ["for-each-ref", "--format=%(refname:short)", f"refs/remotes/{REMOTE_NAME}/"]
    )
    branches: List[Tuple[str, str]] = []
    for r in remotes_raw.splitlines():
        r = r.strip()
        if _looks_like_invalid_remote_ref(r):
            continue
        # r is like 'origin/feature/foo' → short is the part after first '/'
        short_name = r.split("/", 1)[1] if "/" in r else r
        if _looks_like_invalid_remote_ref(short_name):
            continue
        branches.append((short_name, f"{REMOTE_NAME}/{short_name}"))
    logging.info("Detected %d valid remote branches from %s", len(branches), REMOTE_NAME)
    return branches


def _best_source_branch_for(branch_ref: str, candidates: Sequence[str]) -> Optional[str]:
    """Heuristically choose a source branch for the given remote ref.

    Args:
        branch_ref: Full remote ref (e.g., origin/feature/foo).
        candidates: List of candidate remote refs to consider as source.

    Returns:
        The best matching candidate remote ref, or None if none found.
    """
    best_name = None
    best_when = None
    for cand in candidates:
        if cand == branch_ref:
            continue
        try:
            mb = run_git(["merge-base", branch_ref, cand]).strip()
            when = run_git(["show", "-s", "--format=%ci", mb]).strip()
        except Exception:
            continue
        if not when:
            continue
        if best_when is None or when > best_when:
            best_when = when
            best_name = cand
    return best_name


def unique_commit_list(remote_ref: str) -> List[CommitInfo]:
    """Return the commits reachable from the remote branch.

    Args:
        remote_ref: Full remote ref (e.g., origin/feature/foo).

    Returns:
        A list of CommitInfo objects in chronological order.
    """
    fmt = "%H%x1f%ci%x1f%cn%x1f%ce%x1e"
    try:
        raw = run_git(["log", "--date=iso-strict", f"--pretty=format:{fmt}", remote_ref])
    except RuntimeError as e:
        logging.warning("Skipping branch %s due to git error: %s", remote_ref, e)
        return []
    commits: List[CommitInfo] = []
    for record in raw.split("\x1e"):
        if not record.strip():
            continue
        parts = record.strip().split("\x1f")
        if len(parts) == 4:
            commits.append(CommitInfo(*parts))
    commits.reverse()
    return commits


def infer_creation_info(
    short_name: str, remote_ref: str, all_refs: Sequence[str], primary_branches: Sequence[str]
) -> BranchCreationInfo:
    """Infer branch creation metadata.

    Args:
        short_name: Short branch name.
        remote_ref: Full remote ref (e.g., origin/feature/foo).
        all_refs: All remote refs detected.
        primary_branches: List of primary branch names for source inference.

    Returns:
        A BranchCreationInfo object.
    """
    commits = unique_commit_list(remote_ref)
    created_when = created_by_name = created_by_email = None
    if commits:
        first = commits[0]
        created_when = first.commit_date
        created_by_name = first.committer_name
        created_by_email = first.committer_email
    candidate_pool = [
        f"{REMOTE_NAME}/{b}" for b in primary_branches if f"{REMOTE_NAME}/{b}" in all_refs
    ]
    candidate_pool += [r for r in all_refs if r not in candidate_pool]
    source = _best_source_branch_for(remote_ref, candidate_pool)
    return BranchCreationInfo(short_name, created_when, created_by_name, created_by_email, source)


_MERGE_PATTERNS = [
    re.compile(r"Merge (?:remote-tracking )?branch '([^']+)'(?: into ([^\s]+))?", re.I),
    re.compile(r"Merge pull request #\d+ from [^/\s]+/([^\s]+)", re.I),
    re.compile(r"Squash(?:ed)? merge (?:of )?'([^']+)'(?: into ([^\s]+))?", re.I),
    re.compile(r"Merge branch \"([^\"]+)\"(?: into ([^\s]+))?", re.I),
]


def _parse_merge_subject(subject: str) -> Tuple[Optional[str], Optional[str]]:
    """Try multiple common patterns to extract (merged_branch, merged_into).

    Args:
        subject: The commit subject line.

    Returns:
        A tuple of (merged_branch, merged_into) or (None, None) if not
    """
    for pat in _MERGE_PATTERNS:
        m = pat.search(subject)
        if m:
            merged_branch = m.group(1)
            merged_into = m.group(2) if m.lastindex and m.lastindex >= 2 else None
            return (
                merged_branch.split("/")[-1] if "/" in merged_branch else merged_branch
            ), merged_into
    return None, None


def detect_merge_events(short_name: str) -> List[MergeEvent]:
    """Detect merge commits that mention the branch by name in the subject.

    Args:
        short_name: Short branch name.

    Returns:
        A list of MergeEvent objects for merges involving the branch.
    """
    fmt = "%H%x1f%ci%x1f%cn%x1f%ce%x1f%s%x1e"
    raw = run_git(["log", "--all", "--merges", f"--pretty=format:{fmt}"])
    events: List[MergeEvent] = []
    for record in raw.split("\x1e"):
        if not record.strip():
            continue
        parts = record.strip().split("\x1f")
        if len(parts) != 5:
            continue
        commit, when, name, email, subject = parts
        merged_branch, merged_into = _parse_merge_subject(subject)
        if merged_branch == short_name:
            events.append(MergeEvent(short_name, merged_into, when, name, email, commit, subject))
    events.sort(key=lambda e: e.merged_when)
    return events


# --------------------
# Tag helpers
# --------------------


def list_all_tags() -> List[str]:
    """Return a simple list of tag names.

    Returns:
        A list of tag names as strings.
    """
    out = run_git(["tag", "--list"])
    return [t.strip() for t in out.splitlines() if t.strip()]


def tag_commit_hash(tag: str) -> Optional[str]:
    """Resolve a tag to its commit hash (works for lightweight and annotated).

    Args:
        tag: Tag name.

    Returns:
        The commit hash the tag points to, or None if not found.
    """
    try:
        out = run_git(["rev-list", "-n", "1", tag]).strip()
        return out or None
    except RuntimeError:
        return None


_TAGGER_RE = re.compile(r"^tagger\s+(.+?)\s+<([^>]+)>\s+(.+)$")


def tag_metadata(tag: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Return (tagger_name, tagger_email, tagger_date) if annotated, else (None, None, None).

    Args:
        tag: Tag name.

    Returns:
        A tuple of (tagger_name, tagger_email, tagger_date) or (None, None, None) if lightweight tag.
    """
    try:
        blob = run_git(["cat-file", "-p", f"refs/tags/{tag}"])
    except RuntimeError:
        return None, None, None
    for line in blob.splitlines():
        m = _TAGGER_RE.match(line)
        if m:
            name, email, date = m.group(1), m.group(2), m.group(3)
            return name, email, date
        if line.strip() == "":  # header terminator
            break
    return None, None, None


def build_tag_map(
    global_tags: bool, reachable_commits: Optional[set[str]] = None
) -> Dict[str, List[Tuple[str, Optional[str], Optional[str], Optional[str]]]]:
    """Map commit_hash -> [(tag, date, tagger_name, tagger_email), ...].

    Args:
        global_tags: Whether to include all tags or only those reachable from branches.
        reachable_commits: Set of commit hashes reachable from branches (if global_tags is False).

    Returns:
        A mapping of commit_hash to list of tag info tuples.
    """
    mapping: Dict[str, List[Tuple[str, Optional[str], Optional[str], Optional[str]]]] = {}
    for tag in list_all_tags():
        commit = tag_commit_hash(tag)
        if not commit:
            continue
        if not global_tags and reachable_commits is not None and commit not in reachable_commits:
            continue
        tname, temail, tdate = tag_metadata(tag)
        mapping.setdefault(commit, []).append((tag, tdate, tname, temail))
    return mapping


def detect_tag_events(
    short_name: str,
    commit_list: List[CommitInfo],
    tag_map: Dict[str, List[Tuple[str, Optional[str], Optional[str], Optional[str]]]],
) -> List[TagEvent]:
    """Associate tag events to commits reachable from the branch.

    Args:
        short_name: Short branch name.
        commit_list: List of CommitInfo objects for the branch.
        tag_map: Mapping of commit_hash to tag info.

    Returns:
        List of TagEvent objects for tags on commits in the branch.
    """
    events: List[TagEvent] = []
    for c in commit_list:
        if c.commit_hash not in tag_map:
            continue
        for tag, date, tname, temail in tag_map[c.commit_hash]:
            events.append(TagEvent(short_name, tag, date, tname, temail, c.commit_hash))
    events.sort(key=lambda t: (t.tag_when or "", t.tag, t.tag_commit))
    return events


# -------------------------------------------------------------
# Report generation
# -------------------------------------------------------------


def banner(section_number: int, description: str, tallies: Dict[str, int]) -> str:
    """Create a standardized section banner with tallies.

    Args:
        section_number: The section number.
        description: The section description.
        tallies: A dictionary of tally names to values.

    Returns:
        The formatted banner string.
    """
    lines = [
        "##--------------------------------------------------------------",
        "##",
        f"## Section {section_number}: {description}",
    ]
    if tallies:
        tally_str = " | ".join(f"{k}: {v}" for k, v in tallies.items())
        lines.append(f"## {tally_str}")
    lines.append("##--------------------------------------------------------------")
    return "\n".join(lines)


def write_report(
    report_file: Path,
    start_time: datetime,
    end_time: datetime,
    logfile: Path,
    repo_root: Path,
    branch_records: List[BranchRecord],
    tag_map: Dict[str, List[Tuple[str, Optional[str], Optional[str], Optional[str]]]],
    reverse: bool = False,
) -> None:
    """Write the repository history report according to the SRS.

    Args:
        report_file: Path to the report file to write.
        start_time: When the analysis started.
        end_time: When the analysis ended.
        logfile: Path to the log file.
        repo_root: Path to the repository root.
        branch_records: List of BranchRecord objects.
        tag_map: Mapping of commit_hash to tag info.
        reverse: Whether to list newest events first.
    """
    duration = end_time - start_time
    user = getpass.getuser()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    branch_count = len(branch_records)
    tag_count = sum(len(b.tags) for b in branch_records)
    commit_count = sum(len(b.commits) for b in branch_records)
    merge_count = sum(len(b.merges) for b in branch_records)

    tagged_commits = set(tag_map.keys())

    with report_file.open("w", encoding="utf-8") as fh:
        # Header (key/value) block
        fh.write("## method-created: " + os.path.abspath(__file__) + "\n")
        fh.write(f"## date-created: {created_at}\n")
        fh.write(f"## created-by: {user}\n")
        fh.write(f"## logfile: {os.path.abspath(str(logfile))}\n")
        fh.write(f"## code-repository: {str(repo_root)}\n")
        fh.write(f"## current-working-directory: {os.path.abspath(os.getcwd())}\n")
        fh.write(f"## branch-count: {branch_count}\n")
        fh.write(f"## tag-count: {tag_count}\n")
        fh.write(f"## start-time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        fh.write(f"## end-time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        total_seconds = int(duration.total_seconds())
        hh, mm, ss = total_seconds // 3600, (total_seconds % 3600) // 60, total_seconds % 60
        fh.write(f"## duration: {hh:02d}:{mm:02d}:{ss:02d}\n\n")

        # Section 1 — timeline
        tallies = {
            "branches": branch_count,
            "commits": commit_count,
            "merges": merge_count,
            "tags": tag_count,
        }
        fh.write(banner(1, "Repository History", tallies) + "\n\n")

        timeline: List[Tuple[str, str, str, str, Optional[str], str, str]] = []
        for b in branch_records:
            if b.creation.created_when:
                timeline.append(
                    (
                        b.creation.created_when,
                        b.name,
                        "created",
                        b.creation.created_when,
                        None,
                        b.creation.created_by_name or "",
                        b.creation.created_by_email or "",
                    )
                )
            for c in b.commits:
                event = "tagged" if c.commit_hash in tagged_commits else "committed"
                timeline.append(
                    (
                        c.commit_date,
                        b.name,
                        event,
                        c.commit_date,
                        c.commit_hash,
                        c.committer_name,
                        c.committer_email,
                    )
                )
            for m in b.merges:
                timeline.append(
                    (
                        m.merged_when,
                        b.name,
                        "merged",
                        m.merged_when,
                        m.merge_commit,
                        m.merged_by_name,
                        m.merged_by_email,
                    )
                )
            # No need to append explicit tag events if we already classify the commit as 'tagged' above;
            # however, include tag-only entries when tag has date but commit wasn't listed (edge case).
            for t in b.tags:
                if t.tag_commit not in tagged_commits:
                    timeline.append(
                        (
                            t.tag_when or "",
                            b.name,
                            "tagged",
                            t.tag_when or "",
                            t.tag_commit,
                            t.tagged_by_name or "",
                            t.tagged_by_email or "",
                        )
                    )

        timeline.sort(key=lambda x: x[0] or "")
        if reverse:
            timeline.reverse()

        for _order_key, branch, event, date, commit_hash, actor, actor_email in timeline:
            fh.write(f"Branch Name: {branch}\n")
            fh.write(f"Event: {event}\n")
            fh.write(f"Date of Event: {date}\n")
            fh.write(f"Commit Hash: {commit_hash or ''}\n")
            fh.write(f"Actor: {actor}\n")
            fh.write(f"Actor Email: {actor_email}\n\n")

        # Section 2 — per-branch summary
        fh.write(banner(2, "Per-Branch Summary", {"branches": branch_count}) + "\n\n")
        for b in branch_records:
            if b.commits:
                first_commit_date = b.commits[0].commit_date
                first_actor = b.commits[0].committer_name
                first_email = b.commits[0].committer_email
            elif b.merges:
                first_commit_date = b.merges[0].merged_when
                first_actor = b.merges[0].merged_by_name
                first_email = b.merges[0].merged_by_email
            elif b.tags:
                first_commit_date = b.tags[0].tag_when or "(unknown)"
                first_actor = b.tags[0].tagged_by_name or "(unknown)"
                first_email = b.tags[0].tagged_by_email or "(unknown)"
            else:
                first_commit_date = "(unknown)"
                first_actor = "(unknown)"
                first_email = "(unknown)"

            last_event_date = "(none)"
            last_event_type = "(none)"
            if b.tags:
                last_event_date = b.tags[-1].tag_when or "(unknown)"
                last_event_type = "tagged"
            elif b.merges:
                last_event_date = b.merges[-1].merged_when
                last_event_type = "merged"
            elif b.commits:
                last_event_date = b.commits[-1].commit_date
                last_event_type = "committed"

            fh.write(f"Branch: {b.name}\n")
            fh.write(f"  Created: {first_commit_date}\n")
            fh.write(f"  Created By: {first_actor} <{first_email}>\n")
            fh.write(f"  Source (heuristic): {b.creation.source_branch or '(unknown)'}\n")
            fh.write(f"  Last Activity: {last_event_date} ({last_event_type})\n")
            fh.write(
                f"  Commits: {len(b.commits)}  Merges: {len(b.merges)}  Tags: {len(b.tags)}\n\n"
            )


# -------------------------------------------------------------
# CLI and orchestration
# -------------------------------------------------------------


def default_paths() -> Tuple[Path, Path, Path]:
    """Compute default outdir, report_file, and logfile paths.

    Returns:
        A tuple of (outdir, report_file, logfile) Paths.
    """
    user = getpass.getuser()
    script_base = Path(__file__).stem
    ts = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    outdir = Path("/tmp") / user / script_base / ts
    report_file = outdir / f"{script_base}_report.txt"
    logfile = outdir / f"{script_base}.log"
    return outdir, report_file, logfile


def configure_logging(logfile: Path) -> None:
    """Configure logging to file (INFO+) and stderr (WARNING+).

    Args:
        logfile: Path to the log file.
    """
    logfile.parent.mkdir(parents=True, exist_ok=True)
    fmt = "%(levelname)s : %(asctime)s : %(pathname)s : %(lineno)d : %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    fh = logging.FileHandler(str(logfile), encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
    sh = logging.StreamHandler()
    sh.setLevel(logging.WARNING)
    sh.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
    logging.basicConfig(level=logging.INFO, handlers=[fh, sh])


app = typer.Typer(help="Derive and report the full history of a Git repository.")


@app.command()
def main(
    outdir: Optional[Path] = typer.Option(None, "--outdir"),  # noqa: B008
    report_file: Optional[Path] = typer.Option(None, "--report-file"),  # noqa: B008
    logfile: Optional[Path] = typer.Option(None, "--logfile"),  # noqa: B008
    primary_branches: Optional[List[str]] = typer.Option(None, "--primary-branches"),  # noqa: B008
    global_tags: bool = typer.Option(  # noqa: B008
        False,
        "--global-tags",
        help="Include all tags globally instead of restricting to remote branches.",
    ),
    reverse: bool = typer.Option(  # noqa: B008
        False, "--reverse", help="List newest events first."
    ),  # noqa: B008
    branch: Optional[str] = typer.Option(  # noqa: B008
        None,
        "--branch",
        help="Comma-separated list of branch names to include (short names). If omitted, all remote branches are analyzed.",  # noqa: E501
    ),
) -> None:
    """Program entry point.

    Args:
        outdir: Output directory for report and log files.
        report_file: Path to the report file.
        logfile: Path to the log file.
        primary_branches: List of primary branch names for creation inference.
        global_tags: Whether to include all tags or only those reachable from branches.
        reverse: Whether to list newest events first in the report.
        branch: Comma-separated list of branch names to include (short names). If omitted, all remote branches are analyzed.  # noqa: E501
    """
    start_time = datetime.now()
    def_outdir, def_report, def_log = default_paths()
    outdir = outdir or def_outdir
    report_file = report_file or def_report
    logfile = logfile or def_log
    outdir.mkdir(parents=True, exist_ok=True)
    configure_logging(logfile)

    repo_root = detect_repo_root()
    fetch_all()

    remote_branches = list_remote_branches()
    if not remote_branches:
        logging.warning("No valid remote branches detected under %s", REMOTE_NAME)

    # Apply branch filter if requested
    if branch:
        requested = {b.strip() for b in branch.split(",") if b.strip()}
        logging.info("Branch filter enabled. Requested branches: %s", sorted(requested))

        before = len(remote_branches)
        remote_branches = [(short, full) for (short, full) in remote_branches if short in requested]
        after = len(remote_branches)

        if after == 0:
            logging.warning(
                "No requested branches were found on the remote. Requested: %s",
                ", ".join(sorted(requested)),
            )
        else:
            logging.info(
                "Filtered branches: retained %d of %d detected remote branches.",
                after,
                before,
            )

    all_refs = [r for (_, r) in remote_branches]

    # Gather commits for tag reachability filtering
    commits_from_all = set()
    for _, remote_ref in remote_branches:
        for c in unique_commit_list(remote_ref):
            commits_from_all.add(c.commit_hash)

    tag_map = build_tag_map(global_tags, commits_from_all)
    selected_primary = primary_branches or DEFAULT_PRIMARY_BRANCHES

    records: List[BranchRecord] = []
    for short_name, remote_ref in remote_branches:
        creation = infer_creation_info(short_name, remote_ref, all_refs, selected_primary)
        commits = unique_commit_list(remote_ref)
        merges = detect_merge_events(short_name)
        tags = detect_tag_events(short_name, commits, tag_map)
        records.append(BranchRecord(short_name, remote_ref, creation, commits, merges, tags))

    end_time = datetime.now()

    write_report(
        report_file=report_file,
        start_time=start_time,
        end_time=end_time,
        logfile=logfile,
        repo_root=repo_root,
        branch_records=records,
        tag_map=tag_map,
        reverse=reverse,
    )

    print(f"Wrote the report file to '{os.path.abspath(str(report_file))}'")
    print(f"Wrote the log file to '{os.path.abspath(str(logfile))}'")


if __name__ == "__main__":  # pragma: no cover
    app()
