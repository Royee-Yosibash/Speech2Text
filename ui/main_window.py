"""Main application window for Speech2Text.

Provides the primary UI: a speak button to trigger recording, a status
indicator, and a read-only text area that displays transcription results.
"""

import os
import wave

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from backend.recorder import Recorder, SilentAudioError, check_audio_not_silent

WINDOW_TITLE = "Speech2Text"
WINDOW_MIN_WIDTH = 500
WINDOW_MIN_HEIGHT = 400

STATUS_IDLE = "Idle"
STATUS_RECORDING = "Recording..."
STATUS_TRANSCRIBING = "Transcribing..."

BUTTON_LABEL_SPEAK = "Speak"
BUTTON_LABEL_STOP = "Stop"

TEST_WAV_FILENAME = "test_audio.wav"

STYLESHEET = """
    QPushButton#speakButton {
        font-size: 18px;
        padding: 12px 32px;
        border-radius: 8px;
        background-color: #2196F3;
        color: white;
        border: none;
    }
    QPushButton#speakButton:hover {
        background-color: #1976D2;
    }
    QPushButton#speakButton:pressed {
        background-color: #0D47A1;
    }
    QPushButton#speakButton[recording="true"] {
        background-color: #E53935;
    }
    QPushButton#speakButton[recording="true"]:hover {
        background-color: #C62828;
    }
    QLabel#statusLabel {
        font-size: 13px;
        color: #888;
    }
    QTextEdit#transcriptionArea {
        font-size: 14px;
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 8px;
    }
"""


class MainWindow(QMainWindow):
    """Primary application window containing all Speech2Text UI elements."""

    def __init__(self) -> None:
        super().__init__()
        self._recorder = Recorder()
        self._setup_window()
        self._build_ui()
        self.setStyleSheet(STYLESHEET)

    def _setup_window(self) -> None:
        """Configure top-level window properties."""
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

    def _build_ui(self) -> None:
        """Construct and lay out all child widgets."""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # -- Speak button (centered) --
        self.speak_button = QPushButton(BUTTON_LABEL_SPEAK)
        self.speak_button.setObjectName("speakButton")
        self.speak_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.speak_button.setFixedHeight(56)
        self.speak_button.setProperty("recording", "false")
        self.speak_button.clicked.connect(self._on_speak_clicked)

        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(self.speak_button)
        button_row.addStretch()
        layout.addLayout(button_row)

        # -- Status indicator --
        self.status_label = QLabel(STATUS_IDLE)
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # -- Transcription display --
        transcript_label = QLabel("Transcription")
        transcript_label.setFont(QFont(transcript_label.font().family(), 11, QFont.Weight.Bold))
        layout.addWidget(transcript_label)

        self.transcription_area = QTextEdit()
        self.transcription_area.setObjectName("transcriptionArea")
        self.transcription_area.setReadOnly(True)
        self.transcription_area.setPlaceholderText("Transcribed text will appear here...")
        layout.addWidget(self.transcription_area, stretch=1)

    def _on_speak_clicked(self) -> None:
        """Toggle recording on or off when the Speak button is clicked."""
        if self._recorder.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self) -> None:
        """Start capturing audio and update UI to reflect recording state."""
        self._recorder.start()
        self.speak_button.setText(BUTTON_LABEL_STOP)
        self.speak_button.setProperty("recording", "true")
        self.speak_button.style().unpolish(self.speak_button)
        self.speak_button.style().polish(self.speak_button)
        self.status_label.setText(STATUS_RECORDING)

    def _stop_recording(self) -> None:
        """Stop capturing audio, save to WAV, and update UI."""
        audio_data = self._recorder.stop()
        self.speak_button.setText(BUTTON_LABEL_SPEAK)
        self.speak_button.setProperty("recording", "false")
        self.speak_button.style().unpolish(self.speak_button)
        self.speak_button.style().polish(self.speak_button)
        self.status_label.setText(STATUS_IDLE)

        try:
            check_audio_not_silent(audio_data)
        except SilentAudioError as e:
            self.transcription_area.setPlainText(f"No audio detected: {e}")
            return

        wav_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), TEST_WAV_FILENAME)
        _save_wav(wav_path, audio_data, self._recorder.sample_rate)
        self.transcription_area.setPlainText(f"Audio saved to {wav_path}")


def _save_wav(path: str, audio: np.ndarray, sample_rate: int) -> None:
    """Write a float32 audio array to a 16-bit PCM WAV file.

    Args:
        path: Destination file path.
        audio: 1-D float32 audio samples in [-1.0, 1.0].
        sample_rate: Sample rate in Hz.
    """
    pcm = (audio * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
