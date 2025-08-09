import socket
import sys
import threading
import time
import warnings
from typing import Optional

from config import (
    DEFAULT_LANGUAGE,
    DEFAULT_SPEED,
    DEFAULT_VOICE,
    HOST,
    MAX_SPEED,
    TIMEOUT,
    MIN_SPEED,
    PORT,
    PROMPT,
    REPO_ID,
    SAMPLE_RATE,
    console,
)

with console.status(
    "[yellow]Initializing Kokoro...[/]",
    spinner="dots",
    spinner_style="yellow",
    speed=0.8,
):
    # Ignoring the following warnings:
    # 1. RNN dropout warning (UserWarning) - Expected behavior when dropout > 0 with num_layers=1
    # 2. weight_norm deprecation (FutureWarning) - Still functional, will update when PyTorch removes it
    # These are safe to suppress as they don't affect model behavior.
    warnings.filterwarnings(
        "ignore",
        message="dropout option adds dropout after all but last recurrent layer",
        category=UserWarning,
        module="torch.nn.modules.rnn",
    )
    warnings.filterwarnings(
        "ignore",
        message=r"`torch\.nn\.utils\.weight_norm` is deprecated",
        category=FutureWarning,
        module="torch.nn.utils.weight_norm",
    )
    from kokoro import KPipeline
console.print("[bold green]Kokoro initialized!")

import easyocr
import nltk

from input_hander import Args, get_input
from models import TTSPlayer
from utils import (
    clear_history,
    display_help,
    display_languages,
    display_status,
    display_voices,
    format_status,
    get_easyocr_language_map,
    get_language_map,
    get_voices,
    split_text_to_sentences,
)

running_threads = 1

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

        # Download nltk tokenizers if not found
        try:
            nltk.data.find("tokenizers/punkt")
            nltk.data.find("tokenizers/punkt_tab")
        except LookupError:
            with console.status(
                "[yellow]Download nltk tokenizers...[/]",
                spinner="dots",
                spinner_style="yellow",
                speed=0.8,
            ):
                nltk.download("punkt", quiet=True)
                nltk.download("punkt_tab", quiet=True)
            console.print("[bold green]Downloading nltk tokenizers finished!")

        # audio_warmup()

        if args.setup:
            return
        elif args.daemon:
            easyocr_lang = [
                lang
                for code, lang in get_easyocr_language_map().items()
                if code == args.language
            ]

            image_reader = easyocr.Reader(easyocr_lang)
            run_daemon(
                pipeline,
                args.language,
                args.voice,
                args.speed,
                args.device,
                args.verbose,
                args.port,
                image_reader,
            )
        elif args.gui:
            from gui import run_gui

            easyocr_lang = [
                lang
                for code, lang in get_easyocr_language_map().items()
                if code == args.language
            ]

            image_reader = easyocr.Reader(easyocr_lang)
            run_gui(
                pipeline,
                args.language,
                args.voice,
                args.speed,
                args.device,
                args.theme,
                image_reader,
            )
        elif args.all_voices and args.input_text:
            run_with_all(
                pipeline, args.language, args.speed, args.verbose, args.input_text
            )
        elif args.input_text:
            run_cli(
                pipeline,
                args.language,
                args.voice,
                args.speed,
                args.verbose,
                args.input_text,
                args.output_file,
            )
        else:
            run_console(
                pipeline,
                args.language,
                args.voice,
                args.speed,
                args.verbose,
                args.history_off,
                args.device,
                args.ctrl_c,
                PROMPT,
            )
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Terminated[/]")
    except EOFError:
        console.print("\n")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")


def speak_thread(clipboard_data: str, player: TTSPlayer) -> None:
    """Player speak wrapper"""
    try:
        player.speak(clipboard_data, console_mode=False)
    except Exception as e:
        print(f"Error in thread: {str(e)}")


def run_daemon(
    pipeline: KPipeline,
    language: str,
    voice: str,
    speed: float,
    device: Optional[str],
    verbose: bool,
    port: int,
    image_reader: easyocr.Reader,
) -> None:
    """Start daemon mode"""
    current_thread = None
    player = TTSPlayer(pipeline, language, voice, speed, verbose)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((HOST, port))
            server_socket.listen(1)
            print(f"Listening on {HOST}:{port}...")

            while True:
                conn, addr = server_socket.accept()
                with conn:
                    print(f"Connected by {addr}")

                    # Read all
                    data = b""
                    while True:
                        chunk = conn.recv(4096)
                        if not chunk:
                            break
                        data += chunk

                    if data.startswith(b"IMAGE:"):
                        results = image_reader.readtext(data[6:])
                        clipboard_data = ""
                        clipboard_data = " ".join(
                            text for _, text, _ in results if text
                        ).strip()
                        if not clipboard_data:
                            continue
                    elif data.startswith(b"TEXT:"):
                        clipboard_data = data[5:].decode()
                    else:
                        clipboard_data = data.decode()

                    print(f"Received {clipboard_data[:20]}...")

                # Handle commands
                if clipboard_data.startswith("!"):
                    parts = clipboard_data.split(maxsplit=1)
                    cmd = parts[0].lower()
                    arg = parts[1] if len(parts) > 1 else ""

                    if cmd == "!lang":
                        if player.change_language(arg, device):
                            print(f"Language changed to: {player.languages[arg]}")

                            easyocr_lang = [
                                lang
                                for code, lang in get_easyocr_language_map().items()
                                if code == arg
                            ]
                            image_reader = easyocr.Reader(easyocr_lang)
                        else:
                            print("Invalid language code.")

                    elif cmd == "!voice":
                        if player.change_voice(arg):
                            print(f"Voice changed to: {arg}")
                        else:
                            print("Invalid voice.")

                    elif cmd == "!speed":
                        try:
                            new_speed = float(arg)
                            if player.change_speed(new_speed):
                                print(f"Speed changed to: {new_speed}")
                            else:
                                print(
                                    f"Speed must be between {MIN_SPEED} and {MAX_SPEED}"
                                )
                        except ValueError:
                            print("Invalid speed value")

                    elif cmd == "!pause":
                        player.pause_playback()
                    elif cmd == "!resume":
                        player.resume_playback()
                    elif cmd == "!back":
                        player.back_sentence()
                    elif cmd == "!next":
                        player.skip_sentence()
                    elif cmd in ("!stop", "!exit", "!status"):
                        if current_thread is not None and current_thread.is_alive():
                            print("Stopping previous playback...")
                            player.stop_playback()
                            current_thread.join()
                        if cmd == "!exit":
                            print("Exiting...")
                            if current_thread is not None and current_thread.is_alive():
                                print("Stopping previous playback...")
                                player.stop_playback()
                                current_thread.join()
                            sys.exit(0)
                        if cmd == "!status":
                            status_str = format_status(
                                player.language, player.voice, player.speed
                            )
                            current_thread = threading.Thread(
                                target=speak_thread,
                                args=(status_str, player),
                            )
                            current_thread.daemon = True
                            current_thread.start()
                else:
                    if current_thread is not None and current_thread.is_alive():
                        print("Stopping previous playback...")
                        player.stop_playback()
                        current_thread.join()
                    sentences = split_text_to_sentences(
                        clipboard_data, player.nltk_language
                    )
                    current_thread = threading.Thread(
                        target=speak_thread,
                        args=(sentences, player),
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
        try:
            if "Address already in use" in str(e):
                print(f"Error: Port {port} is already in use.")
                print("This could be due to:")
                print("  - Another instance of this program running.")
                print(f"  - A different process using port {port}.")
                print("To resolve this:")
                print(
                    "  - Check for and terminate any other instances of this program."
                )
                print(
                    "  - Alternatively, use a different port with the --port option (e.g., --port 9911)."
                )
            run_cli(
                pipeline,
                DEFAULT_LANGUAGE,
                DEFAULT_VOICE,
                DEFAULT_SPEED,
                False,
                f"Error: {str(e)[:40]}. for more info see logs. Exiting.",
                None,
            )
        except Exception as e:
            pass


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
    sentences = split_text_to_sentences(input_text, player.nltk_language)
    try:
        for voice in target_voices:
            player.change_voice(voice)
            console.print(f"[cyan]{voice} speaking:[/] {input_text[:30]}")
            player.speak(sentences, console_mode=False)
    except KeyboardInterrupt:
        console.print("[bold yellow]Exiting...[/]")
        global running_threads
        if threading.active_count() > running_threads:
            player.stop_playback(False)
            start_time = time.time()
            while threading.active_count() > running_threads and (time.time() - start_time) < TIMEOUT:
                time.sleep(0.1)
            if threading.active_count() > running_threads:
                console.print("[red]Warning: Threads still active after timeout, proceeding anyway.[/]")
                running_threads += 1
        sys.exit()


def run_cli(
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
    sentences = split_text_to_sentences(input_text, player.nltk_language)
    if output_file is None:
        try:
            with console.status(
                f"[cyan]Speaking:[/] {input_text[:30]}...", spinner_style="cyan"
            ):
                player.speak(sentences, console_mode=False)
        except KeyboardInterrupt:
            console.print("[bold yellow]Exiting...[/]")
            global running_threads
            if threading.active_count() > running_threads:
                player.stop_playback(False)
                start_time = time.time()
                while threading.active_count() > running_threads and (time.time() - start_time) < TIMEOUT:
                    time.sleep(0.1)
                if threading.active_count() > running_threads:
                    console.print("[red]Warning: Threads still active after timeout, proceeding anyway.[/]")
                    running_threads += 1
            sys.exit()
    else:
        player.generate_audio_file(sentences, output_file=output_file)


def run_console(
    pipeline: KPipeline,
    language: str,
    voice: str,
    speed: float,
    verbose: bool,
    history_off: bool,
    device: Optional[str],
    ctrlc: bool,
    prompt="> ",
) -> None:
    """Run an interactive TTS session with dynamic settings."""

    player = TTSPlayer(pipeline, language, voice, speed, verbose, ctrlc)

    console.rule("[bold green]Interactive TTS started[/]")
    display_help()

    # Display starting configuration
    console.print("[green]Starting with:[/]")
    console.print(f"  Language: [cyan]{get_language_map()[language]}[/]")
    console.print(f"  Voice: [cyan]{voice}[/]")
    console.print(f"  Speed: [cyan]{speed}[/]")
    global running_threads
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

                elif cmd in ("!s", "!stop"):
                    player.stop_playback()

                elif cmd in ("!p", "!pause"):
                    player.pause_playback()

                elif cmd in ("!r", "!resume"):
                    player.resume_playback()

                elif cmd in ("!b", "!back"):
                    player.back_sentence()

                elif cmd in ("!n", "!next"):
                    player.skip_sentence()

                elif cmd == "!list_langs":
                    display_languages()

                elif cmd == "!list_voices":
                    display_voices(player.language)

                elif cmd == "!list_all_voices":
                    display_voices()

                elif cmd in ("!help", "!h"):
                    display_help()

                elif cmd in ("!quit", "!q"):
                    console.print("[bold yellow]Exiting...[/]")
                    if threading.active_count() > running_threads:
                        player.stop_playback(False)
                        start_time = time.time()
                        while threading.active_count() > running_threads and (time.time() - start_time) < TIMEOUT:
                            time.sleep(0.1)
                        if threading.active_count() > running_threads:
                            console.print("[red]Warning: Threads still active after timeout, proceeding anyway.[/]")
                            running_threads += 1
                    break

                elif cmd == "!clear":
                    print("\033[H\033[J", end="")

                elif cmd == "!clear_history":
                    clear_history()

                elif cmd == "!ctrlc":
                    player.ctrlc = not player.ctrlc
                    if player.ctrlc:
                        console.print("[green]Ctrl+C ends the playback")
                    else:
                        console.print("[green]Ctrl+C gives a new line")

                elif cmd in ("!status", "!h"):
                    display_status(player.language, player.voice, player.speed)

                elif cmd == "!verbose":
                    player.verbose = not player.verbose
                else:
                    console.print(f"[red]Unknown command: {cmd}[/]")
                    console.print("Type !help for available commands.")

                continue

            # Stop if previous playback still running
            if threading.active_count() > running_threads:
                player.stop_playback(False)
                start_time = time.time()
                while threading.active_count() > running_threads and (time.time() - start_time) < TIMEOUT:
                    time.sleep(0.1)
                if threading.active_count() > running_threads:
                    console.print("[red]Warning: Threads still active after timeout, proceeding anyway.[/]")
                    running_threads += 1

            sentences = split_text_to_sentences(user_input, player.nltk_language)
            with console.status(
                f"[cyan]Speaking:[/] {user_input[:30]}...", spinner_style="cyan"
            ):
                player.speak(sentences)

        except KeyboardInterrupt:
            if player.ctrlc:
                player.stop_playback(False)
                console.print("\n[bold yellow]Interrupted. Type !q to exit.[/]")
            else:
                player.print_complete = False
                console.print("\n[bold yellow]Type !p to pause.[/]")
        except EOFError:
            console.print("\n[bold yellow]Type !q to exit.[/]")
        except Exception as e:
            console.print(f"[bold red]Error:[/] {str(e)}")
