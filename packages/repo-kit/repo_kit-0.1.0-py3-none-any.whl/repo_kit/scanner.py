from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .git_utils import is_github_url, shallow_clone, safe_rmtree
from .models import CheckItem, RepoReport

README_CANDIDATES = [
    "README.md",
    "README.MD",
    "README",
]

LICENSE_CANDIDATES = [
    "LICENSE",
    "LICENSE.md",
    "LICENSE.txt",
]

CONTRIB_CANDIDATES = [
    "CONTRIBUTING.md",
    "CONTRIBUTING",
    ".github/CONTRIBUTING.md",
]

CODE_OF_CONDUCT_CANDIDATES = [
    "CODE_OF_CONDUCT.md",
    ".github/CODE_OF_CONDUCT.md",
]

PR_TEMPLATE_CANDIDATES = [
    ".github/PULL_REQUEST_TEMPLATE.md",
    "PULL_REQUEST_TEMPLATE.md",
]

SECURITY_CANDIDATES = [
    "SECURITY.md",
    ".github/SECURITY.md",
]


def _exists_any(repo: Path, relpaths: List[str]) -> str:
    for rp in relpaths:
        if (repo / rp).exists():
            return rp
    return ""


def _read_text(repo: Path, relpath: str) -> str:
    try:
        return (repo / relpath).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _has_readme_sections(text: str) -> bool:
    # simple heuristic: look for common headings
    wanted = [
        r"^#{1,6}\s+installation\b",
        r"^#{1,6}\s+usage\b",
        r"^#{1,6}\s+contributing\b",
        r"^#{1,6}\s+license\b",
    ]
    flags = re.IGNORECASE | re.MULTILINE
    found = 0
    for pat in wanted:
        if re.search(pat, text, flags):
            found += 1
    return found >= 3


def _has_issue_templates(repo: Path) -> bool:
    d = repo / ".github" / "ISSUE_TEMPLATE"
    if not d.exists() or not d.is_dir():
        return False
    for p in d.glob("*"):
        if p.suffix.lower() in {".yml", ".yaml", ".md"}:
            return True
    return False


def _has_ci_workflow(repo: Path) -> bool:
    d = repo / ".github" / "workflows"
    if not d.exists() or not d.is_dir():
        return False
    ymls = list(d.glob("*.yml")) + list(d.glob("*.yaml"))
    if not ymls:
        return False
    # best-effort: any workflow file named ci/test or containing 'pytest'/'go test'/'npm test'/'cargo test'
    for wf in ymls:
        name = wf.name.lower()
        content = wf.read_text(encoding="utf-8", errors="ignore").lower()
        if "ci" in name or "test" in name:
            return True
        if any(k in content for k in ["pytest", "go test", "npm test", "cargo test", "gradle test", "mvn test"]):
            return True
    return True


def _has_release_workflow(repo: Path) -> bool:
    d = repo / ".github" / "workflows"
    if not d.exists() or not d.is_dir():
        return False
    ymls = list(d.glob("*.yml")) + list(d.glob("*.yaml"))
    for wf in ymls:
        name = wf.name.lower()
        content = wf.read_text(encoding="utf-8", errors="ignore").lower()
        if "release" in name:
            return True
        # tag-trigger heuristics
        if "tags:" in content and "push:" in content:
            return True
        if "workflow_dispatch" in content and "github release" in content:
            return True
    return False


def scan_repo(target: str, keep_clone: bool = False) -> RepoReport:
    source = target
    cloned_root: Path | None = None

    if is_github_url(target):
        clone = shallow_clone(target, keep=keep_clone)
        repo = clone.path
        if not keep_clone:
            cloned_root = repo.parent
    else:
        repo = Path(target).expanduser().resolve()

    items: List[CheckItem] = []

    readme_rel = _exists_any(repo, README_CANDIDATES)
    readme_ok = bool(readme_rel)
    items.append(CheckItem("readme", "README", readme_ok, 15, readme_rel or "missing"))

    readme_sections_ok = False
    if readme_ok:
        readme_text = _read_text(repo, readme_rel)
        readme_sections_ok = _has_readme_sections(readme_text)
    items.append(
        CheckItem(
            "readme_sections",
            "README sections (Installation/Usage/Contributing/License)",
            readme_sections_ok,
            10,
            "need at least 3 of 4 standard sections" if readme_ok else "README missing",
        )
    )

    lic_rel = _exists_any(repo, LICENSE_CANDIDATES)
    items.append(CheckItem("license", "LICENSE", bool(lic_rel), 10, lic_rel or "missing"))

    contrib_rel = _exists_any(repo, CONTRIB_CANDIDATES)
    items.append(CheckItem("contributing", "CONTRIBUTING", bool(contrib_rel), 8, contrib_rel or "missing"))

    coc_rel = _exists_any(repo, CODE_OF_CONDUCT_CANDIDATES)
    items.append(CheckItem("code_of_conduct", "CODE_OF_CONDUCT", bool(coc_rel), 7, coc_rel or "missing"))

    issue_templates_ok = _has_issue_templates(repo)
    items.append(CheckItem("issue_templates", "Issue templates", issue_templates_ok, 8, ".github/ISSUE_TEMPLATE"))

    pr_rel = _exists_any(repo, PR_TEMPLATE_CANDIDATES)
    items.append(CheckItem("pr_template", "PR template", bool(pr_rel), 5, pr_rel or "missing"))

    ci_ok = _has_ci_workflow(repo)
    items.append(CheckItem("ci", "CI workflow", ci_ok, 12, ".github/workflows"))

    release_ok = _has_release_workflow(repo)
    items.append(CheckItem("release", "Release workflow", release_ok, 10, ".github/workflows"))

    changelog_ok = (repo / "CHANGELOG.md").exists()
    items.append(CheckItem("changelog", "CHANGELOG", changelog_ok, 8, "CHANGELOG.md"))

    sec_rel = _exists_any(repo, SECURITY_CANDIDATES)
    items.append(CheckItem("security", "SECURITY policy", bool(sec_rel), 7, sec_rel or "missing"))

    score = sum(i.weight for i in items if i.ok)

    badge_markdown = "![Repo Score](./.github/repo-score.svg)"

    report = RepoReport(
        source=source,
        repo_path=str(repo),
        score=score,
        items=items,
        badge_markdown=badge_markdown,
    )

    if cloned_root is not None:
        safe_rmtree(cloned_root)

    return report
