from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .scanner import scan_repo
from .applier import apply_kit
from .badges import generate_badges
from .git_utils import is_github_url

app = typer.Typer(add_completion=False, help="Repo health check + one-command open-source kit.")
console = Console()


@app.command()
def scan(
    target: str = typer.Argument(..., help="Local path or GitHub URL (https://github.com/OWNER/REPO)."),
    format: str = typer.Option("table", "--format", "-f", help="Output: table|json|md"),
    fail_below: Optional[int] = typer.Option(None, help="Exit non-zero if score < this threshold."),
    keep_clone: bool = typer.Option(False, help="If target is a URL, keep the temporary clone directory."),
):
    """Scan a repo and output a Repo Score (0-100) + checklist."""
    report = scan_repo(target, keep_clone=keep_clone)

    if format == "json":
        console.print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    elif format == "md":
        console.print(report.to_markdown())
    else:
        table = Table(title=f"Repo Score: {report.score}/100")
        table.add_column("Check")
        table.add_column("Status")
        table.add_column("Notes")
        for item in report.items:
            table.add_row(item.name, "✅" if item.ok else "❌", item.notes or "")
        console.print(table)
        console.print(f"\nEmbed badge: {report.badge_markdown}")

    if fail_below is not None and report.score < fail_below:
        raise typer.Exit(code=2)


@app.command()
def apply(
    path: str = typer.Option(".", help="Local repository path (must exist)."),
    stack: str = typer.Option("generic", help="Template stack: generic|python|node|go|rust"),
    force: bool = typer.Option(False, help="Overwrite existing files."),
    author: str = typer.Option("", help="Author name for LICENSE header (optional)."),
    year: str = typer.Option("", help="Year for LICENSE header (optional)."),
):
    """Apply the professional open-source kit (safe by default)."""
    repo_path = Path(path).resolve()
    if not repo_path.exists():
        console.print(f"[red]Path does not exist:[/red] {repo_path}")
        raise typer.Exit(code=2)

    result = apply_kit(repo_path, stack=stack, force=force, author=author, year=year)

    table = Table(title="repo-kit apply")
    table.add_column("File")
    table.add_column("Action")
    for p, action in result.actions:
        table.add_row(str(p), action)
    console.print(table)


@app.command()
def badge(
    path: str = typer.Option(".", help="Local repository path."),
    no_shields: bool = typer.Option(False, help="Do not insert shields.io badges; only the local Repo Score badge."),
    force: bool = typer.Option(False, help="Overwrite .github/repo-score.svg and re-insert badges."),
):
    """Generate a local Repo Score badge SVG and insert badges into README."""
    repo_path = Path(path).resolve()
    report = scan_repo(str(repo_path), keep_clone=True)

    res = generate_badges(repo_path, report, include_shields=(not no_shields), force=force)

    table = Table(title="repo-kit badge")
    table.add_column("File")
    table.add_column("Action")
    for p, action in res.actions:
        table.add_row(str(p), action)
    console.print(table)
    if is_github_url(report.source):
        console.print("Tip: badges look best on GitHub when your default branch is 'main'.")


if __name__ == "__main__":
    app()
