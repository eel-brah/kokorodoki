import socket
import sys
import threading
from typing import Optional

from config import HOST, MAX_SPEED, MIN_SPEED, PORT, PROMPT, REPO_ID, console

with console.status(
    "[yellow]Initializing Kokoro...[/]",
    spinner="dots",
    spinner_style="yellow",
    speed=0.8,
):
    from kokoro import KPipeline
console.print("[bold green]Kokoro initialized!")

from input_hander import Args, get_input
from models import TTSPlayer
from utils import (
    clear_history,
    display_help,
    display_languages,
    display_voices,
    get_language_map,
    get_voices,
)


def start(args: Args) -> None:
    """Initialize and run"""
    try:
        with console.status(
            "[yellow]Initializing Kokoro pipeline...[/]",
            spinner="dots",
            spinner_style="yellow",
            speed=0.8,
        ):
            # Initialize TTS pipeline
            pipeline = KPipeline(
                lang_code=args.language, repo_id=REPO_ID, device=args.device
            )
        console.print("[bold green]Kokoro pipeline initialized!")

        if args.daemon:
            run_deamon(
                pipeline,
                args.language,
                args.voice,
                args.speed,
                args.verbose,
            )
        elif args.all_voices and args.input_text:
            run_with_all(
                pipeline, args.language, args.speed, args.verbose, args.input_text
            )
        elif args.input_text:
            run_noninteractive(
                pipeline,
                args.language,
                args.voice,
                args.speed,
                args.verbose,
                args.input_text,
                args.output_file,
            )
        else:
            run_interactive(
                pipeline,
                args.language,
                args.voice,
                args.speed,
                args.verbose,
                args.history_off,
                args.device,
                PROMPT,
            )
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Terminated[/]")
    except EOFError:
        console.print("\n")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")


def speak_thread(clipboard_data, player):
    try:
        player.speak(clipboard_data, interactive=False)
    except Exception as e:
        print(f"Error in thread: {str(e)}")


def run_deamon(
    pipeline: KPipeline,
    language: str,
    voice: str,
    speed: float,
    verbose: bool,
) -> None:
    """Start daemon mode"""
    current_thread = None
    player = TTSPlayer(pipeline, language, voice, speed, verbose)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((HOST, PORT))
            server_socket.listen(1)
            print(f"Listening on {HOST}:{PORT}...")

            while True:
                conn, addr = server_socket.accept()
                with conn:
                    print(f"Connected by {addr}")
                    data = b""
                    while True:
                        chunk = conn.recv(4096)
                        if not chunk:
                            break
                        data += chunk

                    clipboard_data = data.decode()
                    print(f"Received {clipboard_data[:20]}")

                    if clipboard_data == "!stop":
                        print("Stopping previous playback...")
                        if current_thread is not None and current_thread.is_alive():
                            print("Stopping previous playback...")
                            player.stop_playback()
                            current_thread.join()
                        continue

                    # Stop previous thread
                    if current_thread is not None and current_thread.is_alive():
                        print("Stopping previous playback...")
                        player.stop_playback()
                        current_thread.join()

                    # Start new thread
                    current_thread = threading.Thread(
                        target=speak_thread,
                        args=(clipboard_data, player),
                    )
                    current_thread.daemon = True
                    current_thread.start()
                    print("Started new playback thread")

    except KeyboardInterrupt:
        print("Exiting...")
        if current_thread is not None and current_thread.is_alive():
            player.stop_playback()
            current_thread.join(timeout=1)
        sys.exit()
    except Exception as e:
        print(f"Error: {str(e)}")
        if current_thread is not None and current_thread.is_alive():
            player.stop_playback()
            current_thread.join(timeout=1)


def run_with_all(
    pipeline: KPipeline,
    language: str,
    speed: float,
    verbose: bool,
    input_text: str,
) -> None:
    """Run with all available voices"""
    console.print(
        f"\n[bold blue]Reading with all available {get_language_map()[language]} voices[/]\n"
    )
    target_voices = [voice for voice in get_voices() if voice.startswith(language)]

    player = TTSPlayer(pipeline, language, target_voices[0], speed, verbose)
    try:
        for voice in target_voices:
            player.change_voice(voice)
            console.print(f"[cyan]{voice} speaking:[/] {input_text[:30]}")
            player.speak(input_text, interactive=False)
    except KeyboardInterrupt:
        console.print("[bold yellow]Exiting...[/]")
        sys.exit()


def run_noninteractive(
    pipeline: KPipeline,
    language: str,
    voice: str,
    speed: float,
    verbose: bool,
    input_text: str,
    output_file: Optional[str],
) -> None:
    """Generate audio"""
    player = TTSPlayer(pipeline, language, voice, speed, verbose)
    if output_file is None:
        try:
            with console.status(
                f"[cyan]Speaking:[/] {input_text[:30]}", spinner_style="cyan"
            ):
                player.speak(input_text, interactive=False)
        except KeyboardInterrupt:
            console.print("[bold yellow]Exiting...[/]")
            sys.exit()
    else:
        player.generate_audio_file(input_text, output_file=output_file)


def run_interactive(
    pipeline: KPipeline,
    language: str,
    voice: str,
    speed: float,
    verbose: bool,
    history_off: bool,
    device: str,
    prompt="> ",
) -> None:
    """Run an interactive TTS session with dynamic settings."""

    player = TTSPlayer(pipeline, language, voice, speed, verbose)

    console.rule("[bold green]Interactive TTS started[/]")
    display_help()

    # Display starting configuration
    console.print("[green]Starting with:[/]")
    console.print(f"  Language: [cyan]{get_language_map()[language]}[/]")
    console.print(f"  Voice: [cyan]{voice}[/]")
    console.print(f"  Speed: [cyan]{speed}[/]")
    while True:
        try:
            user_input = get_input(history_off, prompt)
            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("!"):
                parts = user_input.split(maxsplit=1)
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""

                if cmd == "!lang":
                    if player.change_language(arg, device):
                        console.print(
                            f"[green]Language changed to:[/] {player.languages[arg]}"
                        )
                    else:
                        console.print("[red]Invalid language code.[/]")
                        display_languages()

                elif cmd == "!voice":
                    if player.change_voice(arg):
                        console.print(f"[green]Voice changed to:[/] {arg}")
                    else:
                        console.print("[red]Invalid voice.[/]")
                        console.print("Use !list_voices to see options.")

                elif cmd == "!speed":
                    try:
                        new_speed = float(arg)
                        if player.change_speed(new_speed):
                            console.print(f"[green]Speed changed to:[/] {new_speed}")
                        else:
                            console.print(
                                f"[red]Speed must be between {MIN_SPEED} and {MAX_SPEED}[/]"
                            )
                    except ValueError:
                        console.print("[red]Invalid speed value[/]")

                elif cmd == "!stop":
                    player.stop_playback()

                elif cmd == "!list_langs":
                    display_languages()

                elif cmd == "!list_voices":
                    display_voices()

                elif cmd in ("!help", "!h"):
                    display_help()

                elif cmd in ("!quit", "!q"):
                    console.print("[bold yellow]Exiting...[/]")
                    break

                elif cmd == "!clear":
                    print("\033[H\033[J", end="")

                elif cmd == "!clear_history":
                    clear_history()

                elif cmd == "!verbose":
                    player.verbose = not player.verbose
                else:
                    console.print(f"[red]Unknown command: {cmd}[/]")
                    console.print("Type !help for available commands.")

                continue

            with console.status(
                f"[cyan]Speaking:[/] {user_input[:30]}", spinner_style="cyan"
            ):
                player.speak(user_input)

        except KeyboardInterrupt:
            player.stop_playback(False)
            console.print("\n[bold yellow]Interrupted. Type !q to exit.[/]")
        except EOFError:
            console.print("\n[bold yellow]Type !q to exit.[/]")
        except Exception as e:
            console.print(f"[bold red]Error:[/] {str(e)}")
