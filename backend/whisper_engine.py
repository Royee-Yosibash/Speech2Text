"""Whisper-based speech-to-text engine.

Loads an OpenAI Whisper model once and exposes a method to transcribe
float32 audio arrays into text.
"""

import os

import numpy as np
import whisper

from backend.transcription_engine import TranscriptionEngine

DEFAULT_MODEL_NAME = "base"

MODEL_NAME = os.environ.get("WHISPER_MODEL", DEFAULT_MODEL_NAME)


class WhisperEngine(TranscriptionEngine):
    """Wraps an OpenAI Whisper model for audio-to-text transcription.

    Args:
        model_name: Whisper model size to load (tiny, base, small, medium, large).
    """

    def __init__(self, model_name: str = MODEL_NAME) -> None:
        self._model_name = model_name
        self._model = whisper.load_model(model_name)

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
