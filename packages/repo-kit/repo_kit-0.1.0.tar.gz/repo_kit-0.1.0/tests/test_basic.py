from pathlib import Path

from repo_kit.applier import apply_kit
from repo_kit.scanner import scan_repo


def test_apply_then_scan(tmp_path: Path):
    apply_kit(tmp_path, stack="python", force=False)

    report = scan_repo(str(tmp_path), keep_clone=True)
    # after applying, score should be 100
    assert report.score == 100

    # badge should reference local svg
    assert "repo-score.svg" in report.badge_markdown


def test_scan_empty_repo(tmp_path: Path):
    report = scan_repo(str(tmp_path), keep_clone=True)
    # empty repo should score low
    assert report.score < 40
