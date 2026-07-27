from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path

import build_extension
from find_blender import find_blender

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "blender" / "smoke_extension_policy.py"
REPOSITORY_ID = "user_default"
EXTENSION_MODULE_PREFIX = f"bl_ext.{REPOSITORY_ID}"
FAILURE_MARKERS = (
    "traceback (most recent call last):",
    "exception_access_violation",
    "nameerror",
    "winerror",
    ":fail]",
    "policy violation",
)
DEFAULT_TIMEOUT_SECONDS = 180
SENTINELS = {
    Path("profile-sentinel.bin"): b"achievements-progress-sentinel\x00\x01\xff",
    Path("textures/sentinel-icon.bin"): b"texture-sentinel\x10\x20\x30",
    Path("rewards/sentinel-reward.blend"): b"BLENDER-reward-sentinel\x00\xff",
}


def manifest_identity(root: Path = ROOT) -> tuple[str, str]:
    with (root / "blender_manifest.toml").open("rb") as handle:
        manifest = tomllib.load(handle)
    extension_id = manifest.get("id")
    version = manifest.get("version")
    if not isinstance(extension_id, str) or not extension_id:
        raise ValueError("Extension manifest id must be a non-empty string")
    if not isinstance(version, str) or not version:
        raise ValueError("Extension manifest version must be a non-empty string")
    return extension_id, version


def install_command(blender: Path, archive: Path) -> list[str]:
    return [
        str(blender),
        "--background",
        "--factory-startup",
        "--command",
        "extension",
        "install-file",
        "--repo",
        REPOSITORY_ID,
        "--enable",
        str(archive),
    ]


def remove_command(blender: Path, extension_id: str) -> list[str]:
    return [
        str(blender),
        "--background",
        "--command",
        "extension",
        "remove",
        f"{REPOSITORY_ID}.{extension_id}",
    ]


def probe_command(blender: Path) -> list[str]:
    return [
        str(blender),
        "--background",
        "--python-exit-code",
        "1",
        "--python",
        str(PROBE),
    ]


def policy_env(
    profile_root: Path,
    extension_id: str,
    *,
    phase: str = "installed",
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    resources = profile_root / "blender-user-resources"
    env = dict(os.environ if base_env is None else base_env)
    env["HOME"] = str(profile_root)
    env["USERPROFILE"] = str(profile_root)
    env["BLENDER_USER_RESOURCES"] = str(resources)
    env["ACHIEVEMENTS_EXTENSION_MODULE"] = f"{EXTENSION_MODULE_PREFIX}.{extension_id}"
    env["ACHIEVEMENTS_EXPECTED_EXTENSION_DIR"] = str(
        resources / "extensions" / REPOSITORY_ID / extension_id
    )
    env["ACHIEVEMENTS_POLICY_PHASE"] = phase
    return env


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def sentinel_fingerprint(data_root: Path) -> dict[str, tuple[int, str]]:
    fingerprint: dict[str, tuple[int, str]] = {}
    for relative_path in SENTINELS:
        path = data_root / relative_path
        if not path.is_file():
            raise RuntimeError(f"sentinel missing: {path}")
        raw = path.read_bytes()
        fingerprint[relative_path.as_posix()] = (
            len(raw),
            hashlib.sha256(raw).hexdigest().upper(),
        )
    return fingerprint


def create_sentinels(data_root: Path) -> dict[str, tuple[int, str]]:
    for relative_path, raw in SENTINELS.items():
        path = data_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return sentinel_fingerprint(data_root)


def clean_result_code(
    process_code: int,
    output: str,
    *,
    expected_marker: str | None = None,
) -> int:
    normalized = output.casefold()
    if process_code != 0:
        return process_code
    if any(marker in normalized for marker in FAILURE_MARKERS):
        return 1
    if expected_marker is not None and expected_marker not in output:
        return 1
    return 0


def run_command(
    command: Sequence[str],
    *,
    env: Mapping[str, str],
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=ROOT,
        env=dict(env),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=timeout_seconds,
    )


def print_dry_run(
    blender: Path,
    version_line: str,
    extension_id: str,
    version: str,
    *,
    archive: Path | None = None,
    expected_sha256: str | None = None,
) -> None:
    preview_root = ROOT / ".tmp-installed-extension-policy"
    source_dir = preview_root / "source"
    output_dir = preview_root / "output"
    selected_archive = (
        output_dir / f"{extension_id}-{version}.zip"
        if archive is None
        else archive.resolve()
    )
    env = policy_env(preview_root / "profile", extension_id)
    commands = [
        *(
            [build_extension.extension_build_command(blender, source_dir, output_dir)]
            if archive is None
            else []
        ),
        install_command(blender, selected_archive),
        probe_command(blender),
        remove_command(blender, extension_id),
        probe_command(blender),
    ]
    print(version_line)
    for command in commands:
        print(build_extension.format_shell_command(command))
    for name in (
        "HOME",
        "USERPROFILE",
        "BLENDER_USER_RESOURCES",
        "ACHIEVEMENTS_EXTENSION_MODULE",
        "ACHIEVEMENTS_EXPECTED_EXTENSION_DIR",
        "ACHIEVEMENTS_POLICY_PHASE",
    ):
        print(f"{name}={env[name]}")
    print("ACHIEVEMENTS_POLICY_PHASE=removed")
    if expected_sha256:
        print(f"EXPECTED_ARCHIVE_SHA256={expected_sha256.upper()}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build or select, install, inspect, unregister/register, remove, and "
            "re-inspect the extension in a disposable Blender profile."
        )
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--archive",
        type=Path,
        help="Use one exact prebuilt ZIP instead of building committed HEAD.",
    )
    parser.add_argument(
        "--expected-sha256",
        help="Require the selected archive to keep this SHA-256 throughout the lifecycle.",
    )
    args = parser.parse_args()

    blender, version_line = find_blender()
    extension_id, version = manifest_identity()
    if args.dry_run:
        print_dry_run(
            blender,
            version_line,
            extension_id,
            version,
            archive=args.archive,
            expected_sha256=args.expected_sha256,
        )
        return 0

    temp_root = Path(tempfile.mkdtemp(prefix="achievements-installed-policy-"))
    exit_code = 1
    try:
        source_dir = temp_root / "source"
        output_dir = temp_root / "output"
        profile_root = temp_root / "profile"
        output_dir.mkdir(parents=True)
        profile_root.mkdir(parents=True)
        installed_env = policy_env(profile_root, extension_id, phase="installed")
        removed_env = policy_env(profile_root, extension_id, phase="removed")
        # Factory preferences include the built-in ``blender_org`` repository.
        # Initialize its empty directory so offline repository scans stay clean
        # throughout the later external-remove process.
        resources_root = Path(installed_env["BLENDER_USER_RESOURCES"])
        (resources_root / "extensions" / "blender_org").mkdir(parents=True)
        data_root = profile_root / "BlenderAchievements"
        sentinel_baseline = create_sentinels(data_root)

        if args.archive is None:
            build_extension.prepare_release_source(
                ROOT,
                source_dir,
                revision="HEAD",
                generated_root=temp_root,
            )
            archive = output_dir / f"{extension_id}-{version}.zip"
            build_result = run_command(
                build_extension.extension_build_command(blender, source_dir, output_dir),
                env=installed_env,
            )
            print(
                build_result.stdout,
                end="" if build_result.stdout.endswith("\n") else "\n",
            )
            build_extension.validate_extension_command_result("build", build_result)
        else:
            archive = args.archive.resolve()
        if not archive.is_file():
            raise RuntimeError(f"expected archive missing: {archive}")
        archive_sha256 = sha256_file(archive)
        expected_sha256 = (
            args.expected_sha256.upper() if args.expected_sha256 else archive_sha256
        )
        if archive_sha256 != expected_sha256:
            raise RuntimeError(
                f"archive SHA-256 mismatch: {archive_sha256} != {expected_sha256}"
            )

        install_result = run_command(
            install_command(blender, archive),
            env=installed_env,
        )
        print(install_result.stdout, end="" if install_result.stdout.endswith("\n") else "\n")
        if clean_result_code(install_result.returncode, install_result.stdout) != 0:
            raise RuntimeError("extension install was not clean")

        expected_pass = "[smoke_extension_policy:PASS]"
        probe_result = run_command(probe_command(blender), env=installed_env)
        print(probe_result.stdout, end="" if probe_result.stdout.endswith("\n") else "\n")
        if clean_result_code(
            probe_result.returncode,
            probe_result.stdout,
            expected_marker=expected_pass,
        ) != 0:
            raise RuntimeError("installed extension policy probe failed")
        if sentinel_fingerprint(data_root) != sentinel_baseline:
            raise RuntimeError("progress sentinels changed during install/policy probe")
        if sha256_file(archive) != expected_sha256:
            raise RuntimeError("archive changed during install/policy probe")

        remove_result = run_command(
            remove_command(blender, extension_id),
            env=installed_env,
        )
        print(remove_result.stdout, end="" if remove_result.stdout.endswith("\n") else "\n")
        if clean_result_code(remove_result.returncode, remove_result.stdout) != 0:
            raise RuntimeError("extension removal was not clean")

        removed_result = run_command(probe_command(blender), env=removed_env)
        print(
            removed_result.stdout,
            end="" if removed_result.stdout.endswith("\n") else "\n",
        )
        if clean_result_code(
            removed_result.returncode,
            removed_result.stdout,
            expected_marker="[smoke_extension_policy:REMOVED_PASS]",
        ) != 0:
            raise RuntimeError("removed extension post-state probe failed")
        if sentinel_fingerprint(data_root) != sentinel_baseline:
            raise RuntimeError("progress sentinels changed during extension removal")
        if sha256_file(archive) != expected_sha256:
            raise RuntimeError("archive changed during extension removal")
        print(
            "[installed-policy-runner:PASS] disposable install/policy/register/"
            f"unregister/remove lifecycle passed; archive_sha256={expected_sha256}"
        )
        exit_code = 0
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"[installed-policy-runner:FAIL] {exc}")
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
        if temp_root.exists():
            print(
                f"[installed-policy-runner:FAIL] temporary profile cleanup incomplete: {temp_root}"
            )
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
