from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class CheckItem:
    key: str
    name: str
    ok: bool
    weight: int
    notes: str = ""


@dataclass
class RepoReport:
    source: str
    repo_path: str
    score: int
    items: List[CheckItem]
    badge_markdown: str

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "repo_path": self.repo_path,
            "score": self.score,
            "badge_markdown": self.badge_markdown,
            "items": [
                {
                    "key": i.key,
                    "name": i.name,
                    "ok": i.ok,
                    "weight": i.weight,
                    "notes": i.notes,
                }
                for i in self.items
            ],
        }

    def to_markdown(self) -> str:
        lines = []
        lines.append(f"# Repo Score: {self.score}/100\n")
        lines.append(self.badge_markdown)
        lines.append("\n\n| Check | Status | Notes |")
        lines.append("|---|---:|---|")
        for i in self.items:
            status = "✅" if i.ok else "❌"
            notes = i.notes.replace("\n", " ")
            lines.append(f"| {i.name} | {status} | {notes} |")
        return "\n".join(lines) + "\n"
