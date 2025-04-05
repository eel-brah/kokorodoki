import argparse
import socket
import subprocess
import sys
from typing import Optional, Tuple

from config import DEFAULT_LANGUAGE, HOST, MAX_SPEED, MIN_SPEED, PORT
from utils import display_languages, display_voices, get_language_map, get_voices


def get_clipboard() -> Optional[str]:
    """Get clipboard content"""
    try:
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    except subprocess.CalledProcessError as e:
        print(f"Error reading clipboard: {e}")
        print(f"Command returned {e.returncode}")
        print(f"Error output: {e.stderr}")
        return None
    except FileNotFoundError:
        print("Error: xclip is not installed. Please install it first.")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def send_clipboard() -> None:
    """Send clipboard content"""
    clipboard_content = get_clipboard()
    if clipboard_content is not None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((HOST, PORT))
            client_socket.sendall(clipboard_content.encode())


def send_stop() -> None:
    """Stop reading"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))
        client_socket.sendall("!stop".encode())


def send_exit() -> None:
    """Stop reading"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))
        client_socket.sendall("!exit".encode())


def send_speed(speed: float) -> None:
    """Send new speed"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))
        client_socket.sendall(f"!speed {speed}".encode())


def send_language(language: str) -> None:
    """Send new language"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))
        client_socket.sendall(f"!lang {language}".encode())


def send_voice(voice: str) -> None:
    """Send new voice"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))
        client_socket.sendall(f"!voice {voice}".encode())


def parse_args() -> Tuple[bool, Optional[float], Optional[str], Optional[str], bool]:
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Interact with kokorodoki daemon",
    )

    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop reading",
    )
    parser.add_argument(
        "--language",
        "-l",
        type=str,
        help=f"Change language ('{DEFAULT_LANGUAGE}' for American English)",
    )
    parser.add_argument(
        "--voice",
        "-v",
        type=str,
        help="Change voice",
    )
    parser.add_argument(
        "--speed",
        "-s",
        type=float,
        help=f"Change speed (range: {MIN_SPEED}-{MAX_SPEED})",
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
        "--exit",
        action="store_true",
        help="Stop reading",
    )
    args = parser.parse_args()

    if args.list_languages:
        display_languages()
        sys.exit(0)

    if args.list_voices is not False:
        display_voices(args.list_voices)
        sys.exit(0)

    languages = get_language_map()
    voices = get_voices()

    if args.language is not None and args.language not in languages:
        print(f"Error: Invalid language '{args.language}'")
        display_languages()
        sys.exit(1)

    if args.voice is not None:
        if args.voice not in voices:
            print(f"Error: Invalid voice '{args.voice}'")
            display_voices()
            sys.exit(1)
        if not args.voice.startswith(args.language):
            print(
                f"Error: Voice '{args.voice}' is not made for language '{get_language_map()[args.language]}'"
            )
            display_voices()
            sys.exit(1)

    if args.speed is not None and not MIN_SPEED <= args.speed <= MAX_SPEED:
        print(f"Error: Speed must be between {MIN_SPEED} and {MAX_SPEED}")
        sys.exit(1)

    return (args.stop, args.speed, args.language, args.voice, args.exit)


def send(
    stop: bool,
    speed: Optional[float],
    language: Optional[str],
    voice: Optional[str],
    _exit: bool,
) -> None:
    "Send commands or clipboard."
    if _exit:
        send_exit()
        return

    if stop:
        send_stop()
    elif speed is None and voice is None and language is None:
        send_clipboard()
        return

    if speed is not None:
        send_speed(speed)
    if voice is not None:
        send_voice(voice)
    if language is not None:
        send_language(language)


def main():
    """Main entry point."""
    stop, speed, language, voice, _exit = parse_args()

    send(stop, speed, language, voice, _exit)


if __name__ == "__main__":
    main()
