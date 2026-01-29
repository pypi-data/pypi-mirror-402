import sys
from pathlib import Path

import pytest

from suphia import cli
from suphia.cli import default_dest_path, find_workspace_root


def test_find_workspace_root_detects_marker(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    nested = root / "subdir"
    nested.mkdir(parents=True)
    (root / ".git").mkdir()

    assert find_workspace_root(nested) == root


def test_default_dest_path_env_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SUPHIA_WORKSPACE_ROOT", str(tmp_path))
    assert default_dest_path() == tmp_path / ".claude/skills"


def test_default_dest_path_workspace_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    nested = root / "subdir"
    nested.mkdir(parents=True)
    (root / ".vscode").mkdir()

    monkeypatch.chdir(nested)
    assert default_dest_path() == root / ".claude/skills"


def test_default_dest_path_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SUPHIA_WORKSPACE_ROOT", raising=False)
    monkeypatch.setattr(cli, "find_workspace_root", lambda _path: None)
    monkeypatch.chdir(tmp_path)
    assert default_dest_path() == tmp_path / ".claude/skills"


def test_main_skills_publish_invokes_publish(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {"value": False}

    def fake_publish(**_kwargs: object) -> None:
        called["value"] = True

    monkeypatch.setattr(cli, "publish_skills", fake_publish)
    monkeypatch.setattr(
        sys,
        "argv",
        ["suphia", "skills", "publish", "--source", ".", "--dry-run"],
    )

    cli.main()

    assert called["value"]


def test_main_prints_help(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["suphia"])

    with pytest.raises(SystemExit):
        cli.main()

    captured = capsys.readouterr()
    assert "usage" in captured.err.lower()
