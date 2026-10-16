"""Build a standalone executable for Speech2Text using PyInstaller.

Supports both Linux and Windows. Downloads the best Whisper model for
the build machine's hardware and bundles it into the executable.

Usage:
    python build.py

Requires:
    pip install -r requirements.txt
"""

import platform
import subprocess
import sys

import whisper

from backend.model.whisper_engine import WhisperEngine

APP_NAME = "Speech2Text"

WHISPER_PACKAGE_DIR = whisper.__path__[0]
WHISPER_ASSETS_SRC = f"{WHISPER_PACKAGE_DIR}/assets"
WHISPER_ASSETS_DST = "whisper/assets"


def build():
    """Download the Whisper model and invoke PyInstaller."""
    model_name = WhisperEngine.select_model_name()
    models_dir = WhisperEngine.get_models_dir()
    print(f"Downloading Whisper model '{model_name}' into {models_dir} ...")
    WhisperEngine.download_model(model_name, models_dir)

    separator = ";" if platform.system() == "Windows" else ":"
    whisper_data = f"{WHISPER_ASSETS_SRC}{separator}{WHISPER_ASSETS_DST}"
    models_data = f"{models_dir}{separator}models"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--add-data", whisper_data,
        "--add-data", models_data,
        "--hidden-import", "whisper",
        "--hidden-import", "tiktoken",
        "--hidden-import", "tiktoken_ext",
        "--hidden-import", "tiktoken_ext.openai_public",
        "main.py",
    ]

    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    """
    Build a standalone executable.

    Run from the project root:
        python build.py

    No arguments required. The executable will appear in dist/Speech2Text/.
    To override the auto-selected model, set WHISPER_MODEL env var:
        WHISPER_MODEL=small python build.py
    """
    build()
