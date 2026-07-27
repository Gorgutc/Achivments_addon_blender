"""Pure helpers for local unlock-integrity markers.

The marker is intentionally local and deterministic.  It prevents accidental
or casual corruption from silently granting a reward; it is not an anti-cheat
or authentication mechanism.
"""

from __future__ import annotations

import getpass
import hashlib
import hmac
import os
from collections.abc import Callable

UNLOCK_SALT = "BlenderAch2026_"
UNLOCK_HASH_LENGTH = 16
UNAVAILABLE_USERNAME = "unknown-user"


def current_username(
    *,
    login_resolver: Callable[[], str] | None = None,
    fallback_resolver: Callable[[], str] | None = None,
) -> str:
    """Return the legacy login name, with a stable headless fallback.

    ``os.getlogin()`` remains authoritative whenever it works so existing
    markers keep the exact username input they were created with.  Headless
    Blender sessions may not have a controlling terminal; only that failure
    path falls back to ``getpass.getuser()`` and finally a fixed value.
    """

    resolve_login = login_resolver or os.getlogin
    resolve_fallback = fallback_resolver or getpass.getuser
    try:
        return resolve_login()
    except OSError:
        try:
            return resolve_fallback()
        except (KeyError, OSError):
            return UNAVAILABLE_USERNAME


def make_unlock_hash(achievement_id: str, username: str) -> str:
    """Return the legacy-compatible 16-character SHA-256 unlock marker."""

    raw = f"{UNLOCK_SALT}{achievement_id}{username}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:UNLOCK_HASH_LENGTH]


def verify_unlock_hash(achievement_id: str, stored_hash: str, username: str) -> bool:
    """Verify a stored marker without changing or repairing persisted state."""

    if (
        not isinstance(stored_hash, str)
        or len(stored_hash) != UNLOCK_HASH_LENGTH
        or any(character not in "0123456789abcdef" for character in stored_hash)
    ):
        return False
    expected = make_unlock_hash(achievement_id, username)
    return hmac.compare_digest(expected, stored_hash)
