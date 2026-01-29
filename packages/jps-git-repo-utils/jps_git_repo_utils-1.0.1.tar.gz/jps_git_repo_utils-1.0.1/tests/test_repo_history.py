"""Unit tests for ``repo_history.py``.

These tests validate Git-based repository history operations, ensuring correct
behavior of functions that execute Git commands, collect branch and tag
metadata, and generate textual summary reports. The module dynamically imports
``repo_history.py`` to allow direct testing outside a package context.

Coverage summary:
- ``run_git`` — executes valid commands and raises errors on invalid ones.
- ``fetch_all`` — verifies remote fetch behavior (skipped when offline).
- ``list_remote_branches`` — ensures invalid refs (e.g., origin/HEAD) are filtered.
- ``banner`` — checks section formatting and key–value rendering.
- ``write_report`` — validates report generation and expected section headers.
- ``tag_commit_hash`` and ``tag_metadata`` — confirm graceful handling of missing tags.

All tests are deterministic, avoid network dependencies unless explicitly marked,
and rely on pytest fixtures for isolated temporary repositories.
"""

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

repo_path = Path(__file__).resolve().parents[1] / "src" / "jps_git_repo_utils" / "repo_history.py"
spec = importlib.util.spec_from_file_location("repo_history", repo_path)
repo_history = importlib.util.module_from_spec(spec)

# ✅ ensure dataclass decorator can resolve __module__
sys.modules["repo_history"] = repo_history

spec.loader.exec_module(repo_history)


@pytest.mark.skipif(shutil.which("git") is None, reason="git CLI required for repo_history tests")
def test_run_git_valid_command(dummy_repo):
    """Verify that run_git executes valid Git commands and returns output.

    Args:
        dummy_repo: pytest fixture providing a temporary Git repository.
    """
    out = repo_history.run_git(["status"], cwd=dummy_repo)
    assert "On branch" in out


def test_run_git_invalid_command(dummy_repo):
    """Verify that run_git raises RuntimeError for invalid Git commands.

    Args:
        dummy_repo: pytest fixture providing a temporary Git repository.
    """
    with pytest.raises(RuntimeError):
        repo_history.run_git(["nonexistent-command"], cwd=dummy_repo)


@pytest.mark.skip(reason="Network-dependent test – requires a real remote repository.")
def test_fetch_all_requires_remote():
    """Ensure fetch_all logs a message and executes successfully when remotes exist."""
    repo_history.fetch_all()


@pytest.mark.skipif(shutil.which("git") is None, reason="git CLI required for branch detection")
def test_list_remote_branches_handles_invalid_refs(monkeypatch):
    """Simulate invalid refs like origin/HEAD and ensure they are filtered.

    Args:
        monkeypatch: pytest fixture to modify run_git behavior.
    """
    sample_output = "origin/main\norigin/origin\norigin/HEAD\n"
    monkeypatch.setattr(repo_history, "run_git", lambda args: sample_output)
    branches = repo_history.list_remote_branches()
    assert all(not b[0].endswith("origin") for b in branches)
    assert all(not b[0].endswith("HEAD") for b in branches)


def test_banner_formatting():
    """Validate the banner format consistency."""
    b = repo_history.banner(2, "Per-Branch Summary", {"branches": 3})
    assert "Section 2" in b
    assert "branches: 3" in b


def test_write_report_generates_expected_sections(tmp_path):
    """Ensure report file includes both Section 1 and Section 2 headers.

    Args:
        tmp_path: pytest fixture providing a temporary directory.
    """
    report_file = tmp_path / "report.txt"
    start, end = repo_history.datetime.now(), repo_history.datetime.now()
    logfile = tmp_path / "log.txt"

    dummy_branch = repo_history.BranchRecord(
        name="main",
        remote_ref="origin/main",
        creation=repo_history.BranchCreationInfo(
            branch="main",
            created_when="2025-01-01T00:00:00",
            created_by_name="Tester",
            created_by_email="tester@example.com",
            source_branch=None,
        ),
        commits=[
            repo_history.CommitInfo(
                commit_hash="abc123",
                commit_date="2025-01-01T00:00:00",
                committer_name="Tester",
                committer_email="tester@example.com",
            )
        ],
        merges=[],
        tags=[],
    )

    repo_history.write_report(
        report_file=report_file,
        start_time=start,
        end_time=end,
        logfile=logfile,
        repo_root=tmp_path,
        branch_records=[dummy_branch],
        tag_map={},
    )

    text = report_file.read_text()
    assert "Section 1" in text
    assert "Section 2" in text
    assert "Branch Name: main" in text


@pytest.mark.skipif(shutil.which("git") is None, reason="git CLI required for tag resolution")
def test_tag_commit_hash_and_metadata(monkeypatch):
    """Ensure tag_commit_hash() and tag_metadata() handle missing tags gracefully.

    Args:
        monkeypatch: pytest fixture to modify run_git behavior.
    """
    monkeypatch.setattr(repo_history, "run_git", lambda args, **kwargs: "")
    assert repo_history.tag_commit_hash("missing") is None
    name, email, date = repo_history.tag_metadata("missing")
    assert name is None and email is None and date is None
