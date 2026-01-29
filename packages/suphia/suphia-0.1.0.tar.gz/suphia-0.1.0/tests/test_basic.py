import subprocess
import sys
from pathlib import Path
from typing import Any


def test_import() -> None:
    import suphia

    assert suphia is not None


def test_publish_dry_run_snapshot(snapshot: Any, tmp_path: Path) -> None:
    """
    Run `suphia skills publish --dry-run` against the examples/basic-setup directory.
    Snapshot the output to ensure deterministic behavior.
    """
    source_dir = Path("examples/basic-setup").resolve()
    dest_dir = tmp_path / "skills"

    # Ensure source exists
    assert source_dir.exists(), "Examples directory missing!"

    # Run CLI command
    cmd = [
        sys.executable,
        "-m",
        "suphia",
        "skills",
        "publish",
        "--source",
        str(source_dir),
        "--dest",
        str(dest_dir),
        "--dry-run",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    assert result.returncode == 0

    # Snapshot stdout
    # We strip empty lines and ensuring consistent path separators for snapshot
    # stability if needed
    # (Though on Windows it might show backslashes, so we should allow syrupy to
    # handle it or normalize)
    output = result.stdout

    # Normalize paths for snapshot consistency across envs if possible,
    # but for now let's just snapshot the raw output and see.
    # Actually, dynamic temp paths will break snapshots.
    # The output contains the dest paths.

    # We should normalize the tmp_path in output to <DEST>
    output = output.replace(str(dest_dir), "<DEST>")
    output = output.replace(str(source_dir), "<SOURCE>")

    # Also Normalize slashes just in case
    output = output.replace("\\", "/")

    # Normalize link type for cross-platform consistency
    output = output.replace("(Symlink)", "(Link)")
    output = output.replace("(Junction)", "(Link)")

    assert output == snapshot
