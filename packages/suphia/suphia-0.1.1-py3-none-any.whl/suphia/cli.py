import argparse
import os
from pathlib import Path
from typing import Optional

from suphia.skills.publish import publish_skills

WORKSPACE_MARKERS = [
    ".git",
    ".vscode",
    ".idea",
]


def find_workspace_root(start: Path) -> Optional[Path]:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        for marker in WORKSPACE_MARKERS:
            if (candidate / marker).exists():
                return candidate
    return None


def default_dest_path() -> Path:
    env_root = os.environ.get("SUPHIA_WORKSPACE_ROOT")
    if env_root:
        return Path(env_root) / ".claude/skills"

    workspace_root = find_workspace_root(Path.cwd())
    if workspace_root is not None:
        return workspace_root / ".claude/skills"

    return Path.cwd() / ".claude/skills"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="suphia",
        description="A deterministic, cross-platform agent skill publisher.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # skills metadata
    parser_skills = subparsers.add_parser("skills", help="Manage skills")
    skills_subparsers = parser_skills.add_subparsers(dest="subcommand", required=True)

    # skills publish
    parser_publish = skills_subparsers.add_parser(
        "publish", help="Publish skills from source to destination."
    )

    parser_publish.add_argument(
        "--source",
        type=Path,
        default=Path("."),
        help="Source directory to scan for skills (default: .)",
    )
    parser_publish.add_argument(
        "--dest",
        type=Path,
        default=None,
        help="Destination directory (default: <workspace>/.claude/skills)",
    )
    parser_publish.add_argument(
        "--mode",
        choices=["link", "copy"],
        default="link",
        help="Publish mode: link (junction/symlink) or copy (default: link)",
    )
    parser_publish.add_argument(
        "--force", action="store_true", help="Overwrite existing files or conflicts."
    )
    parser_publish.add_argument(
        "--backup",
        action="store_true",
        help="Backup existing files before overwriting (if conflict).",
    )
    parser_publish.add_argument(
        "--clean",
        action="store_true",
        help="Remove published skills that are no longer in source (requires --force).",
    )
    parser_publish.add_argument(
        "--dry-run", action="store_true", help="Print actions without executing them."
    )
    parser_publish.add_argument(
        "--exclude", action="append", help="Exclude patterns (can be repeated)."
    )

    args = parser.parse_args()

    if args.command == "skills" and args.subcommand == "publish":
        source = args.source.resolve()
        dest_path = args.dest if args.dest is not None else default_dest_path()
        dest = dest_path.resolve()

        publish_skills(
            source=source,
            dest=dest,
            mode=args.mode,
            force=args.force,
            backup=args.backup,
            clean=args.clean,
            dry_run=args.dry_run,
            excludes=args.exclude,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
