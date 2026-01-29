#!/usr/bin/env python3
"""Main CLI entry point for jps-git-repo-utils.

This module provides a unified Typer application that combines all
the individual utility commands into a single CLI interface.
"""

import typer

from jps_git_repo_utils import audit_repository, repo_history, standardize_branches

app = typer.Typer(
    name="jps-git-repo-utils",
    help="Git repository management and standardization utilities",
    no_args_is_help=True,
)

# Register commands from submodules directly
app.command(name="standardize", help="Standardize branch naming conventions")(
    standardize_branches.main
)
app.command(name="audit", help="Audit repository for compliance issues")(
    audit_repository.check
)
app.command(name="history", help="Generate repository history reports")(
    repo_history.main
)


@app.command()
def version():
    """Display the version of jps-git-repo-utils."""
    from jps_git_repo_utils import __version__
    typer.echo(f"jps-git-repo-utils version {__version__}")


if __name__ == "__main__":
    app()
