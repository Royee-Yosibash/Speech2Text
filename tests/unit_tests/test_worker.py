"""Tests for the JSON-lines worker protocol."""

import io
import json
import unittest

import numpy as np

from speech2text.worker import JsonLineWorker
from tests.unit_tests.speech_harness import SpeechHarness


class JsonLineWorkerTests(unittest.TestCase):
    """Verify worker commands flow through the actual recorder and engine."""

    def test_worker_transcribes_and_stops_on_shutdown(self) -> None:
        """Start, stop, and shutdown commands produce ordered protocol events."""
        harness = SpeechHarness(self, np.full((32, 1), 0.1, dtype=np.float32))
        commands = "\n".join(
            [
                json.dumps({"action": "start", "language": "fr"}),
                json.dumps({"action": "stop"}),
                json.dumps({"action": "shutdown"}),
                json.dumps({"action": "start"}),
            ]
        )
        output = io.StringIO()

        JsonLineWorker(harness.service, io.StringIO(commands), output).run()

        events = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(
            events,
            [
                {"event": "ready"},
                {"event": "recording_started"},
                {"event": "transcription_completed", "text": "recognized speech"},
                {"event": "shutdown"},
            ],
        )
        self.assertEqual(harness.model.transcribe.call_args.kwargs["language"], "fr")
        harness.stream.stop.assert_called_once_with()
        harness.stream.close.assert_called_once_with()

    def test_worker_reports_malformed_commands_and_continues(self) -> None:
        """Malformed input produces an error event without ending the worker."""
        harness = SpeechHarness(self, np.ones((32, 1), dtype=np.float32))
        commands = "not-json\n" + json.dumps({"action": "not-supported"}) + "\n"
        output = io.StringIO()

        JsonLineWorker(harness.service, io.StringIO(commands), output).run()

        events = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(events[0], {"event": "ready"})
        self.assertEqual(events[1]["event"], "error")
        self.assertIn("Expecting value", events[1]["message"])
        self.assertEqual(events[2], {"event": "error", "message": "Unknown command action: not-supported"})
        harness.input_stream_factory.assert_not_called()

    def test_worker_releases_recording_at_end_of_input(self) -> None:
        """End-of-input releases the actual microphone stream and discards unfinished audio."""
        harness = SpeechHarness(self, np.ones((32, 1), dtype=np.float32))
        output = io.StringIO()
        commands = json.dumps({"action": "start"}) + "\n"

        JsonLineWorker(harness.service, io.StringIO(commands), output).run()

        harness.stream.stop.assert_called_once_with()
        harness.stream.close.assert_called_once_with()
        harness.model.transcribe.assert_not_called()
        self.assertFalse(harness.service.is_recording)


if __name__ == "__main__":
    unittest.main()
