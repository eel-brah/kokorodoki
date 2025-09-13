# Kokorodoki – Windows Setup Guide

This guide walks you through setting up **Kokorodoki** on **Windows**.

---

## Prerequisites

### 1. Install Python 3.12

* Download: [https://www.python.org/downloads/release/python-3120/](https://www.python.org/downloads/release/python-3120/)
* During installation, **make sure to check**: `Add Python to PATH`

### 2. Install Git for Windows

* Download: [https://git-scm.com/downloads](https://git-scm.com/downloads)

### 3. Install eSpeak NG

* Download the `.exe` installer from:
  [https://github.com/espeak-ng/espeak-ng/releases](https://github.com/espeak-ng/espeak-ng/releases)

### 4. C++ Development Tools

* Download: [Visual Studio Community](https://visualstudio.microsoft.com/vs/community/)
* Run the Visual Studio Installer: The installer will open after download
* In the "Workloads" tab: Check “Desktop development with C++”
* Click “Install”


## GPU Acceleration (CUDA Support)

If you have an NVIDIA GPU and want faster performance:

Install the **CUDA Toolkit**:
[https://developer.nvidia.com/cuda-downloads](https://developer.nvidia.com/cuda-downloads)


## Installation

You can use **PowerShell** or **Git Bash**. The steps below use **Git Bash**:

```bash
# Navigate to your home directory
cd

# Clone the repository
git clone https://github.com/eel-brah/kokorodoki kdoki

# Create and activate a virtual environment
python -m venv kdvenv
source kdvenv/Scripts/activate  # Use kdvenv\Scripts\activate.ps1 on PowerShell

# Install dependencies
pip install -r kdoki/requirements.txt
pip install pyreadline3 pyperclip

# Run the application
python kdoki/src/main.py
```

> The first run may take some time as it downloads the AI model.

### Running with CUDA

If you installed CUDA but it using CPU by default, run:

```bash
python kdoki/src/main.py --device cuda
```

If it fails, see the troubleshooting section below.


## Daemon Mode on Windows

Since Windows doesn't support systemd, you can simulate daemon mode using a `.bat` file:

```bat
@echo off
call path\to\kdvenv\Scripts\activate
python path\to\kdoki\src\main.py --daemon
```

Then use **Task Scheduler**:

* Create a scheduled task
* Run the daemon script at login or bind it to a hotkey

---

## Keyboard Shortcuts (with AutoHotkey)

1. Install AutoHotkey: [https://www.autohotkey.com/](https://www.autohotkey.com/)

2. Create a script file (e.g., `kdoki.ahk`):

For example:

```ahk
; Ctrl+Alt+A to send
^!a::Run, C:\path\to\kdvenv\Scripts\python.exe C:\path\to\kdoki\src\client.py

; Ctrl+Alt+P to pause
^!p::Run, C:\path\to\kdvenv\Scripts\python.exe C:\path\to\kdoki\src\client.py --pause

; Ctrl+Alt+R to resume
^!r::Run, C:\path\to\kdvenv\Scripts\python.exe C:\path\to\kdoki\src\client.py --resume

; Ctrl+Alt+S to stop
^!s::Run, C:\path\to\kdvenv\Scripts\python.exe C:\path\to\kdoki\src\client.py --stop

; Ctrl+Alt+N for next
^!n::Run, C:\path\to\kdvenv\Scripts\python.exe C:\path\to\kdoki\src\client.py --next

; Ctrl+Alt+B for previous
^!b::Run, C:\path\to\kdvenv\Scripts\python.exe C:\path\to\kdoki\src\client.py --back
```

3. Run the script to enable global hotkeys.

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
pip uninstall torch -y
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

Then try running Kokorodoki with CUDA:

```bash
python kdoki/src/main.py --device cuda
```

You're all set! 🚀
