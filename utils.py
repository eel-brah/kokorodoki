import os
import readline
from typing import Dict, List, Optional

from rich.table import Table

from config import COMMANDS, HISTORY_FILE, HISTORY_LIMIT, console


def get_language_map() -> Dict[str, str]:
    """Return the available languages"""
    return {
        "a": "American English",
        "b": "British English",
        "e": "Spanish",
        "f": "French",
        "h": "Hindi",
        "i": "Italian",
        "p": "Brazilian Portuguese",
        "j": "Japanese",
        "z": "Mandarin Chinese",
    }


def get_voices() -> List[str]:
    """Return the available voices"""
    return [
        "af_alloy",
        "af_aoede",
        "af_bella",
        "af_heart",
        "af_jessica",
        "af_kore",
        "af_nicole",
        "af_nova",
        "af_river",
        "af_sarah",
        "af_sky",
        "am_adam",
        "am_echo",
        "am_eric",
        "am_fenrir",
        "am_liam",
        "am_michael",
        "am_onyx",
        "am_puck",
        "am_santa",
        "bf_alice",
        "bf_emma",
        "bf_isabella",
        "bf_lily",
        "bm_daniel",
        "bm_fable",
        "bm_george",
        "bm_lewis",
        "ef_dora",
        "em_alex",
        "em_santa",
        "ff_siwis",
        "hf_alpha",
        "hf_beta",
        "hm_omega",
        "hm_psi",
        "if_sara",
        "im_nicola",
        "jf_alpha",
        "jf_gongitsune",
        "jf_nezumi",
        "jf_tebukuro",
        "jm_kumo",
        "pf_dora",
        "pm_alex",
        "pm_santa",
        "zf_xiaobei",
        "zf_xiaoni",
        "zf_xiaoxiao",
        "zf_xiaoyi",
        "zm_yunjian",
        "zm_yunxi",
        "zm_yunxia",
        "zm_yunyang",
    ]


def display_languages() -> None:
    """Display available languages in a formatted table."""
    languages = get_language_map()
    table = Table(title="Available Languages")
    table.add_column("Code", style="cyan")
    table.add_column("Language", style="green")

    for code, name in languages.items():
        table.add_row(code, name)

    console.print(table)


def display_voices() -> None:
    """Display available voices in a formatted table."""
    voices = get_voices()
    table = Table(title="Available Voices")
    table.add_column("Voice ID", style="cyan")
    table.add_column("Prefix", style="yellow")

    for voice in voices:
        prefix, _ = voice.split("_", 1)
        prefix_desc = {
            "a": "American",
            "b": "British",
            "e": "Spanish",
            "f": "French",
            "h": "Hindi",
            "i": "Italian",
            "p": "Portuguese",
            "j": "Japanese",
            "z": "Mandarin",
        }.get(prefix[0], "Unknown")
        gender = "Female" if prefix[1] == "f" else "Male"
        table.add_row(voice, f"{prefix_desc} {gender}")

    console.print(table)


def display_help() -> None:
    """Display help information."""
    table = Table(title="Available Commands")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="green")

    table.add_row("!lang <code>", "Change language (e.g., !lang b)")
    table.add_row("!voice <name>", "Change voice (e.g., !voice af_bella)")
    table.add_row("!speed <value>", "Change speed (e.g., !speed 1.5)")
    table.add_row("!stop", "Stop current playback")
    table.add_row("!list_langs", "List available languages")
    table.add_row("!list_voices", "List available voices")
    table.add_row("!clear", "Clear screen")
    table.add_row("!clear_history", "Clear history")
    table.add_row("!help or !h", "Show this help message")
    table.add_row("!quit or !q", "Exit the program")

    console.print(table)


def clear_history() -> None:
    readline.clear_history()
    try:
        readline.write_history_file(HISTORY_FILE)
    except IOError:
        pass
    console.print("[bold yellow]History cleared.[/]")


def save_history(history_off: bool) -> None:
    if not history_off:
        try:
            readline.write_history_file(HISTORY_FILE)
        except IOError:
            console.print("[bold red]Error saving history file.[/]")


def init_history(history_off: bool) -> None:
    """Load history file and set the limit"""
    if not history_off:
        if os.path.exists(HISTORY_FILE):
            try:
                readline.read_history_file(HISTORY_FILE)
            except IOError:
                pass
        readline.set_history_length(HISTORY_LIMIT)


def init_completer() -> None:
    readline.parse_and_bind("tab: complete")
    readline.set_completer(completer)
    readline.set_completer_delims("")
    readline.parse_and_bind("set completion-ignore-case on")


def completer(text: str, state: int) -> Optional[str]:
    """Auto-complete function for readline."""
    options = [cmd for cmd in COMMANDS if cmd.startswith(text)]
    return options[state] if state < len(options) else None
