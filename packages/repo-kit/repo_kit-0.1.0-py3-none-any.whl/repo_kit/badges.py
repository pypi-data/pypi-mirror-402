from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional

from .git_utils import get_git_remote_origin, parse_github_url
from .models import RepoReport
from .score_svg import BadgeSpec, make_badge_svg


@dataclass
class BadgeResult:
    actions: List[Tuple[Path, str]]


def _infer_slug(repo_path: Path, report: RepoReport) -> Optional[Tuple[str, str]]:
    # Prefer the scan source if it is a GitHub URL
    if report.source and report.source.startswith("http"):
        parsed = parse_github_url(report.source)
        if parsed:
            return parsed

    origin = get_git_remote_origin(repo_path)
    if not origin:
        return None

    # supports https://github.com/OWNER/REPO(.git)? and git@github.com:OWNER/REPO.git
    m = re.match(r"^https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", origin.strip())
    if m:
        return m.group(1), m.group(2)
    m = re.match(r"^git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", origin.strip())
    if m:
        return m.group(1), m.group(2)
    return None


def _readme_path(repo_path: Path) -> Optional[Path]:
    for cand in ["README.md", "README.MD", "README"]:
        p = repo_path / cand
        if p.exists() and p.is_file():
            return p
    return None


def _insert_badge_block(readme: str, badge_line: str) -> str:
    if "repo-score.svg" in readme:
        return readme

    lines = readme.splitlines()
    if not lines:
        return badge_line + "\n"

    # insert after the first Markdown H1 title if present
    for idx, line in enumerate(lines[:10]):
        if line.startswith("# "):
            insert_at = idx + 1
            # skip blank line
            if insert_at < len(lines) and lines[insert_at].strip() == "":
                insert_at += 1
            lines.insert(insert_at, badge_line)
            return "\n".join(lines) + "\n"

    # otherwise put at top
    return badge_line + "\n\n" + readme


def generate_badges(repo_path: Path, report: RepoReport, include_shields: bool = True, force: bool = False) -> BadgeResult:
    actions: List[Tuple[Path, str]] = []

    # 1) generate local svg badge
    svg_path = repo_path / ".github" / "repo-score.svg"
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    existed = svg_path.exists()
    if existed and not force:
        actions.append((svg_path, "skip"))
    else:
        svg = make_badge_svg(BadgeSpec(label="repo score", value=f"{report.score}/100"))
        svg_path.write_text(svg, encoding="utf-8")
        actions.append((svg_path, "overwrite" if existed else "write"))

    # 2) insert badge(s) into README
    readme_path = _readme_path(repo_path)
    if readme_path is None:
        actions.append((repo_path / "README.md", "missing"))
        return BadgeResult(actions=actions)

    slug = _infer_slug(repo_path, report)
    shields = ""
    if include_shields and slug:
        owner, repo = slug
        shields = " ".join(
            [
                f"![CI](https://img.shields.io/github/actions/workflow/status/{owner}/{repo}/ci.yml?branch=main)",
                f"![License](https://img.shields.io/github/license/{owner}/{repo})",
                f"![Stars](https://img.shields.io/github/stars/{owner}/{repo}?style=social)",
            ]
        )

    badge_line = f"![Repo Score](./.github/repo-score.svg)" + (" " + shields if shields else "")

    old = readme_path.read_text(encoding="utf-8", errors="ignore")
    new = _insert_badge_block(old, badge_line)
    if new != old:
        readme_path.write_text(new, encoding="utf-8")
        actions.append((readme_path, "update"))
    else:
        actions.append((readme_path, "skip"))

    return BadgeResult(actions=actions)
