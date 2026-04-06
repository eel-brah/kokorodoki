# Kokorodoki – Windows Setup Guide

This guide walks you through setting up **Kokorodoki** on **Windows** using **uv**.

---

## Prerequisites

### 1. Install Python 3.12 and uv

* Download Python 3.12: https://www.python.org/downloads/release/python-3120/
* During installation, **enable**: `Add Python to PATH`
* Install uv: https://docs.astral.sh/uv/#installation

---

### 2. Install Git for Windows

* https://git-scm.com/downloads

---

### 3. Install eSpeak NG

* Download installer:
  https://github.com/espeak-ng/espeak-ng/releases

---

### 4. Install C++ Build Tools (Required)

* https://visualstudio.microsoft.com/vs/community/
* Select workload: **Desktop development with C++**

---

## GPU Acceleration (Optional)

If you have an NVIDIA GPU:

* Install CUDA Toolkit:
  https://developer.nvidia.com/cuda-downloads

---

##  Installation

### Option 1 — Recommended (Global install)

Install Kokorodoki globally:

Without CUDA (CPU only):
```bash
uv tool install -p python3.12 "https://github.com/eel-brah/kokorodoki/archive/refs/heads/master.zip[windows]"
```

With CUDA support:
```bash
uv tool install -p python3.12 "https://github.com/eel-brah/kokorodoki/archive/refs/heads/master.zip[windows-torch]"
```

#### With Japanese and Chinese support:

```bash
uv tool install -p python3.12 "https://github.com/eel-brah/kokorodoki/archive/refs/heads/master.zip[windows,japanese,chinese]"
```

---

### Option 2 — Manual install

```bash
git clone https://github.com/eel-brah/kokorodoki
cd kokorodoki

# CPU install
uv sync --extra windows

# GPU install (CUDA)
uv sync --extra windows-torch

# Run from project
uv run kokorodoki
```

#### Option 3: install locally as a tool

```bash
uv tool install .
```

Then you can run:

```bash
kokorodoki
```

---

## Usage

```bash
# Run app
kokorodoki

# If running from source, use `uv run kokorodoki` / `uv run doki`

# Help
kokorodoki -h

# GUI
kokorodoki --gui

# Daemon mode
kokorodoki --daemon

# Send clipboard text
doki

# Change voice
doki -v af_sky
```

---

## Running with CUDA

```bash
kokorodoki --device cuda
```

If CUDA is not detected, see troubleshooting below.

---

## Daemon Mode on Windows

Windows does not support `systemd`, so use **Task Scheduler**.

### 1. Create a startup script (optional)

Create `run_kokorodoki.bat`:

```bat
@echo off
kokorodoki --daemon
```

---

### 2. Use Task Scheduler

* Open **Task Scheduler**
* Create a new task
* Trigger: **At logon**
* Action: Run the `.bat` file

---

## Keyboard Shortcuts (AutoHotkey)

1. Install AutoHotkey: https://www.autohotkey.com/

2. Create `kokorodoki.ahk`:

```ahk
; Send clipboard
^!a::Run, doki

; Pause
^!p::Run, doki --pause

; Resume
^!r::Run, doki --resume

; Stop
^!s::Run, doki --stop

; Next
^!n::Run, doki --next

; Back
^!b::Run, doki --back
```

3. Run the script

---

## ⚠️ Troubleshooting

Check your Torch (PyTorch) configuration:

```python
import torch
print(torch.__version__)
print(torch.version.cuda)
print(torch.cuda.is_available())
```

If CUDA is not available, reinstall PyTorch with GPU support:

```bash
uv pip uninstall torch
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

---

### Common Issues

* `kokorodoki` not found → restart terminal after install
* No audio → verify `espeak-ng` installed
* CUDA not detected → reinstall correct PyTorch version

---

## ✅ Done

You're all set! 🚀

## Uninstall / Cleanup
If installed globally 
````
uv tool uninstall kokorodoki
````

If installed manually (cloned repo)
Delete the project folder:
````
rm -rf kokorodoki
````
