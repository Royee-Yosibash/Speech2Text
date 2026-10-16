"""Reusable headless recording and transcription service."""

import re

import numpy as np

from backend.model.whisper_engine import WhisperEngine
from backend.recorder import Recorder, check_audio_not_silent
from backend.transcription_engine import TranscriptionEngine

DEFAULT_LANGUAGE = "en"
LANGUAGE_CODE_PATTERN = re.compile(r"^[a-z]{2}$")
MESSAGE_LANGUAGE_REQUIRED = "Language must be a two-letter language code"


class SpeechToTextService:
    """Coordinates microphone capture and speech transcription.

    Args:
        recorder: Audio recorder implementation. Defaults to the system microphone.
        engine: Transcription engine. Defaults to the local Whisper engine.
    """

    def __init__(
        self,
        recorder: Recorder | None = None,
        engine: TranscriptionEngine | None = None,
    ):
        self._recorder = recorder if recorder is not None else Recorder()
        self._engine = engine if engine is not None else WhisperEngine()
        self._language = DEFAULT_LANGUAGE

    @property
    def is_recording(self) -> bool:
        """Return whether microphone capture is active."""
        return self._recorder.is_recording

    def start_recording(self, language: str = DEFAULT_LANGUAGE):
        """Start capturing microphone audio.

        Args:
            language: Two-letter language code passed to the transcription engine.

        Raises:
            ValueError: If the language is not a two-letter code.
            RuntimeError: If recording is already in progress.
        """
        if not isinstance(language, str):
            raise ValueError(MESSAGE_LANGUAGE_REQUIRED)
        normalized_language = language.strip().lower()
        if LANGUAGE_CODE_PATTERN.fullmatch(normalized_language) is None:
            raise ValueError(MESSAGE_LANGUAGE_REQUIRED)

        self._recorder.start()
        self._language = normalized_language

    def stop_recording(self) -> str:
        """Stop capturing audio and return its transcription.

        Returns:
            Transcribed speech as text.

        Raises:
            RuntimeError: If recording is not active.
            SilentAudioError: If the recording contains no audible speech.
        """
        audio: np.ndarray = self._recorder.stop()
        check_audio_not_silent(audio)
        return self._engine.transcribe(audio, language=self._language)

    def close(self):
        """Release the microphone, discarding any active recording."""
        if self.is_recording:
            self._recorder.stop()
