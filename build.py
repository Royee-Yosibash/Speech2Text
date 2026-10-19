"""Build the shared desktop and worker distribution with PyInstaller.

Supports Linux and Windows. Downloads the selected Whisper model and bundles
the desktop app and headless worker into one onedir distribution.

Usage:
    python build.py
    python build.py --install

Requires:
    pip install -e '.[build]'
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

from speech2text.model.whisper_engine import WhisperEngine

PROJECT_ROOT = Path(__file__).resolve().parent
SPEC_FILE = PROJECT_ROOT / "Speech2Text.spec"
DEFAULT_DIST_PATH = PROJECT_ROOT / "dist"
INSTALL_DATA_HOME_ENVIRONMENT_VARIABLE = "SPEECH2TEXT_DATA_HOME"


def get_install_data_home() -> Path:
    """Return the platform's per-user data directory for the install bundle.

    Returns:
        User data directory, honoring XDG and Speech2Text overrides.
    """
    configured_data_home = os.environ.get(INSTALL_DATA_HOME_ENVIRONMENT_VARIABLE)
    if configured_data_home:
        return Path(configured_data_home).expanduser()

    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    if sys.platform == "darwin":
        default_data_home = Path.home() / "Library" / "Application Support"
        return Path(os.environ.get("XDG_DATA_HOME", default_data_home)).expanduser()

    default_data_home = Path.home() / ".local" / "share"
    return Path(os.environ.get("XDG_DATA_HOME", default_data_home)).expanduser()


def build(dist_path: Path = DEFAULT_DIST_PATH) -> None:
    """Download the selected model and build the shared PyInstaller bundle."""
    model_name = WhisperEngine.select_model_name()
    models_dir = WhisperEngine.get_models_dir()
    print(f"Downloading Whisper model '{model_name}' into {models_dir} ...")
    WhisperEngine.download_model(model_name, models_dir)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--distpath",
        str(dist_path),
        str(SPEC_FILE),
    ]

    subprocess.run(cmd, check=True, cwd=PROJECT_ROOT)


def main() -> None:
    """Build the distribution locally or into a per-user install location."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--install",
        action="store_true",
        help="Build under XDG_DATA_HOME or ~/.local/share.",
    )
    parser.add_argument(
        "--distpath",
        type=Path,
        help="PyInstaller output directory (contains the Speech2Text bundle).",
    )
    arguments = parser.parse_args()
    if arguments.install and arguments.distpath is not None:
        parser.error("--install and --distpath cannot be used together")

    if arguments.install:
        dist_path = get_install_data_home()
    elif arguments.distpath is not None:
        dist_path = arguments.distpath.expanduser()
    else:
        dist_path = DEFAULT_DIST_PATH

    build(dist_path)


if __name__ == "__main__":
    # Build locally with python build.py, or install with python build.py --install.
    main()
