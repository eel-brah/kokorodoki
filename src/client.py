import argparse
import os
import socket
import subprocess
import sys
from enum import Enum
from typing import Optional, Tuple

from config import DEFAULT_LANGUAGE, HOST, MAX_SPEED, MIN_SPEED, PORT
from utils import display_languages, display_voices, get_language_map, get_voices


class Action(Enum):
    NONE = 0
    STOP = 1
    PAUSE = 2
    RESUME = 3
    NEXT = 4
    BACK = 5
    EXIT = 6


ACTION_MAPPING = {
    "stop": Action.STOP,
    "pause": Action.PAUSE,
    "resume": Action.RESUME,
    "next": Action.NEXT,
    "back": Action.BACK,
    "exit": Action.EXIT,
}

ACTION_COMMANDS = {
    Action.EXIT: "!exit",
    Action.STOP: "!stop",
    Action.PAUSE: "!pause",
    Action.RESUME: "!resume",
    Action.NEXT: "!next",
    Action.BACK: "!back",
}


def get_clipboard() -> Optional[str | bytes]:
    """Get clipboard content on X11 or Wayland"""
    is_wayland = os.environ.get("WAYLAND_DISPLAY") is not None

    if is_wayland:
        try:
            try:
                result = subprocess.run(
                    ["wl-paste", "--no-newline"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                return result.stdout
            except UnicodeDecodeError:
                result = subprocess.run(
                    ["wl-paste", "--type", "image/png"],
                    capture_output=True,
                    check=True,
                )
                return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error reading Wayland clipboard: {e}")
            print(f"Command returned {e.returncode}")
            print(f"Error output: {e.stderr}")
            return None
        except FileNotFoundError:
            print("Error: wl-paste is not installed. Please install wl-clipboard.")
            return None
        except Exception as e:
            print(f"Unexpected error on Wayland: {e}")
            return None
    else:
        try:
            try:
                result = subprocess.run(
                    ["xclip", "-selection", "clipboard", "-o"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                return result.stdout.strip()
            except subprocess.CalledProcessError:
                result = subprocess.run(
                    ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"],
                    capture_output=True,
                    check=True,
                )
                return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error reading X11 clipboard: {e}")
            print(f"Command returned {e.returncode}")
            print(f"Error output: {e.stderr}")
            return None
        except FileNotFoundError:
            print("Error: xclip is not installed. Please install it first.")
            return None
        except Exception as e:
            print(f"Unexpected error on X11: {e}")
            return None


def send_clipboard() -> None:
    """Send clipboard content"""
    clipboard_content = get_clipboard()

    if clipboard_content is not None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((HOST, PORT))
            if isinstance(clipboard_content, bytes):
                client_socket.sendall(b"IMAGE:" + clipboard_content)
            else:
                client_socket.sendall(b"TEXT:" + clipboard_content.encode())


def send_action(action: str) -> None:
    """Send action"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))
        client_socket.sendall(action.encode())


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


def parse_args() -> Tuple[Action, Optional[float], Optional[str], Optional[str], bool]:
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Interact with kokorodoki daemon",
    )

    global PORT

    parser.add_argument(
        "--port", type=int, default=PORT, help=f"Choose a port number (default: {PORT})"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Get current settings",
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
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--stop",
        action="store_true",
        help="Stop reading",
    )
    input_group.add_argument(
        "--pause",
        action="store_true",
        help="Pause reading",
    )
    input_group.add_argument(
        "--resume",
        action="store_true",
        help="Resume reading",
    )
    input_group.add_argument(
        "--next",
        action="store_true",
        help="Skip a sentence",
    )
    input_group.add_argument(
        "--back",
        action="store_true",
        help="Back one sentence",
    )
    input_group.add_argument(
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

    if args.language is None and args.voice is not None:
        args.language = args.voice[0]
    elif args.language is not None and args.language not in languages:
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

    action = next(
        (ACTION_MAPPING[flag] for flag in ACTION_MAPPING if getattr(args, flag, False)),
        Action.NONE,
    )

    PORT = args.port
    return (
        action,
        args.speed,
        args.language,
        args.voice,
        args.status,
    )


def send(
    action: Action,
    speed: Optional[float],
    language: Optional[str],
    voice: Optional[str],
    status: bool,
) -> None:
    "Send commands or clipboard."
    if action in ACTION_COMMANDS:
        send_action(ACTION_COMMANDS[action])
        return

    if speed is None and voice is None and language is None and not status:
        send_clipboard()
        return

    if language is not None:
        send_language(language)
    if speed is not None:
        send_speed(speed)
    if voice is not None:
        send_voice(voice)
    if status:
        send_action("!status")


def main():
    """Main entry point."""
    # action, speed, language, voice, status = parse_args()
    send(*parse_args())


if __name__ == "__main__":
    main()
