"""PyInstaller spec for the shared desktop and headless executable."""

import sys
from pathlib import Path

import whisper

PROJECT_ROOT = Path(SPECPATH).resolve()
SOURCE_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SOURCE_ROOT))

from speech2text.model.whisper_engine import WhisperEngine

APP_NAME = "Speech2Text"
WHISPER_ASSETS = Path(whisper.__file__).resolve().parent / "assets"
MODEL_DIR = Path(WhisperEngine.get_models_dir())
DATA_FILES = [
    (str(WHISPER_ASSETS), "whisper/assets"),
    (str(MODEL_DIR), "models"),
]
HIDDEN_IMPORTS = [
    "whisper",
    "tiktoken",
    "tiktoken_ext",
    "tiktoken_ext.openai_public",
]

analysis = Analysis(
    [str(PROJECT_ROOT / "main.py")],
    pathex=[str(PROJECT_ROOT), str(SOURCE_ROOT)],
    binaries=[],
    datas=DATA_FILES,
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(analysis.pure)
console_options = {"hide_console": "hide-late"} if sys.platform == "win32" else {}

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    **console_options,
)

COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    name=APP_NAME,
)
