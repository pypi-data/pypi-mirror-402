from pathlib import Path

from suphia.discovery import find_skills, is_skill_dir


def test_is_skill_dir_detects_skill_files(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# skill")
    assert is_skill_dir(skill_dir)

    alt_dir = tmp_path / "alt"
    alt_dir.mkdir()
    (alt_dir / "skills.md").write_text("# skill")
    assert is_skill_dir(alt_dir)


def test_find_skills_resolves_collisions(tmp_path: Path) -> None:
    (tmp_path / "a" / "skill").mkdir(parents=True)
    (tmp_path / "b" / "skill").mkdir(parents=True)
    (tmp_path / "a" / "skill" / "SKILL.md").write_text("# skill")
    (tmp_path / "b" / "skill" / "SKILL.md").write_text("# skill")

    results = find_skills(tmp_path)
    assert set(results.keys()) == {"a-skill", "b-skill"}


def test_find_skills_excludes_paths(tmp_path: Path) -> None:
    (tmp_path / "keep" / "skill").mkdir(parents=True)
    (tmp_path / "skip" / "skill").mkdir(parents=True)
    (tmp_path / "keep" / "skill" / "SKILL.md").write_text("# skill")
    (tmp_path / "skip" / "skill" / "SKILL.md").write_text("# skill")

    results = find_skills(tmp_path, exclude_patterns=["skip"])
    assert set(results.keys()) == {"skill"}


def test_find_skills_reuses_names_across_branches(tmp_path: Path) -> None:
    (tmp_path / "a" / "b").mkdir(parents=True)
    (tmp_path / "c" / "b").mkdir(parents=True)
    (tmp_path / "a" / "b" / "SKILL.md").write_text("# skill")
    (tmp_path / "c" / "b" / "SKILL.md").write_text("# skill")

    results = find_skills(tmp_path)
    assert set(results.keys()) == {"a-b", "c-b"}
