from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

GITHUB_RE = re.compile(r"^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$")


@dataclass
class CloneResult:
    path: Path
    owner: str
    repo: str
    url: str


def is_github_url(s: str) -> bool:
    return bool(GITHUB_RE.match(s.strip()))


def parse_github_url(url: str) -> Optional[Tuple[str, str]]:
    m = GITHUB_RE.match(url.strip())
    if not m:
        return None
    return m.group("owner"), m.group("repo")


def get_git_remote_origin(repo_path: Path) -> str:
    try:
        out = subprocess.check_output(["git", "-C", str(repo_path), "remote", "get-url", "origin"], text=True).strip()
        return out
    except Exception:
        return ""


def shallow_clone(url: str, keep: bool = False) -> CloneResult:
    parsed = parse_github_url(url)
    if not parsed:
        raise ValueError(f"Not a supported GitHub URL: {url}")
    owner, repo = parsed

    tmpdir = Path(tempfile.mkdtemp(prefix="repo-kit-"))
    dest = tmpdir / repo

    subprocess.check_call(["git", "clone", "--depth", "1", url, str(dest)])

    if keep:
        # user wants to keep the clone path, so do not register cleanup
        return CloneResult(path=dest, owner=owner, repo=repo, url=url)

    # if not keep: mark for cleanup by returning path; caller cleans up
    return CloneResult(path=dest, owner=owner, repo=repo, url=url)


def safe_rmtree(path: Path) -> None:
    try:
        shutil.rmtree(path)
    except Exception:
        pass
