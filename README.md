# Speech2Text

A desktop application that captures microphone input and transcribes it to text.

## Overview

Speech2Text provides a minimal UI with a single "Speak" button. Pressing the button starts recording from the system microphone. Releasing (or pressing again) stops recording, sends the captured audio to a local model, and displays the transcribed text on screen. The transcribed text is automatically copied to the clipboard for immediate use.

## Features

- **Push-to-talk recording** — hold or toggle the "Speak" button to record audio from the default system microphone.
- **Local transcription** — audio is transcribed on-device using a local model. No data leaves the machine.
- **Clipboard integration** — transcribed text is copied to the clipboard automatically.
- **Cross-platform** — runs on both Ubuntu Linux and Windows.

## Architecture

```
┌─────────────────────────────┐
│           UI Layer          │
│  (PyQt6 desktop window)     │
│  - Speak button             │
│  - Transcription display    │
│  - Status indicator         │
└─────────┬───────────────────┘
          │
┌─────────▼───────────────────┐
│       Audio Capture         │
│  (sounddevice / pyaudio)    │
│  - Record from mic          │
│  - Stream to WAV buffer     │
└─────────┬───────────────────┘
          │
┌─────────▼───────────────────┐
│     Whisper Transcription   │
│  (openai-whisper)           │
│  - Load model once at start │
│  - Transcribe audio buffer  │
│  - Return text result       │
└─────────────────────────────┘
```

### Component Responsibilities

| Component | Role |
|---|---|
| **UI Layer** | Renders the window, handles button events, displays results. |
| **Audio Capture** | Opens the default input device, records audio while the button is held, produces a WAV-format buffer. |
| **Whisper Transcription** | Loads a Whisper model into memory on startup. Accepts audio data and returns transcribed text. |

## Tech Stack

| Concern | Choice | Rationale |
|---|---|---|
| Language | Python 3.12+ | Required by project spec. |
| UI framework | PyQt6 | Mature cross-platform desktop toolkit with native look on both Linux and Windows. |
| Audio capture | sounddevice + numpy | Simple API, no compilation required, works on Linux (PulseAudio/ALSA) and Windows (WASAPI). |
| Transcription | openai-whisper | Runs fully offline, multiple model sizes for speed/accuracy tradeoff. |
| Clipboard | pyperclip | Lightweight cross-platform clipboard access. |

## Whisper Model Selection

Whisper ships several model sizes. The application defaults to `base` but this is configurable.

| Model | Parameters | Relative Speed | Use Case |
|---|---|---|---|
| `tiny` | 39M | Fastest | Quick drafts, low-resource machines. |
| `base` | 74M | Fast | Default. Good balance of speed and accuracy. |
| `small` | 244M | Moderate | Better accuracy when hardware allows. |
| `medium` | 769M | Slow | High accuracy, requires decent GPU. |
| `large` | 1550M | Slowest | Best accuracy, requires significant GPU memory. |

## Project Structure

```
Speech2Text/
├── README.md
├── requirements.txt
├── main.py                 # Entry point
├── ui/
│   ├── __init__.py
│   └── main_window.py      # PyQt6 window and widgets
├── backend/
│   ├── __init__.py
│   ├── recorder.py         # Microphone capture logic
│   ├── whisper_engine.py   # Whisper model loading and inference
│   └── clipboard.py        # Clipboard helper
    ├── utils/
│       └── __init__.py
└── tests/
    └── unit_tests/
        ├── __init__.py
        ├── test_recorder.py
        └── test_whisper_engine.py
```

## Prerequisites

- Python 3.12 or later
- `ffmpeg` installed and available on PATH (required by Whisper)
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
2. Click and hold (or toggle) the button to start recording.
3. Release (or click again) to stop recording.
4. The transcribed text appears in the display area and is copied to the clipboard.

## Configuration

Environment variables or a future config file can control:

| Variable | Default | Description |
|---|---|---|
| `WHISPER_MODEL` | `base` | Whisper model size to load. |
| `AUDIO_SAMPLE_RATE` | `16000` | Sample rate in Hz (Whisper expects 16 kHz). |

## License

See [LICENSE](LICENSE).
