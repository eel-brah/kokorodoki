**🎧 Natural-sounding TTS that fits anywhere. Fast, Real-Time, flexible, and open. Try KokoroDoki!**

# KokoroDoki: Real-Time Text-to-Speech (TTS)

**KokoroDoki** is a real-time Text-to-Speech application supporting multiple languages and voices. It runs locally on your laptop, utilizing either the CPU or leverage CUDA for GPU acceleration.

Powered by [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) an open-weight TTS model that delivers high-quality, natural-sounding speech, it rivals larger models while remaining lightweight and highly responsive.

Whether you need to listen to articles, generating audio files, or just want text spoken back in real time, KokoroDoki has you covered—featuring Console, GUI, CLI, and Daemon modes to suit any workflow.


## Features

* **🌍 Multilingual Support**
  Supports English (US/UK), Spanish, French, Hindi, Italian, Brazilian Portuguese, Japanese, Mandarin Chinese.

* **🗣️ Diverse Voice Selection**
  Switch between a range of expressive voices.

* **🎛️ Interactive Playback Control**
  Pause, resume, skip, rewind, or change voice/language on the fly.

* **🗌 Clipboard Monitoring (Daemon Mode)**
  Automatically speak out any copied text.

* **📂 Export to WAV**
  Save generated audio for offline use or editing.

* **📟 Console Mode**
  An interactive terminal mode with commands to control playback, switch voices/languages, and more.

* **🖥️ GUI Mode**
  A GUI with support for multiple themes and sentence highlighting.

* **🛠️ Daemon**
  Runs as a background service. Accepts commands/text from client.py.

* **</> CLI Modes**
  One-shot text-to-speech conversion from input text or file.

* **🧠 CPU & GPU**
  Built on [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M), supports CPU and CUDA-based acceleration.



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

## Installation

### Requirements

* **Python**: 3.12
* **CUDA**: [cuda-toolkit](https://developer.nvidia.com/cuda-toolkit)
* **Audio/Voice Tools**: `portaudio`, `espeak`
* **Build Tools**: `python3-dev` `python3-virtualenv`
* **Clipboard Support (for Daemon Mode)**: `xclip`


### Setup Instructions

#### Dependencies 

CUDA: [Install cuda-toolkit](https://developer.nvidia.com/cuda-toolkit)

Python3.12, portaudio, espeak and xclip:

For Debian/Ubuntu:
```bash
sudo apt update && sudo apt install -y python3.12 python3.12-dev python3.12-venv espeak portaudio19-dev xclip
```

For Fedora/RHEL/CentOS:
```bash
sudo dnf install -y python3.12 python3.12-devel python3-virtualenv portaudio-devel espeak xclip
```

#### Installation

```bash

# Clone the repository
cd ~/.local/bin
git clone https://github.com/eel-brah/kokorodoki kdoki

# Set up a virtual environment
mkdir -p ~/.venvs
cd ~/.venvs
python3.12 -m venv kdvenv
source kdvenv/bin/activate

# Install Python requirements
pip install -r ~/.local/bin/kdoki/requirements.txt

# Exit the virtual environment
deactivate

# Copy the wrapper
cp ~/.local/bin/kdoki/kokorodoki ~/.local/bin
chmod +x ~/.local/bin/kokorodoki

# Copy the wrapper for the client (Daemon mode)
cp ~/.local/bin/kdoki/doki ~/.local/bin
chmod +x ~/.local/bin/doki
```

#### Integrate with systemd

```bash
# Integrate with systemd for better control (Daemon mode)
mkdir -p ~/.config/systemd/user/
cp ~/.local/bin/kdoki/kokorodoki.service ~/.config/systemd/user/
systemctl --user enable kokorodoki.service
systemctl --user start kokorodoki.service
systemctl --user status kokorodoki.service

# To test it:
# Copy some text like "Integrate with systemd for better control"
# Then run:
doki

# Create custom shortcuts for more convenience experience
```

#### Optional: Language Support Packages

```bash
# For Japanese
pip install pyopenjtalk

# For Mandarin Chinese
pip install ordered_set pypinyin jieba cn2an
```


## Usage

### Examples

```bash
# Launch with default mode (Console mode) and default settings
kokorodoki

# OR, if you didn't follow the setup steps above:
# Use the path to your virtual environment and the path to where you cloned
/path/to/venv/bin/python3.12 /path/to/kokorodoki/src/main.py

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
* `--file`, `-f` Supply a text file for CLI mode.
* `--output`, `-o` Specify output `.wav` file path.
* `--all` Test all voices for the selected language (only with `--text` or `--file`).

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

To send a text, copy the desired text and run `client.py` 

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
```

#### Recommended: Use with `systemd` for Better Control

See the ['Integrate with systemd'](#integrate-with-systemd) section in the installation guide above for steps.

#### Recommended: Create Custom Shortcuts

To improve your experience, it's recommended to create custom keyboard shortcuts for frequently used commands.

Below are some useful commands you can bind to shortcuts:

```bash
# Send from clipboard
~/.venvs/kdvenv/bin/python3.12 ~/.local/bin/kdoki/src/client.py

# Stop playback 
~/.venvs/kdvenv/bin/python3.12 ~/.local/bin/kdoki/src/client.py --stop

# Pause playback
~/.venvs/kdvenv/bin/python3.12 ~/.local/bin/kdoki/src/client.py --pause

# Resume playback
~/.venvs/kdvenv/bin/python3.12 ~/.local/bin/kdoki/src/client.py --resume

# Skip to next sentence
~/.venvs/kdvenv/bin/python3.12 ~/.local/bin/kdoki/src/client.py --next

# Go back a sentence
~/.venvs/kdvenv/bin/python3.12 ~/.local/bin/kdoki/src/client.py --back
```

You can assign these to keyboard shortcuts using your desktop environment’s keyboard settings (e.g., GNOME → Settings → Keyboard → Custom Shortcuts).


### 4/4. ⚡ CLI Mode (One-Shot)

Use the command-line interface for quick, one-off tasks:

```bash
# Speak text
python src/main.py --text "Hello, world!"              
# Speak text from a file and save the audio to a file
python src/main.py --file input.txt --output out.wav   
# Speak using all available voices of a specific language
python src/main.py -l a --text "All voices" --all      
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
This project is licensed under the GNU General Public License v3.0 (GPLv3).

You are free to use, modify, and distribute this software under the terms of the GPLv3.

