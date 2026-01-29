import shutil
import sys
from pathlib import Path
from typing import List

from suphia.discovery import find_skills, get_canonical_path
from suphia.filesystem import create_link


def publish_skills(
    source: Path,
    dest: Path,
    mode: str,
    force: bool,
    backup: bool,
    clean: bool,
    dry_run: bool,
    excludes: List[str],
) -> None:
    # 1. Discovery
    try:
        skills = find_skills(source, excludes)
    except Exception as e:
        print(f"Error during discovery: {e}", file=sys.stderr)
        sys.exit(1)

    if not skills:
        print("No skills found.")
        return

    # 2. Preparation
    if not dest.exists() and not dry_run:
        dest.mkdir(parents=True, exist_ok=True)

    # Get existing published skills for cleaning
    existing_published = set()
    if dest.exists():
        existing_published = {p.name for p in dest.iterdir()}

    # 3. Publish Loop
    for name, skill_source_path in skills.items():
        target_path = dest / name

        # Check source equivalence (Source equivalence rule)
        # If a discovered skill directory is the same source directory as one that is
        # already published (linked or copied): treat it as already handled.

        # We need to check if ANY existing published skill points to this source.
        # This is slightly expensive (resolving all keys in dest), but safer.

        is_already_handled = False
        canonical_source = get_canonical_path(skill_source_path)

        if dest.exists():
            for existing_name in dest.iterdir():
                # Avoid following symlinks recursively or getting confused
                # We want to know if 'existing_name' resolves to 'canonical_source'
                try:
                    if existing_name.resolve() == canonical_source:
                        print(
                            f"[SKIP] {name} (already linked to same source at "
                            f"{existing_name.name})"
                        )
                        is_already_handled = True
                        break
                except (OSError, RuntimeError):
                    pass

        if is_already_handled:
            if name in existing_published:
                existing_published.remove(name)
            continue

        # Handling Destination Conflict
        if target_path.exists() or (
            target_path.is_symlink() and not target_path.exists()
        ):
            # Resolution logic

            # Check if it ALREADY points to the correct source
            # (Source equivalence check for THIS specific target)
            try:
                if target_path.resolve() == canonical_source:
                    print(f"[SKIP] {name} (already correct)")
                    if name in existing_published:
                        existing_published.remove(name)
                    continue
            except (OSError, RuntimeError):
                pass  # broken link or other issue, proceed to overwrite logic

            # If we are here, target exists but points elsewhere or is a different file
            if not force:
                print(
                    f"Error: Destination {target_path} exists and conflicts. "
                    "Use --force to overwrite.",
                    file=sys.stderr,
                )
                # Fail or continue? Usually strict fail is safer for "publish" unless
                # implicit.
                # Requirement: "error unless --force"
                sys.exit(1)

            # Handle Backup
            if backup and not dry_run:
                import time

                timestamp = int(time.time())
                backup_path = target_path.with_name(f"{name}.bak.{timestamp}")
                print(f"[BACKUP] {target_path} -> {backup_path}")
                target_path.rename(backup_path)
            elif not dry_run:
                # Remove
                if target_path.is_dir() and not target_path.is_symlink():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()
                print(f"[REMOVE] {target_path}")
            elif dry_run:
                if backup:
                    print(f"[BACKUP] {target_path}")
                else:
                    print(f"[REMOVE] {target_path}")

        # Create Link
        create_link(skill_source_path, target_path, mode, dry_run)

        if name in existing_published:
            existing_published.remove(name)

    # 4. Clean
    if clean:
        if not force:
            print("Error: --clean requires --force.", file=sys.stderr)
            sys.exit(1)

        for stale in existing_published:
            stale_path = dest / stale
            if dry_run:
                print(f"[CLEAN] {stale_path}")
            else:
                if stale_path.is_dir() and not stale_path.is_symlink():
                    shutil.rmtree(stale_path)
                else:
                    stale_path.unlink()
                print(f"[CLEAN] {stale_path}")
