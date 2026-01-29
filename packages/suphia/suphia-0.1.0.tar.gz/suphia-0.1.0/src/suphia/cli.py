import argparse
from pathlib import Path

from suphia.skills.publish import publish_skills


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
        default=Path(".claude/skills"),
        help="Destination directory to publish skills to (default: .claude/skills)",
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
        # Resolve paths relative to CWD if they are not absolute
        source = args.source.resolve()
        # For dest, we might not want to resolve if it doesn't exist yet.
        # However, resolve() usually works on paths.
        # We need absolute paths for link creation logic usually
        dest = args.dest.resolve()

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
