import os
from pathlib import Path

import pytest

from suphia.skills.publish import publish_skills


def test_publish_skills_dry_run_empty(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    dest = tmp_path / "dest"

    publish_skills(
        source=source,
        dest=dest,
        mode="link",
        force=False,
        backup=False,
        clean=False,
        dry_run=True,
        excludes=[],
    )

    captured = capsys.readouterr()
    assert "No skills found" in captured.out


def test_publish_skills_conflict_requires_force(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source_skill = source / "skill"
    source_skill.mkdir(parents=True)
    (source_skill / "SKILL.md").write_text("# skill")

    dest.mkdir()
    (dest / "skill").mkdir()

    with pytest.raises(SystemExit):
        publish_skills(
            source=source,
            dest=dest,
            mode="link",
            force=False,
            backup=False,
            clean=False,
            dry_run=True,
            excludes=[],
        )

    captured = capsys.readouterr()
    assert "conflicts" in captured.err


def test_publish_skills_clean_requires_force(tmp_path: Path) -> None:
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source_skill = source / "skill"
    source_skill.mkdir(parents=True)
    (source_skill / "SKILL.md").write_text("# skill")

    dest.mkdir()
    (dest / "skill").mkdir()

    with pytest.raises(SystemExit):
        publish_skills(
            source=source,
            dest=dest,
            mode="link",
            force=False,
            backup=False,
            clean=True,
            dry_run=True,
            excludes=[],
        )


def test_publish_skills_copy_mode(tmp_path: Path) -> None:
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source_skill = source / "skill"
    source_skill.mkdir(parents=True)
    (source_skill / "SKILL.md").write_text("# skill")

    publish_skills(
        source=source,
        dest=dest,
        mode="copy",
        force=True,
        backup=False,
        clean=False,
        dry_run=False,
        excludes=[],
    )

    assert (dest / "skill" / "SKILL.md").exists()


def test_publish_skills_backup_overwrite(tmp_path: Path) -> None:
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source_skill = source / "skill"
    source_skill.mkdir(parents=True)
    (source_skill / "SKILL.md").write_text("# skill")

    dest.mkdir()
    (dest / "skill").mkdir()
    (dest / "skill" / "old.txt").write_text("old")

    publish_skills(
        source=source,
        dest=dest,
        mode="copy",
        force=True,
        backup=True,
        clean=False,
        dry_run=False,
        excludes=[],
    )

    backups = list(dest.glob("skill.bak.*"))
    assert backups


def test_publish_skills_skip_already_handled(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source_skill = source / "skill"
    source_skill.mkdir(parents=True)
    (source_skill / "SKILL.md").write_text("# skill")

    dest.mkdir()
    os.symlink(source_skill, dest / "existing")

    publish_skills(
        source=source,
        dest=dest,
        mode="copy",
        force=True,
        backup=False,
        clean=False,
        dry_run=False,
        excludes=[],
    )

    captured = capsys.readouterr()
    assert "[SKIP]" in captured.out


def test_publish_skills_clean_removes_stale(tmp_path: Path) -> None:
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source_skill = source / "skill"
    source_skill.mkdir(parents=True)
    (source_skill / "SKILL.md").write_text("# skill")

    dest.mkdir()
    (dest / "stale").mkdir()

    publish_skills(
        source=source,
        dest=dest,
        mode="copy",
        force=True,
        backup=False,
        clean=True,
        dry_run=False,
        excludes=[],
    )

    assert not (dest / "stale").exists()


def test_publish_skills_clean_dry_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source_skill = source / "skill"
    source_skill.mkdir(parents=True)
    (source_skill / "SKILL.md").write_text("# skill")

    dest.mkdir()
    (dest / "stale").mkdir()

    publish_skills(
        source=source,
        dest=dest,
        mode="copy",
        force=True,
        backup=False,
        clean=True,
        dry_run=True,
        excludes=[],
    )

    captured = capsys.readouterr()
    assert "[CLEAN]" in captured.out


def test_publish_skills_force_remove_non_dir(tmp_path: Path) -> None:
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source_skill = source / "skill"
    source_skill.mkdir(parents=True)
    (source_skill / "SKILL.md").write_text("# skill")

    dest.mkdir()
    (dest / "skill").write_text("not a dir")

    publish_skills(
        source=source,
        dest=dest,
        mode="copy",
        force=True,
        backup=False,
        clean=False,
        dry_run=False,
        excludes=[],
    )

    assert (dest / "skill" / "SKILL.md").exists()
