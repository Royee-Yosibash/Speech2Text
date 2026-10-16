"""Tests for the headless speech-to-text service."""

import unittest
from unittest.mock import ANY

import numpy as np

from backend.recorder import SilentAudioError
from backend.speech_service import SpeechToTextService
from tests.unit_tests.speech_harness import SpeechHarness


class SpeechToTextServiceTests(unittest.TestCase):
    """Verify service behavior using the real recorder and Whisper engine."""

    def test_recording_transcribes_with_requested_language(self) -> None:
        """The recorder's captured samples reach the Whisper model with the selected language."""
        audio = np.full((32, 1), 0.1, dtype=np.float32)
        harness = SpeechHarness(self, audio)
        service = harness.service

        service.start_recording("DE")
        transcript = service.stop_recording()

        np.testing.assert_array_equal(harness.model.transcribe.call_args.args[0], audio.flatten())
        self.assertEqual(transcript, "recognized speech")
        self.assertEqual(
            harness.model.transcribe.call_args.kwargs,
            {"language": "de", "fp16": False},
        )
        self.assertEqual(harness.model_loader.call_count, 1)
        harness.stream.stop.assert_called_once_with()
        harness.stream.close.assert_called_once_with()
        self.assertFalse(service.is_recording)

    def test_close_stops_and_discards_active_recording(self) -> None:
        """Closing the service releases its actual recorder without transcribing."""
        harness = SpeechHarness(self, np.ones((32, 1), dtype=np.float32))
        harness.service.start_recording()

        harness.service.close()

        harness.stream.stop.assert_called_once_with()
        harness.stream.close.assert_called_once_with()
        harness.model.transcribe.assert_not_called()
        self.assertFalse(harness.service.is_recording)

    def test_start_rejects_non_iso_language_code(self) -> None:
        """Invalid language codes fail before the actual recorder opens a stream."""
        harness = SpeechHarness(self, np.ones((32, 1), dtype=np.float32))

        with self.assertRaises(ValueError):
            harness.service.start_recording("english")

        harness.input_stream_factory.assert_not_called()

    def test_stop_rejects_silent_audio(self) -> None:
        """The real silence check prevents empty audio from reaching Whisper."""
        harness = SpeechHarness(self, np.zeros((32, 1), dtype=np.float32))
        harness.service.start_recording()

        with self.assertRaises(SilentAudioError):
            harness.service.stop_recording()

        harness.stream.stop.assert_called_once_with()
        harness.model.transcribe.assert_not_called()

    def test_recorder_uses_whisper_audio_format(self) -> None:
        """The actual recorder configures the stream for mono 16 kHz float audio."""
        harness = SpeechHarness(self, np.ones((32, 1), dtype=np.float32))
        harness.service.start_recording()

        self.assertEqual(
            harness.input_stream_factory.call_args.kwargs,
            {
                "samplerate": 16000,
                "channels": 1,
                "dtype": "float32",
                "callback": ANY,
            },
        )
        harness.service.close()


if __name__ == "__main__":
    unittest.main()
