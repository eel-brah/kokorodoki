import queue
import sys
import threading
import time
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

    def __init__(
        self,
        pipeline: KPipeline,
        language: str,
        voice: str,
        speed: float,
        verbose: bool,
        ctrlc: bool = True,
    ):
        self.pipeline = pipeline
        self.language = language
        self.voice = voice
        self.speed = speed
        self.verbose = verbose
        self.languages = get_language_map()
        self.voices = get_voices()
        self.audio_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.audio_player = AudioPlayer(SAMPLE_RATE)
        self.ctrlc = not ctrlc
        self.print_complete = True

    def change_language(self, new_lang: str, device: Optional[str]) -> bool:
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
                    if self.verbose:
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
            self.print_complete = True
            while not self.stop_event.is_set():
                audio = self.audio_queue.get()

                if audio is None:
                    break

                if self.verbose:
                    console.print("[dim]Playing chunk...[/dim]")

                self.audio_player.play(audio)
                if self.audio_player.stream is not None:
                    while self.audio_player.stream.active:
                        if self.stop_event.is_set():
                            self.audio_player.stop()
                            return
                        time.sleep(0.2)
                self.audio_queue.task_done()
            if self.print_complete is True:
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

    def pause_playback(self) -> None:
        """Pause playback."""
        self.audio_player.pause()

    def resume_playback(self) -> None:
        """Resume playback."""
        self.audio_player.resume()

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
            if interactive and self.ctrlc:
                self.stop_playback(False)
                console.print("\n[bold yellow]Interrupted. Type !q to exit.[/]")
            elif interactive:
                # self.stop_playback(False)
                self.print_complete = False
                console.print("\n[bold yellow]Type !p to pause.[/]")
            else:
                console.print("\n[bold yellow]Exiting...[/]")
            gen_thread.join()
            play_thread.join()
            if not interactive:
                sys.exit()


class AudioPlayer:
    def __init__(self, samplerate=SAMPLE_RATE):
        self.samplerate = samplerate
        self.current_frame = 0
        self.playing = True
        self.event = threading.Event()
        self.lock = threading.Lock()
        self.stream = None

    def _callback(self, outdata, frames, time, status):
        with self.lock:
            if not self.playing:
                outdata.fill(0)
                return

            chunksize = min(len(self.audio_data) - self.current_frame, frames)

            if len(self.audio_data.shape) == 1:
                for channel in range(outdata.shape[1]):
                    outdata[:chunksize, channel] = self.audio_data[
                        self.current_frame : self.current_frame + chunksize
                    ]
            else:
                channels = min(self.audio_data.shape[1], outdata.shape[1])
                outdata[:chunksize, :channels] = self.audio_data[
                    self.current_frame : self.current_frame + chunksize, :channels
                ]
            if chunksize < frames:
                outdata[chunksize:] = 0
                raise sd.CallbackStop()
            self.current_frame += chunksize

    def play(self, audio, blocking = False) -> None:
        """Start playback"""
        if self.stream is not None:
            self.stop()
        self.audio_data = audio

        def finished_callback():
            self.event.set()

        self.stream = sd.OutputStream(
            samplerate=self.samplerate,
            channels=1 if len(self.audio_data.shape) == 1 else self.audio_data.shape[1],
            callback=self._callback,
            finished_callback=finished_callback,
        )
        self.stream.start()
        if blocking:
            self.event.wait()
            self.stop()

    def resume(self) -> None:
        """Resume playback"""
        with self.lock:
            if self.stream is not None:
                self.playing = True

    def pause(self) -> None:
        """Pause playback"""
        with self.lock:
            if self.stream is not None:
                self.playing = False

    def stop(self) -> None:
        """stop playback"""
        with self.lock:
            self.playing = False
            self.current_frame = 0
        if self.stream is not None:
            self.stream.stop(True)
            self.stream.close(True)
            self.stream = None
            self.playing = True
            self.event.clear()
