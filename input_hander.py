import argparse
import sys
from dataclasses import dataclass
from typing import Optional

from config import (
    DEFAULT_LANGUAGE,
    DEFAULT_SPEED,
    DEFAULT_VOICE,
    MAX_SPEED,
    MIN_SPEED,
    console,
)
from utils import (
    display_languages,
    display_voices,
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
    verbose: bool


def parse_args() -> Args:
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        prog="kokorodoki",
        description="Real-time TTS with Kokoro-82M. Use !commands to adjust settings.",
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
        "--history-off",
        "--history_off",
        action="store_true",
        help="Disable the saving of history",
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
        "--all",
        action="store_true",
        help="Read a text/file with all the available voices (only valid when --text or --file is used)",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="daemon mode",
    )
    parser.add_argument(
        "--verbose",
        "-V",
        action="store_true",
        help="Print what is being done",
    )

    args = parser.parse_args()

    # Display lists if requested
    if args.list_languages:
        display_languages()
        sys.exit(0)

    if args.list_voices is not False:
        display_voices(args.list_voices)
        sys.exit(0)

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
    if not args.voice.startswith(args.language):
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

    if args.output is not None and not args.output.endswith(".wav"):
        console.print("[bold red]Error:[/] The output file name should end with .wav")
        sys.exit(1)

    # Validate that output/all isn't used without input
    if args.output is not None and args.all:
        console.print("[bold red]Error:[/] --output/-o can't be used with --all")
        sys.exit(1)
    if args.output is not None and args.text is None and args.file is None:
        console.print("[bold red]Error:[/] --output/-o can only be used with --text or --file")
        sys.exit(1)
    if args.all and args.text is None and args.file is None:
        console.print("[bold red]Error:[/] --all can only be used with --text or --file")
        sys.exit(1)

    # Handle input text/file
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
        args.verbose,
    )


def get_input(history_off: bool, prompt="> ") -> str:
    user_input = input(prompt).strip()
    save_history(history_off)
    return user_input
