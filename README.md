# Speech2Text

A desktop application that captures microphone input and transcribes it to text using a local model. No data leaves the machine.

## Features

- **Push-to-talk recording** -- toggle the "Speak" button to record audio from the default system microphone.
- **Local transcription** -- audio is transcribed on-device. No network requests.
- **Multi-language support** -- English, German, and Spanish out of the box.
- **Automatic model selection** -- picks the best model size based on available GPU VRAM (or falls back to CPU).
- **Cross-platform** -- runs on both Ubuntu Linux and Windows.
- **Standalone executable** -- build a distributable binary with a single command.

## Architecture

```
┌─────────────────────────────┐
│           UI Layer          │
│  (PyQt6 desktop window)    │
│  - Speak / Stop button     │
│  - Language selector        │
│  - Transcription display   │
│  - Status indicator        │
└─────────┬───────────────────┘
          │
┌─────────▼───────────────────┐
│       Audio Capture         │
│  (sounddevice + numpy)      │
│  - Record from mic          │
│  - Silence detection        │
└─────────┬───────────────────┘
          │
┌─────────▼───────────────────┐
│       Transcription         │
│  (openai-whisper)           │
│  - Auto model selection     │
│  - Load model from local    │
│  - Transcribe audio buffer  │
└─────────────────────────────┘
```

## Project Structure

```
Speech2Text/
├── main.py                          # Entry point
├── build.py                         # Build script (PyInstaller)
├── requirements.txt
├── ui/
│   ├── __init__.py
│   └── main_window.py               # PyQt6 window and widgets
└── backend/
    ├── __init__.py
    ├── recorder.py                  # Microphone capture and silence detection
    ├── transcription_engine.py      # Abstract transcription interface
    └── model/
        ├── __init__.py
        └── whisper_engine.py        # Whisper model selection, download, and inference
```

## Prerequisites

- Python 3.12 or later
- `ffmpeg` installed and available on PATH (required by the transcription model)
- A working microphone

## Installation

```bash
git clone https://github.com/royee-yosibash/speech2text.git
cd speech2text
python -m venv .venv
source .venv/bin/activate   # Linux
# .venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

1. The application window opens with a "Speak" button.
2. Select a language from the dropdown.
3. Click the button to start recording.
4. Click again to stop recording.
5. The transcribed text appears in the display area.

On first run the model is downloaded automatically to the `models/` directory.

## Headless Interface

Other applications can use the same recorder and transcription engine without
opening the desktop window. The Python API is available through
`backend.speech_service.SpeechToTextService`:

```python
from backend.speech_service import SpeechToTextService

service = SpeechToTextService()
try:
    service.start_recording(language="en")
    transcript = service.stop_recording()
finally:
    service.close()
```

For external processes, run the persistent JSON-lines worker from the project
root:

```bash
python -m backend.worker
```

The worker loads Whisper once, then reads one JSON object per line from stdin
and writes one JSON event per line to stdout. Each command must be newline
terminated:

```json
{"action":"start","language":"en"}
{"action":"stop"}
{"action":"shutdown"}
```

The `language` field is optional and defaults to `en`. Events include `ready`,
`recording_started`, `transcription_completed` (with a `text` field),
`shutdown`, or `error` (with a `message` field). End-of-input also shuts down
the worker and releases the microphone. Model loading and transcription output
that is not part of the protocol goes to stderr.

## Building a Standalone Executable

The included `build.py` script uses PyInstaller to produce a distributable binary that bundles the model and all dependencies.

```bash
python build.py
```

This will:

1. Detect your hardware (GPU VRAM or CPU-only) and select the appropriate model.
2. Download the model into `models/` if not already present.
3. Bundle everything into `dist/Speech2Text/`.

To override the auto-selected model:

```bash
WHISPER_MODEL=small python build.py        # Linux
set WHISPER_MODEL=small && python build.py  # Windows
```

The resulting executable is at:

| Platform | Path |
|---|---|
| Linux | `dist/Speech2Text/Speech2Text` |
| Windows | `dist\Speech2Text\Speech2Text.exe` |

## Model Selection

The application automatically selects a model based on available hardware. The current implementation uses [OpenAI Whisper](https://github.com/openai/whisper).

| Hardware | Selected Model |
|---|---|
| CUDA GPU with 8+ GB VRAM | `medium` |
| CUDA GPU with 4-8 GB VRAM | `small` |
| CUDA GPU with < 4 GB VRAM | `base` |
| CPU only | `base` |

Override at any time by setting the `WHISPER_MODEL` environment variable:

| Model | Parameters | Relative Speed | Notes |
|---|---|---|---|
| `tiny` | 39M | Fastest | Quick drafts, low-resource machines. |
| `base` | 74M | Fast | Default for CPU. Good speed/accuracy balance. |
| `small` | 244M | Moderate | Better accuracy when hardware allows. |
| `medium` | 769M | Slow | High accuracy, requires decent GPU. |
| `large` | 1550M | Slowest | Best accuracy, requires significant GPU memory. |

## License

See [LICENSE](LICENSE).
