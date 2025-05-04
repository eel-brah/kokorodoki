import queue
import sys
import threading
import time
from typing import Optional, Union

import librosa
import numpy as np
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
from utils import get_language_map, get_nltk_language, get_voices


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
        self.nltk_language = get_nltk_language(self.language)
        self.voice = voice
        self.speed = speed
        self.verbose = verbose
        self.languages = get_language_map()
        self.voices = get_voices()
        self.audio_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.skip = threading.Event()
        self.back = threading.Event()
        self.lock = threading.Lock()
        self.back_number = 0
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
            self.change_voice(
                next(voice for voice in get_voices() if voice.startswith(new_lang))
            )
            self.nltk_language = get_nltk_language(self.language)
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

    def trim_silence(self, audio, threshold=0.003):
        """Trim silence from the beginning and end of an audio chunk."""
        # Convert to absolute values to handle negative amplitudes
        abs_audio = np.abs(audio)
        # Find indices where amplitude exceeds threshold
        non_silent = np.where(abs_audio > threshold)[0]

        if len(non_silent) == 0:
            return audio

        # Trim the audio
        start_idx = non_silent[0]
        end_idx = non_silent[-1] + 1
        return audio[start_idx:end_idx]

    def generate_audio(self, text: Union[str, list]) -> None:
        """Generate audio chunks and put them in the queue."""
        try:
            sentences = [text] if isinstance(text, str) else text
            for sentence in sentences:
                generator = self.pipeline(
                    sentence, voice=self.voice, speed=self.speed, split_pattern=None
                )

                for result in generator:
                    if self.stop_event.is_set():
                        break

                    if result.audio is not None:
                        audio = result.audio.numpy()
                        if self.verbose:
                            console.print(
                                f"[dim]Generated: {result.graphemes[:30]}...[/]"
                            )
                        # Trim silence for smooth reading
                        trimed_audio, _ = librosa.effects.trim(audio, top_db=50)
                        # trimed_audio = self.trim_silence(audio, threshold=0.001)
                        self.audio_queue.put(trimed_audio)

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

    def play_audio(self, gui_highlight=None) -> None:
        """Play audio chunks from the queue."""
        try:
            audio_chunks = []
            audio_size = 0
            self.back_number = 0
            self.print_complete = True
            while not self.stop_event.is_set():
                self.skip.clear()
                self.back.clear()
                with self.lock:
                    back_number = self.back_number = min(self.back_number, audio_size)
                if back_number > 0 and audio_size > 0:
                    audio = audio_chunks[audio_size - back_number]
                else:
                    audio = self.audio_queue.get()
                    if audio is None:
                        break

                    audio_chunks.append(audio)
                    audio_size += 1

                if self.verbose:
                    console.print("[dim]Playing chunk...[/dim]")

                self.audio_player.play(audio)
                if gui_highlight is not None:
                    gui_highlight.queue.put(
                        (gui_highlight.highlight, (audio_size - (back_number or 1),))
                    )
                if self.audio_player.stream is not None:
                    while self.audio_player.stream.active:
                        if self.stop_event.is_set():
                            self.audio_player.stop()
                            return
                        elif self.skip.is_set():
                            break
                        elif self.back.is_set():
                            break
                        time.sleep(0.2)

                with self.lock:
                    if not self.back.is_set() and self.back_number > 0:
                        self.back_number -= 1
                    if self.back_number == 0:
                        self.audio_queue.task_done()
            if gui_highlight is not None:
                gui_highlight.queue.put(gui_highlight.remove_highlight)
            self.audio_player.stop()
            if self.print_complete is True:
                console.print("[green]Playback complete.[/]\n")
        except Exception as e:
            console.print(f"[dim]Playback thread error: {e}[/dim]")

    def skip_sentence(self) -> None:
        self.skip.set()

    def back_sentence(self) -> None:
        self.back_number += 1
        self.back.set()

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

    def speak(
        self, text: Union[str, list], console_mode=True, gui_highlight=None
    ) -> None:
        """Start TTS generation and playback in separate threads."""

        self.stop_event.clear()

        # Make sure the queue is empty
        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()

        gen_thread = threading.Thread(
            target=self.generate_audio, args=(text,), daemon=True
        )
        play_thread = threading.Thread(
            target=self.play_audio, args=(gui_highlight,), daemon=True
        )

        try:
            # Start generation thread
            gen_thread.start()

            # Start playback thread
            play_thread.start()

            # Wait for playback to complete
            play_thread.join()
        except KeyboardInterrupt:
            if console_mode and self.ctrlc:
                self.stop_playback(False)
                console.print("\n[bold yellow]Interrupted. Type !q to exit.[/]")
            elif console_mode:
                # self.stop_playback(False)
                self.print_complete = False
                console.print("\n[bold yellow]Type !p to pause.[/]")
            else:
                console.print("\n[bold yellow]Exiting...[/]")
            gen_thread.join()
            play_thread.join()
            if not console_mode:
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

    def play(self, audio, blocking=False) -> None:
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
