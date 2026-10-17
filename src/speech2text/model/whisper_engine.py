"""Whisper-based speech-to-text engine.

Loads an OpenAI Whisper model once and exposes a method to transcribe
float32 audio arrays into text. Also handles model selection based on
hardware and path resolution for bundled executables.
"""

import os
import sys
from pathlib import Path

import numpy as np
import torch
import whisper

from speech2text.transcription_engine import TranscriptionEngine

MODELS_DIR_NAME = "models"
APPLICATION_NAME = "speech2text"
MODEL_DIR_ENVIRONMENT_VARIABLE = "SPEECH2TEXT_MODEL_DIR"

GPU_VRAM_THRESHOLDS_GB = [
    (8, "medium"),
    (4, "small"),
    (0, "base"),
]
CPU_DEFAULT_MODEL = "base"


class WhisperEngine(TranscriptionEngine):
    """Wraps an OpenAI Whisper model for audio-to-text transcription.

    Args:
        model_name: Whisper model size to load (tiny, base, small, medium, large).
                    Defaults to automatic selection based on hardware.
    """

    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or self.select_model_name()
        self._model = whisper.load_model(
            self._model_name,
            download_root=self.get_models_dir(),
        )

    def transcribe(self, audio: np.ndarray, language: str = "en") -> str:
        """Differences from base class: uses the Whisper model with fp16 disabled.

        Args:
            audio: 1-D float32 NumPy array at 16 kHz sample rate.
            language: ISO 639-1 language code to force (e.g. "en", "de", "es").

        Returns:
            The transcribed text string.
        """
        result = self._model.transcribe(audio, language=language, fp16=False)
        return result["text"].strip()

    @staticmethod
    def select_model_name() -> str:
        """Pick the best Whisper model for the current machine's hardware.

        Respects the ``WHISPER_MODEL`` environment variable if set.
        Otherwise selects based on GPU VRAM when CUDA is available,
        falling back to the CPU default.

        Returns:
            A Whisper model name string (e.g. "base", "small", "medium").
        """
        override = os.environ.get("WHISPER_MODEL")
        if override:
            return override

        if not torch.cuda.is_available():
            return CPU_DEFAULT_MODEL

        vram_bytes = torch.cuda.get_device_properties(0).total_mem
        vram_gb = vram_bytes / (1024 ** 3)

        for threshold_gb, model_name in GPU_VRAM_THRESHOLDS_GB:
            if vram_gb >= threshold_gb:
                return model_name

        return CPU_DEFAULT_MODEL

    @staticmethod
    def get_models_dir() -> str:
        """Return the writable model directory for this installation.

        Honors ``SPEECH2TEXT_MODEL_DIR`` first. Frozen applications use bundled
        models; source checkouts retain their project-level ``models/`` folder;
        installed packages use the user's cache directory.

        Returns:
            Absolute path to the models directory.
        """
        if getattr(sys, "frozen", False):
            bundled_models_dir = Path(sys._MEIPASS) / MODELS_DIR_NAME
            if bundled_models_dir.is_dir():
                return str(bundled_models_dir)

            executable_dir = Path(sys.executable).resolve().parent
            shared_models_dir = executable_dir / "_internal" / MODELS_DIR_NAME
            if shared_models_dir.is_dir():
                return str(shared_models_dir)

            return str(bundled_models_dir)

        configured_dir = os.environ.get(MODEL_DIR_ENVIRONMENT_VARIABLE)
        if configured_dir:
            return os.path.abspath(os.path.expanduser(configured_dir))

        source_root = Path(__file__).resolve().parents[4]
        source_models_dir = source_root / MODELS_DIR_NAME
        if (source_root / "pyproject.toml").is_file():
            return str(source_models_dir)

        cache_root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        return str(cache_root / APPLICATION_NAME / MODELS_DIR_NAME)

    @staticmethod
    def download_model(model_name: str, target_dir: str) -> str:
        """Download a Whisper model to *target_dir* if not already present.

        Args:
            model_name: Whisper model identifier (e.g. "base", "small").
            target_dir: Directory in which to store the downloaded ``.pt`` file.

        Returns:
            Absolute path to the downloaded model file.
        """
        os.makedirs(target_dir, exist_ok=True)
        url = whisper._MODELS[model_name]
        path = whisper._download(url, target_dir, in_memory=False)
        return path
