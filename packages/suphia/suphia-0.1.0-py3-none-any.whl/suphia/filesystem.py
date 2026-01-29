import os
import shutil
import subprocess
import sys
from pathlib import Path


def get_filesystem_type(path: Path) -> str:
    """
    Determine if the path resides on a Windows or Linux filesystem.

    Treat the repo as Windows filesystem if:
    - Running in WSL and repo path starts with /mnt/
    - Running on Windows and repo path starts with C:\, D:\, etc.
      (checked via drive letter presence)
    """
    path_str = str(path.absolute())

    # Check for WSL /mnt/ prefix
    if sys.platform == "linux" and "microsoft" in os.uname().release.lower():
        if path_str.startswith("/mnt/"):
            return "windows"
        return "linux"

    # Native Windows
    if sys.platform == "win32":
        return "windows"

    # Pure Linux
    return "linux"


def wslpath_to_windows(path: str) -> str:
    """Convert a WSL path to a Windows path using wslpath."""
    try:
        result = subprocess.run(
            ["wslpath", "-w", path], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback or error if wslpath is missing (should not happen in WSL)
        raise RuntimeError(
            f"Failed to convert path '{path}' to Windows path using wslpath."
        )


def create_junction(src: Path, dest: Path, dry_run: bool = False) -> None:
    """
    Create a Windows directory junction.
    If running in WSL, converts paths and uses cmd.exe.
    """

    if sys.platform == "linux" and "microsoft" in os.uname().release.lower():
        # verify src exists
        if not src.exists():
            raise FileNotFoundError(f"Source directory not found: {src}")

        # Convert paths to Windows format
        src_win = wslpath_to_windows(str(src))
        dest_win = wslpath_to_windows(str(dest))

        cmd = ["cmd.exe", "/c", "mklink", "/J", dest_win, src_win]

    elif sys.platform == "win32":
        cmd = ["cmd.exe", "/c", "mklink", "/J", str(dest), str(src)]
    else:
        raise RuntimeError(
            "Cannot create Windows junction on non-Windows/WSL platform."
        )

    if dry_run:
        print(f"[LINK] (Junction) {dest} -> {src}")
        return

    # Create parent directory if it doesn't exist
    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
        )
        print(f"[LINK] (Junction) {dest} -> {src}")
    except subprocess.CalledProcessError as e:
        # If mklink failed, we should probably fail rather than fallback silently
        # The user can use --mode copy if links fail.
        print(f"Error creating junction: {e.stderr.decode()}", file=sys.stderr)
        raise


def create_symlink(src: Path, dest: Path, dry_run: bool = False) -> None:
    """Create a POSIX symlink."""
    if dry_run:
        print(f"[LINK] (Symlink) {dest} -> {src}")
        return

    dest.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(src, dest)
    print(f"[LINK] (Symlink) {dest} -> {src}")


def copy_skill(src: Path, dest: Path, dry_run: bool = False) -> None:
    """Copy the skill directory."""
    if dry_run:
        print(f"[COPY] {dest} -> {src}")
        return

    if dest.exists():
        if dest.is_dir() and not dest.is_symlink():
            shutil.rmtree(dest)
        else:
            os.unlink(dest)

    shutil.copytree(src, dest)
    print(f"[COPY] {dest} -> {src}")


def create_link(src: Path, dest: Path, mode: str, dry_run: bool = False) -> None:
    """
    Create a link or copy based on mode and filesystem type.
    """
    if mode == "copy":
        copy_skill(src, dest, dry_run)
        return

    fs_type = get_filesystem_type(dest if dest.is_absolute() else Path.cwd() / dest)

    # Force junction on Windows filesystem regardless of OS
    if fs_type == "windows":
        create_junction(src, dest, dry_run)
    else:
        create_symlink(src, dest, dry_run)


# Helper for resolving paths
def resolve_path(path: Path) -> Path:
    return path.resolve()
