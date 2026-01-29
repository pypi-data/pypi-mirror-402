#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lists all available CLI tools in the jps-git-repo-utils package.

This script provides a unified help command for developers and release
managers to understand the purpose of each entrypoint utility included
in this package.

Usage:
    jps-git-repo-utils-help
"""

import textwrap

# ANSI color codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def main() -> None:
    """Display help for all entrypoint scripts in this package."""
    help_text = textwrap.dedent(
        f"""
    🧰 jps-git-repo-utils — Available Commands
    ====================================================

    {GREEN}jps-git-repo-utils-audit{RESET}
        Audit repository health by detecting release-engineering anti-patterns:
        - Active PRs not targeting 'develop'
        - Hotfixes on 'main' missing from 'develop'
        - Overlapping file modifications among active feature branches

        Example:
            {YELLOW}jps-git-repo-utils-audit check ./my-repo --github{RESET}

    {GREEN}jps-git-repo-utils-standardize{RESET}
        Enforce branch naming conventions across repositories (see BISD-1181).

        Example:
            {YELLOW}jps-git-repo-utils-standardize ./my-repo --apply{RESET}

    {GREEN}jps-git-repo-utils-history{RESET}
        Analyze Git history for commit, PR, and contributor statistics.

        Example:
            {YELLOW}jps-git-repo-utils-history ./my-repo --summary{RESET}

    {GREEN}jps-git-repo-utils-help{RESET}
        Displays this overview of all available commands.

    ----------------------------------------------------
    Tip: Run each command with '--help' to see detailed options.
    """
    )

    print(help_text)


if __name__ == "__main__":
    main()
