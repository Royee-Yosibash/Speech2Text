"""Whisper-based speech-to-text engine.

Loads an OpenAI Whisper model once and exposes a method to transcribe
float32 audio arrays into text. Also handles model selection based on
hardware and path resolution for bundled executables.
"""

import os
import sys

import numpy as np
import torch
import whisper

from backend.transcription_engine import TranscriptionEngine

MODELS_DIR_NAME = "models"

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
        """Return the absolute path to the models directory.

        When running inside a PyInstaller bundle the path points to the
        bundled ``models/`` directory.  Otherwise it points to the
        ``models/`` directory next to the project root.

        Returns:
            Absolute path to the models directory.
        """
        if getattr(sys, "frozen", False):
            base = sys._MEIPASS
        else:
            base = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
        return os.path.join(base, MODELS_DIR_NAME)

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
