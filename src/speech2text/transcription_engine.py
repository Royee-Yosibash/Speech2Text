"""Abstract base class for speech-to-text transcription engines."""

from abc import ABC, abstractmethod

import numpy as np


class TranscriptionEngine(ABC):
    """Interface that all transcription engine implementations must follow."""

    @abstractmethod
    def __init__(self) -> None:
        pass

    @abstractmethod
    def transcribe(self, audio: np.ndarray, language: str = "en") -> str:
        """Transcribe a float32 audio array to text.

        Args:
            audio: 1-D float32 NumPy array at 16 kHz sample rate.
            language: ISO 639-1 language code to force (e.g. "en", "de", "es").

        Returns:
            The transcribed text string.
        """
