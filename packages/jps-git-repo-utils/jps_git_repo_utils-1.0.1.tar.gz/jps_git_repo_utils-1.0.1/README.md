# jps-git-repo-utils

![Build](https://github.com/jai-python3/jps-git-repo-utils/actions/workflows/test.yml/badge.svg)
![Publish to PyPI](https://github.com/jai-python3/jps-git-repo-utils/actions/workflows/publish-to-pypi.yml/badge.svg)
[![codecov](https://codecov.io/gh/jai-python3/jps-git-repo-utils/branch/main/graph/badge.svg)](https://codecov.io/gh/jai-python3/jps-git-repo-utils)

---

## 🧭 Overview

**jps-git-repo-utils** is a collection of Python-based utility scripts designed to manage and standardize code repositories.  
These tools simplify common administrative tasks such as enforcing naming conventions, auditing branch
structures, generating repository history reports, and synchronizing version metadata.

### ✨ Key Features

- Automated enforcement of branch naming conventions (`feature/`, `bugfix/`, `hotfix/`, `release/`, etc.)
- Repository cleanup and archival of inactive branches
- Consistent versioning and repository metadata management
- Repository history generation with per-branch summaries and event classification
- Integration with Jira and CI/CD pipelines for reporting and audit purposes
- Robust testing framework using **pytest** with 100% reproducible local runs

---

## 🧩 Included Utilities

| Script | Description |
|--------|--------------|
| `standardize_branches.py` | Standardizes branch names, prefixes, and folders (feature, bugfix, hotfix, release). |
| `audit_repository.py` | Audits repository metadata, tags, and release consistency. |
| `repo_history.py` | Generates detailed repository history reports with per-branch summaries, tag events, and merge timelines. |

---

## 💻 Example Commands

### Using the unified CLI

```bash
# Display all available commands
jps-git-repo-utils --help

# Standardize branch naming
jps-git-repo-utils standardize /path/to/repository

# Audit repository for compliance
jps-git-repo-utils audit check /path/to/repository --github

# Generate repository history
jps-git-repo-utils history /path/to/repository --global-tags
```

### Using individual commands

```bash
jps-git-repo-utils-standardize --help
jps-git-repo-utils-audit --help
jps-git-repo-utils-history --help
```

### Using as a Python module

```bash
python -m jps_git_repo_utils.standardize_branches --repo /path/to/repository
python -m jps_git_repo_utils.repo_history --global-tags
```

---

## ⚙️ Installation

```bash
make install
```

---

## 🧪 Development Workflow

```bash
make fix && make format && make lint
make test
```

## Recent Additions

- Comprehensive pytest suite for `repo_history.py`
- Dummy Git repository fixtures for isolated test execution
- 6 passing tests and 1 intentionally skipped (network-dependent)

---

## 📦 Packaging and Distribution

This project follows semantic versioning and uses GitHub Actions for continuous integration,  
PyPI publishing, and test coverage reporting via **Codecov**.

---

## 📜 License

MIT License © Jaideep Sundaram
