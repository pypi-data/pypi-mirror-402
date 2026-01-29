import os
import sys
from pathlib import Path

import pytest

from suphia.filesystem import create_link, get_filesystem_type, wslpath_to_windows


def test_get_filesystem_type_linux(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(os, "uname", lambda: type("U", (), {"release": "generic"})())
    assert get_filesystem_type(tmp_path) == "linux"


def test_get_filesystem_type_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "win32")
    assert get_filesystem_type(Path("C:/repo")) == "windows"


def test_create_link_copy_mode(tmp_path: Path) -> None:
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    src.mkdir()
    (src / "SKILL.md").write_text("# skill")

    create_link(src, dest, mode="copy", dry_run=False)

    assert (dest / "SKILL.md").exists()


def test_create_link_symlink_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    src.mkdir()
    (src / "SKILL.md").write_text("# skill")

    called = {"value": False}

    def fake_create_symlink(*_args: object, **_kwargs: object) -> None:
        called["value"] = True

    monkeypatch.setattr("suphia.filesystem.get_filesystem_type", lambda _path: "linux")
    monkeypatch.setattr("suphia.filesystem.create_symlink", fake_create_symlink)

    create_link(src, dest, mode="link", dry_run=False)

    assert called["value"]


def test_create_link_windows_junction_dry_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    src.mkdir()

    called = {"value": False}

    def fake_create_junction(*_args: object, **_kwargs: object) -> None:
        called["value"] = True

    monkeypatch.setattr(
        "suphia.filesystem.get_filesystem_type", lambda _path: "windows"
    )
    monkeypatch.setattr("suphia.filesystem.create_junction", fake_create_junction)

    create_link(src, dest, mode="link", dry_run=True)

    assert called["value"]


def test_wslpath_to_windows_invokes_subprocess(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Result:
        stdout = "C:\\path"

    def fake_run(*_args: object, **_kwargs: object) -> Result:
        return Result()

    monkeypatch.setattr("subprocess.run", fake_run)

    assert wslpath_to_windows("/mnt/c/path") == "C:\\path"


def test_wslpath_to_windows_raises_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*_args: object, **_kwargs: object) -> None:
        raise FileNotFoundError

    monkeypatch.setattr("subprocess.run", fake_run)

    with pytest.raises(RuntimeError):
        wslpath_to_windows("/mnt/c/path")
