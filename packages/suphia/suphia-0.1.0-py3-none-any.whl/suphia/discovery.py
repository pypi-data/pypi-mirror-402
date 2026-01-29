import os
from pathlib import Path
from typing import Dict, List, Optional, Set


def get_canonical_path(path: Path) -> Path:
    """Resolve path to its absolute, canonical location."""
    return path.resolve()


def is_skill_dir(path: Path) -> bool:
    """Check if directory contains a skill definition file."""
    if not path.is_dir():
        return False
    return (path / "SKILL.md").exists() or (path / "skills.md").exists()


def generate_skill_name(path: Path, root: Path, existing_names: Set[str]) -> str:
    """
    Generate a unique name for the skill based on its path.
    If collision, prepend parent directories until unique or root is reached.
    """
    parts = list(path.relative_to(root).parts)
    # Start with the basename (last part)
    # parts[-1] is the directory name which is the initial skill name

    current_name = parts[-1]
    depth = 1

    while current_name in existing_names:
        depth += 1
        if depth > len(parts):
            # This should ideally not happen if paths are unique, but just in case
            raise ValueError(f"Cannot generate unique name for {path} within {root}")

        # Prepend parent
        current_name = "-".join(parts[-depth:])

    return current_name


def find_skills(
    source_root: Path, exclude_patterns: Optional[List[str]] = None
) -> Dict[str, Path]:
    """
    Recursively find skills in source_root.
    Returns a dictionary mapping unique skill names to their source directory paths.
    """
    if exclude_patterns is None:
        exclude_patterns = []

    found_skills: List[Path] = []

    # Simple walk
    for root, dirs, files in os.walk(source_root):
        root_path = Path(root)

        # Check excludes (basic implementation)
        # In a real robust app we might use fnmatch or similar on the relative path
        if any(exc in str(root_path) for exc in exclude_patterns):
            continue

        # Prevent descending into exclusions if practical (modify dirs in-place)
        # For now, just skip processing

        if is_skill_dir(root_path):
            found_skills.append(root_path)

    # Resolve naming collisions

    # Sort by path length (deeper first? or alphabetical?)
    # Sorting ensures determinism
    found_skills.sort(key=lambda p: str(p))

    # Iteration 1:
    # path -> basename

    current_names = {p: p.name for p in found_skills}
    # Track the latest resolved names for returning

    while True:
        # Check for collisions
        name_counts: Dict[str, int] = {}
        for p, name in current_names.items():
            name_counts[name] = name_counts.get(name, 0) + 1

        collisions = {n for n, c in name_counts.items() if c > 1}

        if not collisions:
            break

        # Resolve collisions
        progress = False
        for p in found_skills:
            name = current_names[p]
            if name in collisions:
                # Prepend parent
                # Calculate current depth relative to source_root to find next parent
                # We need to know how many segments we are currently using.

                # Check how many segments in current name
                segments = name.split("-")
                current_depth_in_name = len(segments)

                # Get path parts relative to root
                try:
                    rel_parts = list(p.relative_to(source_root).parts)
                except ValueError:
                    # Should be rare if p is inside source_root
                    rel_parts = list(p.parts)  # Fallback

                # If we have exhausted the path, we can't prepend more.
                if current_depth_in_name >= len(rel_parts):
                    raise ValueError(
                        f"CRITICAL: Unresolvable collision for {p}. Name: {name}"
                    )

                # New name: join (depth+1) segments from the end
                new_len = current_depth_in_name + 1
                new_name = "-".join(rel_parts[-new_len:])

                if new_name != name:
                    current_names[p] = new_name
                    progress = True

        if not progress:
            # Should be caught by the depth check, but strictly preventing infinite loop
            raise RuntimeError("Infinite loop handling nam collisions.")

    return {name: path for path, name in current_names.items()}
