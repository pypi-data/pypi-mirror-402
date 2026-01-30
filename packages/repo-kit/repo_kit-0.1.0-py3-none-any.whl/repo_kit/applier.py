from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from .templates_content import (
    bug_report_yml,
    feature_request_yml,
    pull_request_template_md,
    ci_workflow_yml,
    release_workflow_yml,
    readme_md,
    mit_license,
    contributing_md,
    code_of_conduct_md,
    keep_a_changelog,
    security_md,
)


@dataclass
class ApplyResult:
    actions: List[Tuple[Path, str]]


def _write_file(path: Path, content: str, force: bool) -> str:
    existed = path.exists()
    if existed and not force:
        return "skip"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return "overwrite" if existed else "write"


def apply_kit(repo_path: Path, stack: str = "generic", force: bool = False, author: str = "", year: str = "") -> ApplyResult:
    actions: List[Tuple[Path, str]] = []

    stack_norm = stack.lower().strip()
    if stack_norm not in {"generic", "python", "node", "go", "rust"}:
        stack_norm = "generic"

    # Core docs
    actions.append((repo_path / "README.md", _write_file(repo_path / "README.md", readme_md(stack_norm), force)))
    actions.append((repo_path / "LICENSE", _write_file(repo_path / "LICENSE", mit_license(author=author, year=year), force)))
    actions.append((repo_path / "CONTRIBUTING.md", _write_file(repo_path / "CONTRIBUTING.md", contributing_md(), force)))
    actions.append((repo_path / "CODE_OF_CONDUCT.md", _write_file(repo_path / "CODE_OF_CONDUCT.md", code_of_conduct_md(), force)))
    actions.append((repo_path / "CHANGELOG.md", _write_file(repo_path / "CHANGELOG.md", keep_a_changelog(), force)))
    actions.append((repo_path / "SECURITY.md", _write_file(repo_path / "SECURITY.md", security_md(), force)))

    # GitHub templates
    issue_dir = repo_path / ".github" / "ISSUE_TEMPLATE"
    actions.append((issue_dir / "bug_report.yml", _write_file(issue_dir / "bug_report.yml", bug_report_yml(), force)))
    actions.append((issue_dir / "feature_request.yml", _write_file(issue_dir / "feature_request.yml", feature_request_yml(), force)))

    actions.append(
        (
            repo_path / ".github" / "PULL_REQUEST_TEMPLATE.md",
            _write_file(repo_path / ".github" / "PULL_REQUEST_TEMPLATE.md", pull_request_template_md(), force),
        )
    )

    # Workflows
    wf_dir = repo_path / ".github" / "workflows"
    actions.append((wf_dir / "ci.yml", _write_file(wf_dir / "ci.yml", ci_workflow_yml(stack_norm), force)))
    actions.append((wf_dir / "release.yml", _write_file(wf_dir / "release.yml", release_workflow_yml(stack_norm), force)))

    # Simple release script (opt-in)
    scripts_dir = repo_path / "scripts"
    release_sh = scripts_dir / "release.sh"
    actions.append((release_sh, _write_file(release_sh, _release_script_sh(), force)))
    try:
        release_sh.chmod(0o755)
    except Exception:
        pass

    return ApplyResult(actions=actions)


def _release_script_sh() -> str:
    return """#!/usr/bin/env bash
set -euo pipefail

# A minimal manual release helper.
# - bumps a version file if you have one (optional)
# - creates an annotated git tag and pushes it

if ! command -v git >/dev/null; then
  echo "git not found" >&2
  exit 2
fi

VERSION=${1:-}
if [[ -z "$VERSION" ]]; then
  echo "usage: scripts/release.sh <version>" >&2
  echo "example: scripts/release.sh 0.1.0" >&2
  exit 2
fi

git status --porcelain

echo "Tagging v$VERSION"
git tag -a "v$VERSION" -m "v$VERSION"

echo "Pushing tag"
git push origin "v$VERSION"

echo "Done. GitHub Actions (release.yml) should publish the release." 
"""
