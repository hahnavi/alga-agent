"""Resolve ALGA_HOME for standalone skill scripts.

Skill scripts may run outside the Alga process (e.g. system Python,
nix env, CI) where ``alga_constants`` is not importable.  This module
provides the same ``get_alga_home()`` and ``display_alga_home()``
contracts as ``alga_constants`` without requiring it on ``sys.path``.

When ``alga_constants`` IS available it is used directly so that any
future enhancements (profile resolution, Docker detection, etc.) are
picked up automatically.  The fallback path replicates the core logic
from ``alga_constants.py`` using only the stdlib.

All scripts under ``google-workspace/scripts/`` should import from here
instead of duplicating the ``ALGA_HOME = Path(os.getenv(...))`` pattern.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from alga_constants import display_alga_home as display_alga_home
    from alga_constants import get_alga_home as get_alga_home
except (ModuleNotFoundError, ImportError):

    def get_alga_home() -> Path:
        """Return the Alga home directory (default: ~/.alga).

        Mirrors ``alga_constants.get_alga_home()``."""
        val = os.environ.get("ALGA_HOME", "").strip()
        return Path(val) if val else Path.home() / ".alga"

    def display_alga_home() -> str:
        """Return a user-friendly ``~/``-shortened display string.

        Mirrors ``alga_constants.display_alga_home()``."""
        home = get_alga_home()
        try:
            return "~/" + str(home.relative_to(Path.home()))
        except ValueError:
            return str(home)
