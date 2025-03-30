import sys
from typing import Optional

from rich.progress import Progress, SpinnerColumn, TextColumn

with Progress(
    SpinnerColumn("dots", style="yellow", speed=0.8),
    TextColumn("[progress.description]{task.description}"),
) as progress:
    progress.add_task("[yellow]Initializing Kokoro...[/]", total=None)
    from kokoro import KPipeline

from config import MAX_SPEED, MIN_SPEED, PROMPT, REPO_ID, console
from input_hander import Args, get_input
from models import  TTSPlayer
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
        with Progress(
            SpinnerColumn("dots", style="yellow", speed=0.8),
            TextColumn("[progress.description]{task.description}"),
        ) as progress:
            progress.add_task("[yellow]Initializing Kokoro pipeline...[/]", total=None)
            # Initialize TTS pipeline
            pipeline = KPipeline(
                lang_code=args.language, repo_id=REPO_ID, device=args.device
            )

        if args.all_voices and args.input_text:
            run_with_all(pipeline, args.language, args.speed, args.input_text)
        elif args.input_text:
            run_noninteractive(
                pipeline,
                args.language,
                args.voice,
                args.speed,
                args.input_text,
                args.output_file,
            )
        else:
            run_interactive(
                pipeline,
                args.language,
                args.voice,
                args.speed,
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


def run_with_all(
    pipeline: KPipeline,
    language: str,
    speed: float,
    input_text: str,
) -> None:
    """Run with all available voices"""
    console.print(
        f"\n[bold blue]Reading with all available {get_language_map()[language]} voices[/]\n"
    )
    target_voices = [voice for voice in get_voices() if voice.startswith(language)]

    player = TTSPlayer(pipeline, language, target_voices[0], speed)
    try:
        for voice in target_voices:
            player.change_voice(voice)
            console.print(f"[cyan]{voice} speaking:[/] {input_text}")
            player.speak(input_text, interactive=False)
    except KeyboardInterrupt:
        console.print("[bold yellow]Exiting...[/]")
        sys.exit()


def run_noninteractive(
    pipeline: KPipeline,
    language: str,
    voice: str,
    speed: float,
    input_text: str,
    output_file: Optional[str],
) -> None:
    """Generate audio"""
    player = TTSPlayer(pipeline, language, voice, speed)
    if output_file is None:
        console.print(f"[cyan]Speaking:[/] {input_text}")
        try:
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
    history_off: bool,
    device: str,
    prompt="> ",
) -> None:
    """Run an interactive TTS session with dynamic settings."""

    player = TTSPlayer(pipeline, language, voice, speed)

    console.print("[bold green]Interactive TTS started.[/]")
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

                elif cmd == "!hclear":
                    clear_history()

                else:
                    console.print(f"[red]Unknown command: {cmd}[/]")
                    console.print("Type !help for available commands.")

                continue

            console.print(f"[cyan]Speaking:[/] {user_input}")
            player.speak(user_input)

        except KeyboardInterrupt:
            player.stop_playback(False)
            console.print("\n[bold yellow]Interrupted. Type !q to exit.[/]")
        except EOFError:
            console.print("\n[bold yellow]Type !q to exit.[/]")
        except Exception as e:
            console.print(f"[bold red]Error:[/] {str(e)}")
