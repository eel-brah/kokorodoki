import argparse
import sys
from typing import Tuple

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


def parse_args() -> Tuple[str, str, float, bool]:
    """Parse command-line arguments for language, voice, and speed."""
    parser = argparse.ArgumentParser(
        description="Real-time TTS with Kokoro-82M. Use !commands to adjust settings."
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
        action="store_true",
        help="List available languages",
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List available voices",
    )
    parser.add_argument(
        "--history_off",
        action="store_true",
        help="Disable the saving of history",
    )

    args = parser.parse_args()

    # Display lists if requested
    if args.list_languages:
        display_languages()
        sys.exit(0)

    if args.list_voices:
        display_voices()
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

    if not MIN_SPEED <= args.speed <= MAX_SPEED:
        console.print(
            f"[bold red]Error:[/] Speed must be between {MIN_SPEED} and {MAX_SPEED}"
        )
        sys.exit(1)

    return args.language, args.voice, args.speed, args.history_off


def get_input(history_off: bool, prompt="> ") -> str:
    user_input = input(prompt).strip()
    save_history(history_off)
    return user_input
