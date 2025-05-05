import argparse
import sys
from dataclasses import dataclass
from typing import Optional

from config import (
    DEFAULT_LANGUAGE,
    DEFAULT_SPEED,
    DEFAULT_THEME,
    DEFAULT_VOICE,
    MAX_SPEED,
    MIN_SPEED,
    PORT,
    console,
)
from utils import (
    display_languages,
    display_themes,
    display_voices,
    get_gui_themes,
    get_language_map,
    get_voices,
    save_history,
)


@dataclass
class Args:
    language: str
    voice: str
    speed: float
    history_off: bool
    device: Optional[str]
    input_text: Optional[str]
    output_file: Optional[str]
    all_voices: bool
    daemon: bool
    port: int
    gui: bool
    theme: int
    verbose: bool
    ctrl_c: bool


def parse_args() -> Args:
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        prog="kokorodoki",
        description="Real-time TTS with Kokoro-82M. Use !commands to adjust settings.",
    )

    parser.add_argument(
        "--list-languages",
        "--list_languages",
        action="store_true",
        help="List available languages",
    )
    parser.add_argument(
        "--list-voices",
        "--list_voices",
        type=str,
        nargs="?",
        const=None,
        default=False,
        help="List available voices. Optionally provide a language to filter by.",
    )
    parser.add_argument(
        "--themes",
        action="store_true",
        help="Show the available gui themes",
    )

    parser.add_argument(
        "--language",
        "-l",
        type=str,
        default=DEFAULT_LANGUAGE,
        help=f"Initial language code (default: '{DEFAULT_LANGUAGE}' for American English)",
    )
    parser.add_argument(
        "--voice",
        "-v",
        type=str,
        default=DEFAULT_VOICE,
        help=f"Initial voice (default: '{DEFAULT_VOICE}')",
    )
    parser.add_argument(
        "--speed",
        "-s",
        type=float,
        default=DEFAULT_SPEED,
        help=f"Initial speed (default: {DEFAULT_SPEED}, range: {MIN_SPEED}-{MAX_SPEED})",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        choices=["cuda", "cpu"],
        help=(
            "Set the device for computation ('cuda' for GPU or 'cpu'). "
            "Default: Auto-selects 'cuda' if available, otherwise falls back to 'cpu'. "
            "If 'cuda' is specified but unavailable, raises an error."
        ),
    )

    parser.add_argument(
        "--history-off",
        "--history_off",
        action="store_true",
        help="Disable the saving of history",
    )
    parser.add_argument(
        "--verbose",
        "-V",
        action="store_true",
        help="Print what is being done",
    )
    parser.add_argument(
        "--ctrl_c_off",
        "-c",
        action="store_true",
        help="Make Ctrl+C not end playback",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Read a text/file with all the available voices (only valid when --text or --file is used)",
    )
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--text",
        "-t",
        default=None,
        type=str,
        help="Supply text",
    )
    input_group.add_argument(
        "--file",
        "-f",
        default=None,
        type=str,
        help="Supply path to a text file",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output file path (only valid when --text or --file is used)",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Daemon mode",
    )
    parser.add_argument(
        "--port", type=int, default=PORT, help=f"Choose a port number (default: {PORT})"
    )
    parser.add_argument(
        "--gui",
        "-g",
        action="store_true",
        help="Gui mode",
    )
    parser.add_argument(
        "--theme",
        type=int,
        default=DEFAULT_THEME,
        help=f"Choose a theme number (default: {get_gui_themes()[DEFAULT_THEME]}, use --themes to get list of themes)",
    )

    args = parser.parse_args()

    # Display lists if requested
    if args.list_languages:
        display_languages()
        sys.exit(0)

    if args.list_voices is not False:
        display_voices(args.list_voices)
        sys.exit(0)

    if args.themes:
        display_themes()
        sys.exit(0)

    # Validate modes
    selected_mode = sum(
        [args.gui, args.daemon, (args.text is not None or args.file is not None)]
    )
    if selected_mode not in (0, 1):
        console.print(
            "[bold red]Error:[/] Only one mode (Console, GUI, Daemon, or CLI) can be selected."
        )
        sys.exit(0)
    if args.theme != DEFAULT_THEME and not args.gui:
        console.print(
            "[bold yellow]Warning:[/] Invalid use of --theme without --gui or -g"
        )
    if selected_mode == 1 and (args.verbose or args.ctrl_c_off or args.history_off):
        console.print(
            "[bold yellow]Warning:[/] Invalid use of verbose, ctrl_c_off, or history_off with mode other than Console."
        )
    if args.port != PORT and not args.daemon:
        console.print("[bold yellow]Warning:[/] Invalid use of --port without --daemon")

    # Validate inputs
    languages = get_language_map()
    voices = get_voices()

    if args.language not in languages:
        console.print(f"[bold red]Error:[/] Invalid language '{args.language}'")
        display_languages()
        sys.exit(1)

    if args.voice not in voices:
        console.print(f"[bold red]Error:[/] Invalid voice '{args.voice}'")
        display_voices()
        sys.exit(1)
    if not args.all and not args.voice.startswith(args.language):
        console.print(
            f"[bold red]Error:[/] Voice '{args.voice}' is not made for language '{get_language_map()[args.language]}'"
        )
        display_voices()
        sys.exit(1)

    if not MIN_SPEED <= args.speed <= MAX_SPEED:
        console.print(
            f"[bold red]Error:[/] Speed must be between {MIN_SPEED} and {MAX_SPEED}"
        )
        sys.exit(1)

    if args.theme not in get_gui_themes():
        console.print("[bold red]Error:[/] Invalid theme")
        display_themes()
        sys.exit(1)

    if not 0 <= args.port <= 65535:
        console.print(
            f"[bold red]Error:[/] Port {args.port} is out of valid range (0-65535)."
        )
        sys.exit(1)

    if args.output is not None and not args.output.endswith(".wav"):
        console.print("[bold red]Error:[/] The output file name should end with .wav")
        sys.exit(1)

    # Validate that output or all isn't used without input
    if args.output is not None and args.all:
        console.print("[bold red]Error:[/] --output/-o can't be used with --all")
        sys.exit(1)
    if args.output is not None and args.text is None and args.file is None:
        console.print(
            "[bold red]Error:[/] --output/-o can only be used with --text or --file"
        )
        sys.exit(1)
    if args.all and args.text is None and args.file is None:
        console.print(
            "[bold red]Error:[/] --all can only be used with --text or --file"
        )
        sys.exit(1)

    # Handle input
    input_text = None
    if args.file is not None:
        if not args.file.strip():
            console.print("[bold red]Error:[/] File path cannot be empty")
            sys.exit(1)
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                input_text = f.read()
        except Exception as e:
            console.print(f"[bold red]Error reading file:[/] {e}")
            sys.exit(1)
    elif args.text is not None:
        if not args.text.strip():
            console.print("[bold red]Error:[/] Text cannot be empty")
            sys.exit(1)
        input_text = args.text

    return Args(
        args.language,
        args.voice,
        args.speed,
        args.history_off,
        args.device,
        input_text,
        args.output,
        args.all,
        args.daemon,
        args.port,
        args.gui,
        args.theme,
        args.verbose,
        args.ctrl_c_off,
    )


def get_input(history_off: bool, prompt="> ") -> str:
    user_input = input(prompt).strip()
    save_history(history_off)
    return user_input
