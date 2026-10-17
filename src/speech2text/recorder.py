"""Audio recorder that captures microphone input into a NumPy buffer.

Uses sounddevice to stream audio from the default input device at 16 kHz
mono (the format Whisper expects). Recording is started and stopped
explicitly; the captured audio is available as a NumPy array.
"""

import numpy as np
import sounddevice as sd

DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 1
DTYPE = "float32"
SILENCE_RMS_THRESHOLD = 0.005


class SilentAudioError(Exception):
    """Raised when recorded audio contains only silence."""


class Recorder:
    """Captures audio from the system microphone.

    Args:
        sample_rate: Sample rate in Hz. Defaults to 16000 (Whisper's expected rate).
        channels: Number of audio channels. Defaults to 1 (mono).
    """

    def __init__(
        self,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        channels: int = DEFAULT_CHANNELS,
    ) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self._chunks: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None

    @property
    def is_recording(self) -> bool:
        """True when the recorder is actively capturing audio."""
        return self._stream is not None and self._stream.active

    def start(self) -> None:
        """Begin recording from the default input device.

        Raises:
            RuntimeError: If recording is already in progress.
        """
        if self.is_recording:
            raise RuntimeError("Recording is already in progress")

        self._chunks = []
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=DTYPE,
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop(self) -> np.ndarray:
        """Stop recording and return the captured audio.

        Returns:
            A 1-D float32 NumPy array of the recorded audio samples.

        Raises:
            RuntimeError: If no recording is in progress.
        """
        if not self.is_recording:
            raise RuntimeError("No recording in progress")

        self._stream.stop()
        self._stream.close()
        self._stream = None

        if not self._chunks:
            return np.array([], dtype=DTYPE)

        return np.concatenate(self._chunks).flatten()

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: object,
        status: sd.CallbackFlags,
    ) -> None:
        """Sounddevice stream callback that accumulates audio chunks.

        Args:
            indata: Recorded audio data for this block.
            frames: Number of frames in this block.
            time_info: Timing information (unused).
            status: Stream status flags (unused).
        """
        self._chunks.append(indata.copy())


def check_audio_not_silent(
    audio: np.ndarray,
    threshold: float = SILENCE_RMS_THRESHOLD,
) -> None:
    """Verify that the audio buffer contains audible signal.

    Args:
        audio: 1-D float32 audio samples.
        threshold: Minimum RMS amplitude to consider non-silent.

    Raises:
        SilentAudioError: If the audio RMS is below the threshold.
    """
    if audio.size == 0:
        raise SilentAudioError("Recording is empty (no samples captured)")

    rms = float(np.sqrt(np.mean(audio ** 2)))
    if rms < threshold:
        raise SilentAudioError(
            f"Recording appears silent (RMS={rms:.6f}, threshold={threshold})"
        )
