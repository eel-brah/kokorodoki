import queue
import sys
import threading
import time
from dataclasses import dataclass
from typing import Optional

import sounddevice as sd
import soundfile as sf
import torch
from kokoro import KPipeline
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from config import MAX_SPEED, MIN_SPEED, REPO_ID, SAMPLE_RATE, console
from utils import get_language_map, get_voices


class TTSPlayer:
    """Class to handle TTS generation and playback."""

    def __init__(self, pipeline: KPipeline, language: str, voice: str, speed: float):
        self.pipeline = pipeline
        self.language = language
        self.voice = voice
        self.speed = speed
        self.languages = get_language_map()
        self.voices = get_voices()
        self.audio_queue = queue.Queue()
        self.stop_event = threading.Event()

    def change_language(self, new_lang: str, device: str) -> bool:
        """Change the language and reinitialize the pipeline."""
        if new_lang in self.languages:
            self.language = new_lang
            self.pipeline = KPipeline(
                lang_code=self.language, repo_id=REPO_ID, device=device
            )
            return True
        return False

    def change_voice(self, new_voice: str) -> bool:
        """Change the voice."""
        if new_voice in self.voices:
            self.voice = new_voice
            return True
        return False

    def change_speed(self, new_speed: float) -> bool:
        """Change the speech speed."""
        if MIN_SPEED <= new_speed <= MAX_SPEED:
            self.speed = new_speed
            return True
        return False

    def generate_audio(self, text: str) -> None:
        """Generate audio chunks and put them in the queue."""
        try:
            generator = self.pipeline(
                text, voice=self.voice, speed=self.speed, split_pattern=None
            )

            for result in generator:
                if self.stop_event.is_set():
                    break

                if result.audio is not None:
                    audio = result.audio.numpy()
                    console.print(f"[dim]Generated: {result.graphemes[:30]}...[/]")
                    self.audio_queue.put(audio)

            self.audio_queue.put(None)  # Signal end of generation
        except Exception as e:
            console.print(f"[bold red]Generation error:[/] {str(e)}")
            self.audio_queue.put(None)  # Ensure playback thread exits

    def generate_audio_file(self, text: str, output_file="Output.wav") -> None:
        """Generate audio file"""
        try:
            with Progress(
                SpinnerColumn("dots", style="yellow", speed=0.8),
                TextColumn("[bold yellow]{task.description}"),
                BarColumn(pulse_style="yellow", complete_style="blue"),
                TimeElapsedColumn(),
            ) as progress:

                task = progress.add_task(
                    f"[bold yellow]Generating {output_file}",
                    total=None,
                )

                generator = self.pipeline(
                    text, voice=self.voice, speed=self.speed, split_pattern=None
                )

                audio_chunks = []
                for result in generator:
                    audio_chunks.append(result.audio)

                # Concatenate all audio chunks
                full_audio = torch.cat(audio_chunks, dim=0)

                # Save the combined audio
                sf.write(output_file, full_audio, SAMPLE_RATE)

                progress.update(
                    task,
                    completed=1,
                    total=1,
                    description=f"[bold green]Saved to {output_file}[/]",
                )

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Exiting...[/]")
            sys.exit()
        except Exception as e:
            console.print(f"[bold red]Generation error:[/] {str(e)}")

    def play_audio(self) -> None:
        """Play audio chunks from the queue."""
        try:
            while not self.stop_event.is_set():
                audio = self.audio_queue.get()

                if audio is None:
                    break

                console.print("[dim]Playing chunk...[/dim]")

                sd.play(audio, samplerate=SAMPLE_RATE)
                while sd.get_stream().active:
                    if self.stop_event.is_set():
                        sd.stop()
                        return
                    time.sleep(0.2)

                self.audio_queue.task_done()
            console.print("[green]Playback complete.[/]\n")
        except Exception as e:
            console.print(f"[dim]Playback thread error: {e}[/dim]")

    def stop_playback(self, printm=True) -> None:
        """Stop ongoing generation and playback."""
        self.stop_event.set()

        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()

        if printm:
            console.print("\n[yellow]Playback stopped.[/]\n")

    def speak(self, text: str, interactive=True) -> None:
        """Start TTS generation and playback in separate threads."""
        self.stop_event.clear()

        # Make sure the queue is empty
        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()

        gen_thread = threading.Thread(
            target=self.generate_audio, args=(text,), daemon=True
        )
        play_thread = threading.Thread(target=self.play_audio, daemon=True)

        try:
            # Start generation thread
            gen_thread.start()

            # Start playback thread
            play_thread.start()

            # Wait for playback to complete
            play_thread.join()
        except KeyboardInterrupt:
            self.stop_playback(False)
            if interactive:
                console.print("\n[bold yellow]Interrupted. Type !q to exit.[/]")
            else:
                console.print("\n[bold yellow]Exiting...[/]")
            gen_thread.join()
            play_thread.join()
            sys.exit()


@dataclass
class Args:
    language: str
    voice: str
    speed: float
    history_off: bool
    device: str
    input_text: Optional[str]
    output_file: Optional[str]
    all_voices: bool
