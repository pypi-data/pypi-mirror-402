import runpy
import sys
from pathlib import Path

import pytest


def test_main_module_invokes_cli(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    called = {"value": False}

    def fake_main() -> None:
        called["value"] = True

    import suphia.cli

    monkeypatch.setattr(suphia.cli, "main", fake_main)
    monkeypatch.setattr(sys, "argv", ["suphia"])
    runpy.run_module("suphia.__main__", run_name="__main__")

    assert called["value"]
