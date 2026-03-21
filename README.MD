# KokoroDoki: Real-Time Text-to-Speech (TTS)

**KokoroDoki** is a real-time Text-to-Speech application supporting multiple languages and voices. It runs locally on your laptop, utilizing either the CPU or leverage CUDA for GPU acceleration.

Powered by [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) an open-weight TTS model that delivers high-quality, natural-sounding speech, it rivals larger models while remaining lightweight and highly responsive.

Whether you need to listen to articles, generating audio files, or just want text spoken back in real time, KokoroDoki has you covered—featuring Console, GUI, CLI, and Daemon modes to suit any workflow.

🎧 [Voice Demo - af_heart](samples/welcome.wav)

https://github.com/user-attachments/assets/103b6bd0-0010-4c3d-a373-cf4b218a05a0

---

## 📁 Table of Contents

* [Features](#features)
* [🌐 Language & Voice Availability](#-language--voice-availability)
* [Setup](#-setup)

  * [Requirements](#requirements)
  * [Setup Instructions](#setup-instructions)

    * [Windows / Docker](#0-windows-or-docker)
    * [Dependencies](#1-dependencies)
    * [Install CUDA Toolkit](#2-install-cuda-toolkit)
    * [Installation](#3-installation)
    * [Integrate with systemd](#4-integrate-with-systemd)
    * [Optional: Language Support Packages](#5-optional-language-support-packages)
* [Usage](#usage)
  * [Examples](#examples)
  * [Command-Line Arguments](#command-line-arguments)
  * [1/4. Console Mode (Interactive Terminal)](#14-%EF%B8%8F-console-mode-interactive-terminal)
  * [2/4. GUI Mode](#24-%EF%B8%8F-gui-mode)
  * [3/4. Daemon Mode (Background Service)](#34-%EF%B8%8F-daemon-mode-background-service)
  * [4/4. CLI Mode (One-Shot)](#44--cli-mode-one-shot)
* [Core Dependencies](#core-dRequirementsependencies)
* [Contribute](#-contribute)
* [License](#-license)

---

## Features

* **🌍 Multilingual Support**
  Supports English (US/UK), Spanish, French, Hindi, Italian, Brazilian Portuguese, Japanese, Mandarin Chinese.

* **🗣️ Diverse Voice Selection**
  Switch between a range of expressive voices.

* **🎛️ Interactive Playback Control**
  Pause, resume, skip, rewind, or change voice/language on the fly.

* **🗌 Clipboard Monitoring (Daemon Mode)**
  Automatically speak out any copied/selected text.

* **📂 Export to WAV**
  Save generated audio for offline use or editing.

* **🎬 SRT Subtitle Support**
  Generate timed audio from SRT subtitle files with perfect synchronization.

* **📟 Console Mode**
  An interactive terminal mode with commands to control playback, switch voices/languages, and more.

* **🖥️ GUI Mode**
  A GUI with support for multiple themes and sentence highlighting.

* **🛠️ Daemon**
  Runs as a background service. Accepts commands/text from client.py.

* **\</> CLI Modes**
  One-shot text-to-speech conversion from input text or file.

* **⚡ Fast & Real-time**
  Designed for low-latency performance with quick response and smooth voice output.

* **🧠 CPU & GPU**
  Supports CPU and CUDA-based acceleration.

> ⚠️ **Note:** While CPU mode is supported, performance is significantly better with CUDA-enabled GPUs. Without CUDA, real-time responsiveness and speed may be reduced.


### Floating Tool Bar

💡 Check out [floatingtoolbar](https://github.com/markd89/floatingtoolbar) by [markd89](https://github.com/markd89) — a Python/Qt GUI alternative to hotkeys for Daemon Mode.


## 🌐 Language & Voice Availability

| Language             | Voices |
| -------------------- | ------ |
| American English     | 20     |
| British English      | 8      |
| Spanish              | 3      |
| French               | 1      |
| Hindi                | 4      |
| Italian              | 2      |
| Brazilian Portuguese | 3      |
| Japanese             | 5      |
| Mandarin Chinese     | 8      |

---

## 🚀 Setup

### Requirements

Make sure you have the following installed (see below for a guide):

* **Python**: 3.12
* **CUDA Toolkit**: [cuda-toolkit](https://developer.nvidia.com/cuda-toolkit)
* **Audio & Voice Tools**: `portaudio`, `espeak`
* **Package Manager**: `uv`
* **Python interface to the Tcl/Tk GUI toolkit**: `python3.12-tkinter`
* **Clipboard Support (for Daemon Mode)**: `xclip` or `wl-clipboard` for Wayland

### Setup Instructions

#### 0. Windows or Docker

> For Windows instructions, see [windows.md](windows.md).
> For Docker, see [docker.md](docker/DOCKER.md).

#### 1. Dependencies

**For Debian-based/Ubuntu systems:**

```bash
sudo apt update && sudo apt install -y \
  python3.12 python3.12-dev python3.12-tk \
  portaudio19-dev espeak wl-clipboard
```

**For Fedora/RHEL/CentOS systems:**

```bash
sudo dnf install -y \
  python3.12 python3.12-devel python3.12-tkinter \
  portaudio espeak wl-clipboard
```

Install `xclip` instead of `wl-clipboard` when using X11.

Install uv: https://docs.astral.sh/uv/#installation

#### 2. Install CUDA Toolkit

Follow the official guide to install the [CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit) compatible with your GPU and OS.

#### 3. Installation

##### Self-install

Run directly with uv (no cloning required):

```bash
uv tool install -p python3.12 https://github.com/eel-brah/kokorodoki/archive/refs/heads/master.zip
```

For japanese and Chinese support:
```bash
uv tool install -p python3.12 "https://github.com/eel-brah/kokorodoki/archive/refs/heads/master.zip[japanese,chinese]"
```

To remove it:
```bash
uv tool uninstall kokorodoki
```

##### Manual install

```bash
git clone https://github.com/eel-brah/kokorodoki
cd kokorodoki

# Create environment + install dependencies
uv sync

# To run it (inside project directory)
uv run kokorodoki

# Optional: install locally as a tool
uv tool install .

# Then run from anywhere
kokorodoki 

# For Japanese support:
uv add ".[japanese]"

# For Chinese:
uv add ".[chinese]"
```

#### 4. Integrate with systemd

```bash
# Integrate with systemd for better control (Daemon mode)
kokorodoki-install-service

systemctl --user daemon-reload
systemctl --user enable kokorodoki.service
systemctl --user start kokorodoki.service
systemctl --user status kokorodoki.service

# To test it:
# Copy some text like "Integrate with systemd for better control"
# Then run:
doki

# Create custom keyboard shortcuts for more convenience experience

# Send the selected text
doki

# Send text or an image from clipboard rather than selected text
doki -c

# Stop playback 
doki --stop

# Pause playback
doki --pause

# Resume playback
doki --resume

# Skip to next sentence
doki --next

# Go back a sentence
doki --back
```


## Usage

### Examples

```bash
# Launch with default mode (Console mode) and default settings
kokorodoki

> Note:
> - If installed via `uv tool install`, use `kokorodoki` / `doki`
> - If running from source, use `uv run kokorodoki` / `uv run doki`

# The first run may take some time as it downloads the AI model.

# Show help
kokorodoki -h

# List available voices
kokorodoki --list-voices

# Choose your settings – Spanish, voice ef_dora, with 1.2x speed
kokorodoki -l e -v ef_dora -s 1.2

# Launch GUI mode
kokorodoki --gui

# Launch daemon mode
kokorodoki --daemon

# Copy some text to clipboard, then run:
doki

# Change voice
doki -v af_sky

# Copy text again and play with:
doki

# Generate and save audio to a file
kokorodoki -l b -v bf_lily -t "Generate audio file" -o output.wav

# Generate timed audio from SRT subtitle file (auto-detected)
kokorodoki -f subtitles.srt -o timed_audio.wav

```

### Command-Line Arguments

#### Info

* `--list-languages` Show all supported languages.
* `--list-voices [LANG]` Show all available voices. Optionally filter by language.
* `--themes` Show available GUI themes.

#### Configuration

* `--language`, `-l` Set the initial language (e.g., `a` for American English).
* `--voice`, `-v` Set the initial voice (e.g., `af_heart`).
* `--speed`, `-s` Set the initial speed (range: 0.5 to 2.0).

#### Modes

* `--gui`, `-g` Run in GUI mode.
* `--daemon` Run in daemon mode.
* `--text`, `-t` Supply a text string for CLI mode.
* `--file`, `-f` Supply a text file or SRT subtitle file (SRT files detected automatically).
* `--output`, `-o` Specify output `.wav` file path.
* `--all` Test all voices for the selected language (only with `--text` or text files).

#### Other Options

* `--device` Set the computation device (`cuda` or `cpu`).
* `--port` Set the port for daemon mode (default: `5561`).
* `--theme` Set GUI theme (default: `darkly`).
* `--history-off` Disable saving command history.
* `--verbose`, `-V` Enable verbose output.
* `--ctrl_c_off`, `-c` Disable Ctrl+C from stopping playback.

### 1/4. 🖥️ Console Mode (Interactive Terminal)

Run an interactive terminal interface for real-time TTS, featuring playback control and input history.

```bash
kokorodoki

> Hello world!       # Read this line
> !help              # Show help
> !lang b            # Switch to British English
> !voice bf_emma     # Use a specific voice
> !speed 1.5         # Adjust speed
> !pause             # Pause playback
> !resume            # Resume
> !quit              # Exit

```

#### Available Commands

🎵 Playback Control
| Command           | Description            | Example     |
|------------------|------------------------|-------------|
| `!stop`, `!s`     | Stop current playback  | `!stop`     |
| `!pause`, `!p`    | Pause playback         | `!pause`    |
| `!resume`, `!r`   | Resume playback        | `!resume`   |
| `!next`, `!n`     | Skip to next sentence  | `!next`     |
| `!back`, `!b`     | Go to previous sentence| `!back`     |

🎚️ Audio Settings
| Command                | Description                      | Example               |
|------------------------|----------------------------------|-----------------------|
| `!lang <code>`         | Change language                  | `!lang b`             |
| `!voice <name>`        | Change voice                     | `!voice af_bella`     |
| `!speed <value>`       | Set playback speed (0.5–2.0)     | `!speed 1.5`          |

🧠 Information
| Command            | Description                                | Example            |
|--------------------|--------------------------------------------|--------------------|
| `!list_langs`      | List available languages                   | `!list_langs`      |
| `!list_voices`     | List voices for the current language       | `!list_voices`     |
| `!list_all_voices` | List voices for all languages              | `!list_all_voices` |
| `!status`          | Show current settings                      | `!status`          |

🛠 Interface
| Command             | Description                             | Example            |
|---------------------|-----------------------------------------|--------------------|
| `!clear`            | Clear the screen                        | `!clear`           |
| `!clear_history`    | Clear command history                   | `!clear_history`   |
| `!verbose`          | Toggle verbose mode                     | `!verbose`         |
| `!ctrlc`            | Change behavior of Ctrl+C               | `!ctrlc`           |
| `!help`, `!h`       | Show this help message                  | `!help`            |
| `!quit`, `!q`       | Exit the program                        | `!quit`            |



### 2/4. 🖌️ GUI Mode

Launch a graphical interface. 

```bash
kokorodoki --gui
```

Themes:
1. darkly
2. cyborg
3. solar
4. vapor

Use `--theme <number>` to set it.


### 3/4. 🛠️ Daemon Mode (Background Service)

Runs in the background and receives text or commands via `client.py`.

```bash
kokorodoki --daemon 
```

To send a text, copy the desired text and run `client.py` or `doki`

```bash
doki
```

Pause and resume playback 
```bash
doki --pause
doki --resume
```

#### 🧾 Client Arguments & Daemon Commands

```bash
# Playback Controls 
--stop                  Stop reading
--pause                 Pause reading
--resume                Resume reading
--next                  Skip a sentence
--back                  Go back one sentence
--status                Get current settings
--exit                  Stop reading

# Change settings
--language, -l          Change language ('a' for American English)
--voice, -v             Change voice
--speed, -s             Change speed (range: 0.5-2.0)

# Info
--list-languages        List available languages
--list-voices [LANG]    List available voices, optionally filtered by language

# Config
--port                  If you run kokorodoki daemon mode in a different port, use this option to specify it
--clipboard             Use clipboard text/image rather than selected text
```

#### Recommended: Use with `systemd` for Better Control

See the ['Integrate with systemd'](#integrate-with-systemd) section in the installation guide above for steps.

#### Recommended: Create Custom Shortcuts

To improve your experience, it's recommended to create custom keyboard shortcuts for frequently used commands.

Below are some useful commands you can bind to shortcuts:

```bash
# Send selected text 
doki

# Use clipboard text/image rather than selected text
doki -c

# Stop playback 
doki --stop

# Pause playback
doki --pause

# Resume playback
doki --resume

# Skip to next sentence
doki --next

# Go back a sentence
doki --back
```

You can assign these to keyboard shortcuts using your desktop environment’s keyboard settings (e.g., GNOME → Settings → Keyboard → Custom Shortcuts).


### 4/4. ⚡ CLI Mode (One-Shot)

Use the command-line interface for quick, one-off tasks:

```bash
# Speak text
kokorodoki --text "Hello, world!"              
# Speak text from a file and save the audio to a file
kokorodoki --file input.txt --output out.wav   
# Generate timed audio from SRT subtitle file (auto-detected)
kokorodoki --file subtitles.srt --output timed_audio.wav
# Speak using all available voices of a specific language
kokorodoki -l a --text "All voices" --all      
```

#### 🎬 SRT Subtitle Support

KokoroDoki now supports SRT subtitle files for generating timed audio. This feature allows you to:

- **Perfect Timing**: Generate audio that matches subtitle timestamps exactly
- **Professional Content**: Create synchronized voiceovers for videos
- **Accessibility**: Convert subtitled content into audio format

**SRT File Format Example:**
```srt
1
00:00:00,000 --> 00:00:03,000
Hello and welcome to our demonstration.

2
00:00:04,000 --> 00:00:07,500
This is how SRT subtitles work with timed audio.

3
00:00:08,500 --> 00:00:12,000
Each subtitle entry will be spoken at the correct time.
```

**Usage:**
```bash
# Generate timed audio from SRT file (auto-detected)
kokorodoki -f subtitles.srt -o synchronized_audio.wav

# With custom voice and language
kokorodoki -f subtitles.srt -l a -v af_heart -o output.wav
```


## Core Dependencies

* `nltk` – Sentence parsing
* `torch`, `numpy`, `librosa` – Audio processing
* `sounddevice`, `soundfile` – Audio playback
* [`kokoro`](https://huggingface.co/hexgrad/Kokoro-82M) – The TTS model
* `tkinter`, `ttkbootstrap` – GUI theming
* `rich` – Fancy CLI output
* `socket` - For Daemon and Client communication


## 🤝 Contribute

1. Fork the repo
2. Create a new branch
3. Make your changes
4. Open a pull request

Bug reports and feature requests are welcome on GitHub Issues.


## 📜 License
This project is licensed under the [GNU General Public License v3.0 (GPLv3)](LICENSE).

You are free to use, modify, and distribute this software under the terms of the GPLv3.

