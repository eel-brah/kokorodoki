import os
import platform
import re
from typing import Dict, List, Optional

if platform.system() == "Windows":
    import pyreadline3 as readline
else:
    import readline

from nltk import sent_tokenize
from rich import box
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


def get_easyocr_language_map() -> Dict[str, str]:
    """Return the available languages for EasyOCR"""
    return {
        "a": "en",
        "b": "en",
        "e": "es",
        "f": "fr",
        "h": "hi",
        "i": "it",
        "p": "pt",
        "j": "ja",
        "z": "ch_sim",
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


def get_gui_themes() -> Dict[int, str]:
    """Return the available gui themes"""
    return {
        # Dark themes
        1: "darkly",
        2: "cyborg",
        3: "solar",
        4: "vapor",
        # Light themes
        5: "cosmo",
        6: "pulse",
        7: "morph",
    }


def display_themes() -> None:
    """Display available gui themes"""
    themes = get_gui_themes()
    table = Table(title="Available Themes", box=box.ROUNDED)
    table.add_column("Number", style="cyan")
    table.add_column("Theme", style="green")
    table.add_column("Style", style="green")

    for number, name in themes.items():
        table.add_row(str(number), name, "Dark" if 1 <= number <= 4 else "Light")

    console.print(table)


def get_nltk_language_map() -> Dict[str, str]:
    """Return available languages in nltk"""
    return {
        "a": "english",
        "b": "english",
        "e": "spanish",
        "f": "french",
        "i": "italian",
        "p": "portuguese",
    }


def get_nltk_language(language_code: str) -> str:
    return next(
        (
            lang
            for code, lang in get_nltk_language_map().items()
            if code == language_code
        ),
        "english",
    )


def display_languages() -> None:
    """Display available languages in a formatted table."""
    languages = get_language_map()
    table = Table(title="Available Languages", box=box.ROUNDED)
    table.add_column("Code", style="cyan")
    table.add_column("Language", style="green")

    for code, name in languages.items():
        table.add_row(code, name)

    console.print(table)


def display_voices(language=None) -> None:
    """Display available voices in a formatted table."""
    voices = get_voices()
    table = Table(title="Available Voices", box=box.ROUNDED)
    table.add_column("Voice ID", style="cyan")
    table.add_column("Prefix", style="yellow")

    if language not in get_language_map() and language is not None:
        console.print(f"[bold red]Error:[/] Invalid language '{language}'")
        display_languages()
        return

    for voice in voices:
        prefix, _ = voice.split("_", 1)
        if language is None or language == prefix[0]:
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


def display_status(language: str, voice: str, speed: float) -> None:
    """Display current settings."""
    console.print("[green]Currently:[/]")
    console.print(f"  Language: [cyan]{get_language_map()[language]}[/]")
    console.print(f"  Voice: [cyan]{voice}[/]")
    console.print(f"  Speed: [cyan]{speed}[/]")


def format_status(language: str, voice: str, speed: float) -> str:
    """Return current settings as a formatted string."""
    status_lines = [
        f"Current language: {get_language_map()[language]}.",
        f"Current voice: {voice}.",
        f"Current speed: {speed}.",
    ]
    return "\n".join(status_lines)


def display_help() -> None:
    """Display help information for available commands."""
    table = Table(
        title="[bold]Command Help[/bold]",
        box=box.ROUNDED,
        title_style="bold magenta",
        header_style="bold white",
    )
    table.add_column("Command", style="cyan", width=20)
    table.add_column("Description", style="green")
    table.add_column("Example", style="yellow")

    command_groups = [
        {
            "group": "Playback Control",
            "commands": [
                ("!stop, !s", "Stop current playback", "!stop"),
                ("!pause, !p", "Pause playback", "!pause"),
                ("!resume, !r", "Resume playback", "!resume"),
                ("!next, !n", "Skip to next sentence", "!next"),
                ("!back, !b", "Go to previous sentence", "!back"),
            ],
        },
        {
            "group": "Audio Settings",
            "commands": [
                ("!lang <code>", "Change language", "!lang b"),
                ("!voice <name>", "Change voice", "!voice af_bella"),
                ("!speed <value>", "Set playback speed (0.5-2.0)", "!speed 1.5"),
            ],
        },
        {
            "group": "Information",
            "commands": [
                ("!list_langs", "List available languages", "!list_langs"),
                (
                    "!list_voices",
                    "List available voices for current language",
                    "!list_voices",
                ),
                (
                    "!list_all_voices",
                    "List voices for all languages",
                    "!list_all_voices",
                ),
                ("!status", "Show current settings", "!status"),
            ],
        },
        {
            "group": "Interface",
            "commands": [
                ("!clear", "Clear the screen", "!clear"),
                ("!clear_history", "Clear command history", "!clear_history"),
                ("!verbose", "Toggle verbose mode", "!verbose"),
                ("!ctrlc", "Change the effect of Ctrl+C", "!ctrlc"),
                ("!help, !h", "Show this help message", "!help"),
                ("!quit, !q", "Exit the program", "!quit"),
            ],
        },
    ]

    for group in command_groups:
        table.add_row(
            f"[bold underline]{group['group']}[/]", "", "", style="bold green"
        )
        for cmd, desc, example in group["commands"]:
            table.add_row(cmd, desc, example)

    console.print(table)
    console.print(
        "[italic dim]Tip: Use commands with aliases (e.g., !s for !stop) for faster input.[/]\n"
    )


def clear_history() -> None:
    readline.clear_history()
    if platform.system() != "Windows":
        try:
            readline.write_history_file(HISTORY_FILE)
        except IOError:
            pass
    console.print("[bold yellow]History cleared.[/]")


def save_history(history_off: bool) -> None:
    if platform.system() == "Windows":
        return
    if not history_off:
        try:
            readline.write_history_file(HISTORY_FILE)
        except IOError:
            console.print("[bold red]Error saving history file.[/]")


def init_history(history_off: bool) -> None:
    """Load history file and set the limit"""
    if platform.system() == "Windows":
        return
    if not history_off:
        if os.path.exists(HISTORY_FILE):
            try:
                readline.read_history_file(HISTORY_FILE)
            except IOError:
                pass
        readline.set_history_length(HISTORY_LIMIT)


def init_completer() -> None:
    if platform.system() == "Windows":
        return
    readline.parse_and_bind("tab: complete")
    readline.set_completer(completer)
    readline.set_completer_delims("")
    readline.parse_and_bind("set completion-ignore-case on")


def completer(text: str, state: int) -> Optional[str]:
    """Auto-complete function for readline."""
    if platform.system() == "Windows":
        return None
    options = [cmd for cmd in COMMANDS if cmd.startswith(text)]
    return options[state] if state < len(options) else None


def split_by_words(chunk: str, max_len: int) -> List[str]:
    """Split a chunk into smaller chunks by words, ensuring each is <= max_len"""

    if len(chunk) <= max_len:
        return [chunk]

    chunks = []
    current_chunk = ""

    words = chunk.split(" ")
    for word in words:
        if len(current_chunk) + len(word) + (1 if current_chunk else 0) > max_len:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = word
            else:
                # If word itself is too long
                while len(word) > max_len:
                    chunks.append(word[:max_len])
                    word = word[max_len:]
                current_chunk = word
        else:
            current_chunk += (" " if current_chunk else "") + word
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def split_long_sentence(sentence: str, max_len=350, min_len=50) -> List[str]:
    """Split a sentence into chunks of <= max_len"""
    if len(sentence) <= max_len:
        return [sentence]

    chunks = []

    # Split by newline
    chunk = sentence
    if len(chunk) <= max_len:
        chunks.append(chunk)
    else:
        # Split by "[,;]\s"
        split_points = [m.start() for m in re.finditer(r"[,;]\s", chunk)]
        if split_points:
            last_pos = 0
            for pos in split_points:
                next_pos = pos + 2
                segment = chunk[last_pos:next_pos]
                if len(segment) > max_len:
                    # For too long segments
                    chunks.extend(split_by_words(segment, max_len))
                elif len(segment) < min_len and last_pos > 0:
                    # Merge short segment with previous chunk
                    chunks[-1] += segment
                else:
                    chunks.append(segment)
                last_pos = next_pos
            # Handle remaining text
            if last_pos < len(chunk):
                chunks.extend(split_by_words(chunk[last_pos:], max_len))
        else:
            chunks.extend(split_by_words(chunk, max_len))

    for i, chunk in enumerate(chunks):
        if len(chunk) > max_len:
            chunks[i : i + 1] = split_by_words(chunk, max_len)
    return [chunk for chunk in chunks if chunk]


def merge_short_sentences(sentences: list[str], min_len=50, max_len=300) -> list[str]:
    """Merge those shorter than min_len with the next sentence"""
    if not sentences:
        return []

    result = []
    current_sentence = sentences[0]

    for i in range(1, len(sentences)):
        if len(current_sentence) < min_len and len(sentences[i]) < max_len:
            current_sentence += sentences[i]
        else:
            result.append(current_sentence)
            current_sentence = sentences[i]

    if current_sentence:
        result.append(current_sentence)

    return result


def split_text_to_sentences(text: str, language: str) -> List[str]:
    """Tokenize text into sentences"""
    sentences = sent_tokenize(text, language=language)

    new_sentences = []
    for sentence in sentences:
        if len(sentence) > 350:
            new_sentences.extend(split_long_sentence(sentence, max_len=350))
        else:
            new_sentences.extend([sentence])

    # new_sentences = merge_short_sentences(new_sentences, min_len=50, max_len=300)
    return new_sentences
