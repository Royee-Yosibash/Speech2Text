"""JSON-lines worker interface for external speech-to-text clients.

Run with ``python -m speech2text.worker`` from the project root. The worker reads
one JSON command per line from stdin and writes one JSON event per line to
stdout. Diagnostics and model-loading output are written to stderr.
"""

import json
import sys
from contextlib import redirect_stdout
from enum import Enum
from typing import TextIO

from speech2text.speech_service import (
    DEFAULT_LANGUAGE,
    MESSAGE_LANGUAGE_REQUIRED,
    SpeechToTextService,
)

class WorkerAction(str, Enum):
    """Commands accepted by the JSON-lines worker."""

    START = "start"
    STOP = "stop"
    SHUTDOWN = "shutdown"


class WorkerEvent(str, Enum):
    """Events emitted by the JSON-lines worker."""

    READY = "ready"
    RECORDING_STARTED = "recording_started"
    TRANSCRIPTION_COMPLETED = "transcription_completed"
    SHUTDOWN = "shutdown"
    ERROR = "error"

MESSAGE_ACTION_REQUIRED = "Command action must be a string"
MESSAGE_UNKNOWN_ACTION = "Unknown command action"


class JsonLineWorker:
    """Serve a speech-to-text service over JSON lines.

    Args:
        service: Recording and transcription service to expose.
        input_stream: Command input stream. Defaults to stdin.
        output_stream: Event output stream. Defaults to stdout.
    """

    def __init__(
        self,
        service: SpeechToTextService,
        input_stream: TextIO | None = None,
        output_stream: TextIO | None = None,
    ):
        self._service = service
        self._input_stream = input_stream if input_stream is not None else sys.stdin
        self._output_stream = output_stream if output_stream is not None else sys.stdout

    def run(self):
        """Process commands until shutdown or end-of-input."""
        self._write_event({"event": WorkerEvent.READY})
        try:
            for line in self._input_stream:
                if self._process_line(line):
                    break
        finally:
            self._service.close()

    def _process_line(self, line: str) -> bool:
        """Parse one command and emit its result or an error event.

        Args:
            line: One JSON-encoded command.

        Returns:
            Whether the command requested worker shutdown.
        """
        try:
            command = json.loads(line)
            with redirect_stdout(sys.stderr):
                event = self._dispatch(command)
        except (json.JSONDecodeError, TypeError, ValueError, RuntimeError) as error:
            event = {"event": WorkerEvent.ERROR, "message": str(error)}
        except Exception as error:
            event = {"event": WorkerEvent.ERROR, "message": str(error)}
        self._write_event(event)
        return event["event"] == WorkerEvent.SHUTDOWN

    def _dispatch(self, command: object) -> dict[str, str]:
        """Execute a command and create its response event.

        Args:
            command: Parsed JSON command.

        Returns:
            An event mapping to encode as JSON.

        Raises:
            TypeError: If the command is not an object or its action is invalid.
            ValueError: If a command field is invalid.
            RuntimeError: If a recording transition is invalid.
        """
        if not isinstance(command, dict):
            raise TypeError("Command must be a JSON object")

        action = command.get("action")
        if not isinstance(action, str):
            raise TypeError(MESSAGE_ACTION_REQUIRED)
        try:
            worker_action = WorkerAction(action)
        except ValueError:
            raise ValueError(f"{MESSAGE_UNKNOWN_ACTION}: {action}") from None

        if worker_action is WorkerAction.START:
            language = command.get("language", DEFAULT_LANGUAGE)
            if not isinstance(language, str):
                raise ValueError(MESSAGE_LANGUAGE_REQUIRED)
            self._service.start_recording(language)
            return {"event": WorkerEvent.RECORDING_STARTED}

        if worker_action is WorkerAction.STOP:
            text = self._service.stop_recording()
            return {"event": WorkerEvent.TRANSCRIPTION_COMPLETED, "text": text}

        if worker_action is WorkerAction.SHUTDOWN:
            return {"event": WorkerEvent.SHUTDOWN}

        raise ValueError(f"{MESSAGE_UNKNOWN_ACTION}: {worker_action.value}")

    def _write_event(self, event: dict[str, str]):
        """Write and flush one JSON event.

        Args:
            event: Event mapping to serialize.
        """
        self._output_stream.write(json.dumps(event, ensure_ascii=False) + "\n")
        self._output_stream.flush()


def main():
    """Initialize the local transcription engine and run the worker."""
    with redirect_stdout(sys.stderr):
        service = SpeechToTextService()
    JsonLineWorker(service).run()


if __name__ == "__main__":
    # Run from the project root with: python -m speech2text.worker
    main()
