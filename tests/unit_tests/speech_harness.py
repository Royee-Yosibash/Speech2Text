"""Test fixture for exercising the real speech pipeline without devices or model downloads."""

from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch

import numpy as np

from speech2text.speech_service import SpeechToTextService


class SpeechHarness:
    """Provide a real service with external audio and model dependencies mocked.

    Args:
        test_case: Test case used to register cleanup for active patches.
        audio: Samples emitted by the mocked sounddevice input stream.
    """

    def __init__(self, test_case: TestCase, audio: np.ndarray) -> None:
        self.audio = audio
        self.stream = MagicMock()
        self.stream.active = False
        self.input_stream_factory = Mock(return_value=self.stream)
        self.stream.start.side_effect = self._start_stream
        self.stream.stop.side_effect = self._stop_stream

        self.model = MagicMock()
        self.model.transcribe.return_value = {"text": " recognized speech "}
        self.model_loader = Mock(return_value=self.model)

        input_stream_patch = patch("speech2text.recorder.sd.InputStream", self.input_stream_factory)
        model_loader_patch = patch("speech2text.model.whisper_engine.whisper.load_model", self.model_loader)
        model_selection_patch = patch(
            "speech2text.model.whisper_engine.WhisperEngine.select_model_name",
            return_value="base",
        )
        test_case.addCleanup(input_stream_patch.stop)
        test_case.addCleanup(model_loader_patch.stop)
        test_case.addCleanup(model_selection_patch.stop)
        input_stream_patch.start()
        model_loader_patch.start()
        model_selection_patch.start()

        self.service = SpeechToTextService()

    def _start_stream(self) -> None:
        """Activate the mocked stream and deliver one captured audio block."""
        self.stream.active = True
        callback = self.input_stream_factory.call_args.kwargs["callback"]
        callback(self.audio, len(self.audio), None, None)

    def _stop_stream(self) -> None:
        """Mark the mocked input stream inactive."""
        self.stream.active = False
