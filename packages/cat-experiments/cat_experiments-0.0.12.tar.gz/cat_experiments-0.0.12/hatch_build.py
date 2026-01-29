"""Hatch build hook to compile and include Go binary in wheel.

Cross-compilation is supported via GOOS and GOARCH environment variables.
When set, the wheel will be tagged for the target platform.

Examples:
    # Build for current platform
    uv build --wheel

    # Cross-compile for Linux x86_64
    GOOS=linux GOARCH=amd64 uv build --wheel

    # Cross-compile for macOS ARM64
    GOOS=darwin GOARCH=arm64 uv build --wheel

    # Cross-compile for Windows x86_64
    GOOS=windows GOARCH=amd64 uv build --wheel
"""

from __future__ import annotations

import os
import platform
import stat
import subprocess
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

# Mapping from Go OS/arch to wheel platform tags
# Use MUSLLINUX=1 env var to build for Alpine Linux
PLATFORM_TAGS: dict[tuple[str, str, bool], str] = {
    # macOS
    ("darwin", "arm64", False): "macosx_11_0_arm64",
    ("darwin", "amd64", False): "macosx_10_12_x86_64",
    # Linux glibc (manylinux)
    ("linux", "amd64", False): "manylinux_2_17_x86_64.manylinux2014_x86_64",
    ("linux", "arm64", False): "manylinux_2_17_aarch64.manylinux2014_aarch64",
    # Linux musl (Alpine)
    ("linux", "amd64", True): "musllinux_1_2_x86_64",
    ("linux", "arm64", True): "musllinux_1_2_aarch64",
    # Windows
    ("windows", "amd64", False): "win_amd64",
}

# Mapping from Python platform to Go OS/arch
PYTHON_TO_GO: dict[str, tuple[str, str]] = {
    "darwin": ("darwin", "arm64" if platform.machine() == "arm64" else "amd64"),
    "linux": ("linux", "aarch64" if platform.machine() == "aarch64" else "amd64"),
    "windows": ("windows", "amd64"),
}


def get_target_platform() -> tuple[str, str, bool]:
    """Get target OS, architecture, and musl flag from environment or current platform.

    Returns:
        Tuple of (goos, goarch, is_musllinux) for Go build.
    """
    goos = os.environ.get("GOOS")
    goarch = os.environ.get("GOARCH")
    is_musllinux = os.environ.get("MUSLLINUX", "").lower() in ("1", "true", "yes")

    if goos and goarch:
        return (goos, goarch, is_musllinux)

    # Fall back to current platform
    system = platform.system().lower()
    if system in PYTHON_TO_GO:
        goos, goarch = PYTHON_TO_GO[system]
        return (goos, goarch, is_musllinux)

    # Default fallback
    return ("linux", "amd64", is_musllinux)


class GoBinaryBuildHook(BuildHookInterface):
    """Build hook that compiles the Go CLI and includes it in the wheel."""

    PLUGIN_NAME = "go-binary"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """Build the Go binary and add it to the wheel.

        Args:
            version: The version being built
            build_data: Build configuration data
        """
        if self.target_name != "wheel":
            # Only include binary in wheel builds
            return

        # Determine target platform
        goos, goarch, is_musllinux = get_target_platform()
        variant = "musllinux" if is_musllinux else "default"
        self.app.display_info(f"Target platform: {goos}/{goarch} ({variant})")

        # Determine output binary name
        binary_name = "cat-experiments"
        if goos == "windows":
            binary_name += ".exe"

        # Build to a temporary location (not in source tree)
        build_dir = Path(self.root) / "build" / "bin"
        build_dir.mkdir(parents=True, exist_ok=True)
        binary_path = build_dir / binary_name

        # Build Go binary
        cli_dir = Path(self.root) / "cli"
        if not cli_dir.exists():
            self.app.display_warning(f"Go CLI directory not found: {cli_dir}")
            return

        env = os.environ.copy()
        env["CGO_ENABLED"] = "0"  # Static binary
        env["GOOS"] = goos
        env["GOARCH"] = goarch

        # Get actual version from metadata (the 'version' param is the version source type)
        actual_version = self.metadata.version
        self.app.display_info(f"Building Go binary: {binary_path} (version={actual_version})")

        try:
            subprocess.run(
                [
                    "go",
                    "build",
                    "-ldflags",
                    f"-s -w -X main.version={actual_version}",
                    "-o",
                    str(binary_path),
                    "./cmd/cat-experiments",
                ],
                cwd=cli_dir,
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            self.app.display_error(f"Go build failed: {e.stderr}")
            raise
        except FileNotFoundError:
            self.app.display_warning("Go not found, skipping binary build")
            return

        # Make binary executable (no-op on Windows but harmless)
        binary_path.chmod(binary_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        # Add binary to wheel's scripts directory (installs to .venv/bin/)
        # This is the same approach ruff uses - the binary becomes directly executable
        build_data["shared_scripts"][str(binary_path)] = binary_name

        # Set platform-specific wheel tag
        platform_key = (goos, goarch, is_musllinux)
        if platform_key in PLATFORM_TAGS:
            platform_tag = PLATFORM_TAGS[platform_key]
            # Override the wheel tag to be platform-specific
            # This makes the wheel a "platform wheel" instead of "pure Python"
            build_data["tag"] = f"py3-none-{platform_tag}"
            self.app.display_info(f"Wheel platform tag: {platform_tag}")

        self.app.display_success(f"Built Go binary: {binary_path}")
