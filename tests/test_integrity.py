from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_current_username_preserves_working_legacy_login():
    from achievements.integrity import current_username

    def unexpected_fallback():
        raise AssertionError("fallback must not run when os.getlogin succeeds")

    assert current_username(
        login_resolver=lambda: "junior",
        fallback_resolver=unexpected_fallback,
    ) == "junior"


def test_current_username_uses_deterministic_headless_fallback():
    from achievements.integrity import current_username

    def headless_login():
        raise OSError(-25, "no controlling terminal")

    assert current_username(
        login_resolver=headless_login,
        fallback_resolver=lambda: "runner",
    ) == "runner"


def test_current_username_uses_fixed_value_when_both_resolvers_fail():
    from achievements.integrity import UNAVAILABLE_USERNAME, current_username

    def unavailable():
        raise OSError("username unavailable")

    assert current_username(
        login_resolver=unavailable,
        fallback_resolver=unavailable,
    ) == UNAVAILABLE_USERNAME
    assert UNAVAILABLE_USERNAME == "unknown-user"


def test_make_unlock_hash_preserves_legacy_format():
    from achievements.integrity import (
        UNLOCK_HASH_LENGTH,
        UNLOCK_SALT,
        make_unlock_hash,
    )

    achievement_id = "first_vertex"
    username = "junior"
    expected = hashlib.sha256(
        f"BlenderAch2026_{achievement_id}{username}".encode()
    ).hexdigest()[:16]

    marker = make_unlock_hash(achievement_id, username)

    assert UNLOCK_SALT == "BlenderAch2026_"
    assert UNLOCK_HASH_LENGTH == 16
    assert marker == expected
    assert len(marker) == 16


def test_verify_unlock_hash_rejects_forged_missing_and_other_username():
    from achievements.integrity import make_unlock_hash, verify_unlock_hash

    achievement_id = "first_vertex"
    marker = make_unlock_hash(achievement_id, "junior")

    assert verify_unlock_hash(achievement_id, marker, "junior")
    assert not verify_unlock_hash(achievement_id, "", "junior")
    assert not verify_unlock_hash(achievement_id, "0" * 16, "junior")
    assert not verify_unlock_hash(achievement_id, "ж" * 16, "junior")
    assert not verify_unlock_hash(achievement_id, marker.upper(), "junior")
    assert not verify_unlock_hash(achievement_id, marker, "someone-else")


def test_reward_verifier_denies_invalid_local_integrity_marker():
    from achievements.integrity import make_unlock_hash, verify_unlock_hash
    from achievements.rewards import RewardVerifier

    username = "junior"
    verifier = RewardVerifier(
        lambda achievement_id, stored_hash: verify_unlock_hash(
            achievement_id, stored_hash, username
        )
    )
    achievement_id = "first_vertex"

    valid_stats = type(
        "Stats",
        (),
        {
            "unlocked": {achievement_id},
            "unlock_hashes": {achievement_id: make_unlock_hash(achievement_id, username)},
        },
    )()
    forged_stats = type(
        "Stats",
        (),
        {
            "unlocked": {achievement_id},
            "unlock_hashes": {achievement_id: "forged"},
        },
    )()
    malformed_stats = type(
        "Stats",
        (),
        {
            "unlocked": {achievement_id},
            "unlock_hashes": {achievement_id: "ж" * 16},
        },
    )()

    assert verifier.can_apply(achievement_id, valid_stats) == (True, None)
    allowed, report = verifier.can_apply(achievement_id, forged_stats)
    assert not allowed
    assert report == ("ERROR", "Unlock verification failed")
    allowed, report = verifier.can_apply(achievement_id, malformed_stats)
    assert not allowed
    assert report == ("ERROR", "Unlock verification failed")
