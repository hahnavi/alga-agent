"""Regression tests for _apply_profile_override ALGA_HOME guard (issue #22502).

When ALGA_HOME is set to the alga root (e.g. systemd hardcodes
ALGA_HOME=/root/.alga), _apply_profile_override must still read
active_profile and update ALGA_HOME to the profile directory.

When ALGA_HOME is already a profile directory (.../profiles/<name>),
_apply_profile_override must trust it and return without re-reading
active_profile (child-process inheritance contract).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path



def _run_apply_profile_override(
    tmp_path, monkeypatch, *, alga_home: str | None, active_profile: str | None,
    argv: list[str] | None = None,
):
    """Run _apply_profile_override in isolation.

    Returns the value of os.environ["ALGA_HOME"] after the call,
    or None if unset.
    """
    alga_root = tmp_path / ".alga"
    alga_root.mkdir(parents=True, exist_ok=True)

    if active_profile is not None:
        (alga_root / "active_profile").write_text(active_profile)

    if active_profile and active_profile != "default":
        (alga_root / "profiles" / active_profile).mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    if alga_home is not None:
        monkeypatch.setenv("ALGA_HOME", alga_home)
    else:
        monkeypatch.delenv("ALGA_HOME", raising=False)

    monkeypatch.setattr(sys, "argv", argv or ["alga", "gateway", "start"])

    from alga_cli.main import _apply_profile_override
    _apply_profile_override()

    return os.environ.get("ALGA_HOME")


class TestApplyProfileOverrideAlgaHomeGuard:
    """Regression guard for issue #22502.

    Verifies that ALGA_HOME pointing to the alga root does NOT suppress
    the active_profile check, while ALGA_HOME already pointing to a
    profile directory IS trusted as-is.
    """

    def test_alga_home_at_root_with_active_profile_is_redirected(
        self, tmp_path, monkeypatch
    ):
        """ALGA_HOME=/root/.alga + active_profile=coder must redirect
        ALGA_HOME to .../profiles/coder.

        Bug scenario from #22502: systemd sets ALGA_HOME to the alga root
        and the user switches to a profile via `alga profile use`.
        Before the fix, the guard returned early and active_profile was ignored.
        """
        alga_root = tmp_path / ".alga"
        alga_root.mkdir(parents=True, exist_ok=True)

        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            alga_home=str(alga_root),
            active_profile="coder",
        )

        assert result is not None, "ALGA_HOME must be set after profile redirect"
        assert "profiles" in result, (
            f"Expected ALGA_HOME to point into profiles/ dir, got: {result!r}"
        )
        assert result.endswith("coder"), (
            f"Expected ALGA_HOME to end with 'coder', got: {result!r}"
        )

    def test_alga_home_already_profile_dir_is_trusted(self, tmp_path, monkeypatch):
        """ALGA_HOME=.../profiles/coder must not be overridden even when
        active_profile says something different.

        Preserves the child-process inheritance contract: a subprocess spawned
        with ALGA_HOME already set to a specific profile must stay in that
        profile.
        """
        alga_root = tmp_path / ".alga"
        profile_dir = alga_root / "profiles" / "coder"
        profile_dir.mkdir(parents=True, exist_ok=True)

        (alga_root / "active_profile").write_text("other")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("ALGA_HOME", str(profile_dir))
        monkeypatch.setattr(sys, "argv", ["alga", "gateway", "start"])

        from alga_cli.main import _apply_profile_override
        _apply_profile_override()

        assert os.environ.get("ALGA_HOME") == str(profile_dir), (
            "ALGA_HOME must remain unchanged when already pointing to a profile dir"
        )

    def test_alga_home_unset_reads_active_profile(self, tmp_path, monkeypatch):
        """Classic case: ALGA_HOME unset + active_profile=coder must set
        ALGA_HOME to the profile directory (existing behaviour must not regress).
        """
        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            alga_home=None,
            active_profile="coder",
        )

        assert result is not None
        assert "coder" in result

    def test_alga_home_unset_default_profile_no_redirect(self, tmp_path, monkeypatch):
        """active_profile=default must not redirect ALGA_HOME."""
        alga_root = tmp_path / ".alga"
        alga_root.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("ALGA_HOME", raising=False)
        monkeypatch.setattr(sys, "argv", ["alga", "gateway", "start"])
        (alga_root / "active_profile").write_text("default")

        from alga_cli.main import _apply_profile_override
        _apply_profile_override()

        assert os.environ.get("ALGA_HOME") is None
