# Speech2Text

A local speech-to-text application and installable Python package. Use the PyQt desktop app or the headless worker to record microphone input and transcribe it with Whisper on-device.

## Features

- **Push-to-talk recording** -- toggle the "Speak" button to record audio from the default system microphone.
- **Headless worker** -- other applications can control recording and receive transcripts over a JSON-lines interface, without launching the desktop UI.
- **Local transcription** -- audio is transcribed on-device. No network requests.
- **Multi-language support** -- English, German, and Spanish out of the box.
- **Automatic model selection** -- picks the best model size based on available GPU VRAM (or falls back to CPU).
- **Cross-platform** -- runs on both Ubuntu Linux and Windows.
- **Standalone executable** -- build a distributable binary with a single command.

## Architecture

```
       ┌──────────────────┐   ┌─────────────────┐
       │ Desktop UI       │   │ Headless worker │
       │ PyQt6            │   │ JSON-lines      │
       └────────┬─────────┘   └────────┬────────┘
                └──────────┬───────────┘
                           ▼
┌─────────────────────────────┐
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
├── Speech2Text.spec                 # Shared GUI/worker bundle
├── pyproject.toml                   # Installable speech2text package
├── ui/
│   ├── __init__.py
│   └── main_window.py               # PyQt6 window and widgets
└── src/
    └── speech2text/
        ├── __init__.py
        ├── recorder.py              # Microphone capture and silence detection
        ├── speech_service.py        # Reusable headless service
        ├── transcription_engine.py
        ├── worker.py                # JSON-lines worker entry point
        └── model/
            └── whisper_engine.py
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
pip install -e '.[build]'
```

This installs the `speech2text` package in editable mode and provides the
`speech2text-worker` console command.

## Usage

```bash
python main.py
```

1. The application window opens with a "Speak" button.
2. Select a language from the dropdown.
3. Click the button to start recording.
4. Click again to stop recording.
5. The transcribed text appears in the display area.

On first transcription the model is downloaded automatically. Source checkouts
store it in `models/`; installed packages use `~/.cache/speech2text/models`.
Set `SPEECH2TEXT_MODEL_DIR` to override the model directory.

## Headless Interface

Other applications can install and use the reusable `speech2text` package
without importing the desktop UI. The Python API is available through
`speech2text.SpeechToTextService`:

```python
from speech2text import SpeechToTextService

service = SpeechToTextService()
try:
    service.start_recording(language="en")
    transcript = service.stop_recording()
finally:
    service.close()
```

The package installs a persistent worker command for external processes:

```bash
speech2text-worker
```

When running from a source checkout, use `python -m speech2text.worker`
from the project root.

In the PyInstaller bundle, run the worker through the shared executable:

```bash
Speech2Text --worker
```

The worker reads one JSON object per line from stdin and writes one JSON event
per line to stdout. It loads Whisper on the first successful transcription and
keeps the model loaded for later recordings. Each command must be newline
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

The included `build.py` script uses PyInstaller to produce one installable
folder containing both the desktop application and the headless worker. They
share the bundled Python runtime, dependencies, and Whisper model.

```bash
python build.py
```

This will:

1. Detect your hardware (GPU VRAM or CPU-only) and select the appropriate model.
2. Download the model into `models/` if not already present.
3. Bundle the desktop app and `--worker` mode into `dist/Speech2Text/`.

To build the shared distribution directly into the user's data directory:

```bash
python build.py --install
```

On Linux, the bundle is installed under `~/.local/share/Speech2Text/` (or
`$XDG_DATA_HOME/Speech2Text/`). OpenCode can run the worker from that bundle.
Use `--distpath` to build into another permanent location:

```bash
python build.py --distpath /path/to/permanent/location
```

The installed bundle contains its Python runtime, dependencies, and selected
Whisper model. The build virtual environment is only needed to create the
bundle; OpenCode runs `Speech2Text --worker` directly.

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

The same executable runs the worker with `--worker`, which is how the OpenCode
plugin connects to it.

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
