import queue
import sys
import threading
import time
from typing import Optional

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
from utils import get_language_map, get_nltk_language, get_voices, parse_srt_file, split_text_to_sentences


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
        self.audio_player = None
        self.ctrlc = not ctrlc
        self.print_complete = True

    def change_language(self, new_lang: str, device: Optional[str]) -> bool:
        """Change the language and reinitialize the pipeline."""
        if new_lang in self.languages:
            self.language = new_lang
            self.pipeline = KPipeline(
                lang_code=self.language, repo_id=REPO_ID, device=device
            )
            if not self.voice.startswith(new_lang):
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

    def generate_audio(self, text: str | list) -> None:
        """Generate audio chunks and put them in the queue."""
        try:
            sentences = [text] if isinstance(text, str) else text
            for sentence in sentences:
                generator = self.pipeline(
                    sentence, voice=self.voice, speed=self.speed, split_pattern=None
                )

                for result in generator:
                    if self.stop_event.is_set():
                        self.audio_queue.put(None)
                        return

                    if result.audio is not None:
                        audio = result.audio.numpy()
                        if self.verbose:
                            console.print(
                                f"[dim]Generated: {result.graphemes[:30]}...[/]"
                            )
                        # Trim silence for smooth reading
                        trimed_audio, _ = librosa.effects.trim(audio, top_db=60)
                        # trimed_audio = self.trim_silence(audio, threshold=0.001)
                        self.audio_queue.put(trimed_audio)

            self.audio_queue.put(None)  # Signal end of generation
        except Exception as e:
            console.print(f"[bold red]Generation error:[/] {str(e)}")
            self.audio_queue.put(None)  # Ensure playback thread exits

    def generate_audio_file(self, text: list | str, output_file="Output.wav") -> None:
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

                sentences = [text] if isinstance(text, str) else text
                audio_chunks = []
                for sentence in sentences:
                    generator = self.pipeline(
                        sentence, voice=self.voice, speed=self.speed, split_pattern=None
                    )

                    for result in generator:
                        trimed_audio, _ = librosa.effects.trim(
                            result.audio.numpy(), top_db=70
                        )
                        audio_chunks.append(self.to_stereo(trimed_audio))

                full_audio = np.concatenate(audio_chunks, axis=0)
                sf.write(output_file, full_audio, SAMPLE_RATE, format="WAV")

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

    def generate_srt_timed_audio(self, srt_file: str, output_file="Output.wav") -> None:
        """Generate timed audio based on SRT subtitle file"""
        try:
            # Parse SRT file
            srt_entries = parse_srt_file(srt_file)
            if not srt_entries:
                console.print("[bold red]Error:[/] No valid entries found in SRT file")
                return

            with Progress(
                SpinnerColumn("dots", style="yellow", speed=0.8),
                TextColumn("[bold yellow]{task.description}"),
                BarColumn(pulse_style="yellow", complete_style="blue"),
                TimeElapsedColumn(),
            ) as progress:

                task = progress.add_task(
                    f"[bold yellow]Generating timed audio from SRT",
                    total=len(srt_entries),
                )

                # Calculate total duration needed
                total_duration = max(entry.end_time for entry in srt_entries)
                total_samples = int(total_duration * SAMPLE_RATE)
                
                # Initialize stereo audio array with silence
                full_audio = np.zeros((total_samples, 2))

                for i, entry in enumerate(srt_entries):
                    # Split text into sentences for better processing
                    sentences = split_text_to_sentences(entry.text, self.nltk_language)
                    
                    # Generate audio for this entry
                    entry_audio_chunks = []
                    for sentence in sentences:
                        generator = self.pipeline(
                            sentence, voice=self.voice, speed=self.speed, split_pattern=None
                        )

                        for result in generator:
                            if result.audio is not None:
                                trimmed_audio, _ = librosa.effects.trim(
                                    result.audio.numpy(), top_db=70
                                )
                                entry_audio_chunks.append(self.to_stereo(trimmed_audio))

                    if entry_audio_chunks:
                        # Concatenate all audio for this entry
                        entry_audio = np.concatenate(entry_audio_chunks, axis=0)
                        
                        # Calculate timing
                        start_sample = int(entry.start_time * SAMPLE_RATE)
                        entry_duration = entry.end_time - entry.start_time
                        target_samples = int(entry_duration * SAMPLE_RATE)
                        
                        # Ensure we don't exceed the target duration
                        if len(entry_audio) > target_samples:
                            # If audio is too long, truncate it
                            entry_audio = entry_audio[:target_samples]
                        
                        # Calculate end sample
                        end_sample = start_sample + len(entry_audio)
                        
                        # Make sure we don't exceed the total audio length
                        if end_sample > len(full_audio):
                            end_sample = len(full_audio)
                            entry_audio = entry_audio[:end_sample - start_sample]
                        
                        # Place audio at the correct timing
                        if start_sample < len(full_audio):
                            full_audio[start_sample:end_sample] = entry_audio

                    progress.update(task, advance=1)

                # Save the final audio
                sf.write(output_file, full_audio, SAMPLE_RATE, format="WAV")

                progress.update(
                    task,
                    completed=len(srt_entries),
                    description=f"[bold green]Saved timed audio to {output_file}[/]",
                )

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Exiting...[/]")
            sys.exit()
        except Exception as e:
            console.print(f"[bold red]SRT generation error:[/] {str(e)}")

    def to_stereo(self, chunk):
        """Convert mono chunk to stereo"""
        if chunk.ndim == 1:
            return np.stack([chunk, chunk], axis=1)
        if chunk.ndim == 2 and chunk.shape[1] == 2:
            return chunk
        raise ValueError(
            f"Unsupported chunk shape: {chunk.shape}. Expected 1D (mono) or 2D (stereo)."
        )

    def play_audio(self, gui_highlight=None) -> None:
        """Play audio chunks from the queue."""
        try:
            if self.audio_player is None:
                self.audio_player = AudioPlayer(SAMPLE_RATE)
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
                while self.audio_player.is_playing:
                    if self.stop_event.is_set():
                        self.audio_player.stop()
                        return
                    elif self.skip.is_set():
                        self.audio_player.stop()
                        break
                    elif self.back.is_set():
                        self.audio_player.stop()
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

    def speak(self, text: str | list, console_mode=True, gui_highlight=None) -> None:
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
            gen_thread.join()
        except KeyboardInterrupt:
            if console_mode and self.ctrlc:
                self.stop_playback(False)
                console.print("\n[bold yellow]Interrupted. Type !q to exit.[/]")
                gen_thread.join()
                play_thread.join()
            elif console_mode:
                # self.stop_playback(False)
                self.print_complete = False
                console.print("\n[bold yellow]Type !p to pause.[/]")
            else:
                console.print("\n[bold yellow]Exiting...[/]")
                self.stop_playback(False)
                gen_thread.join()
                play_thread.join()
                sys.exit()


class AudioPlayer:
    def __init__(self, samplerate):
        self.samplerate = samplerate
        self.current_frame = 0
        self.playing = True
        self.event = threading.Event()
        self.lock = threading.Lock()
        self.current_audio = None
        self.stream = sd.OutputStream(
            samplerate=self.samplerate,
            channels=2,
            callback=self._callback,
            finished_callback=self._finished_callback,
        )
        self.stream.start()

    def _callback(self, outdata, frames, time, status):
        with self.lock:
            if not self.playing or self.current_audio is None:
                outdata.fill(0)
                return

            chunksize = min(len(self.current_audio) - self.current_frame, frames)

            if len(self.current_audio.shape) == 1:
                # Mono audio: copy to all output channels
                for channel in range(outdata.shape[1]):
                    outdata[:chunksize, channel] = self.current_audio[
                        self.current_frame : self.current_frame + chunksize
                    ]
            else:
                # Stereo or multi-channel: copy up to available channels
                channels = min(self.current_audio.shape[1], outdata.shape[1])
                outdata[:chunksize, :channels] = self.current_audio[
                    self.current_frame : self.current_frame + chunksize, :channels
                ]

            if chunksize < frames:
                outdata[chunksize:] = 0
                self.current_audio = None
                self.event.set()

            self.current_frame += chunksize

    def _finished_callback(self):
        """Called when stream is stopped"""
        self.event.set()

    def play(self, audio, blocking=False) -> None:
        """Start playback of a single audio clip"""
        with self.lock:
            self.current_audio = audio
            self.current_frame = 0
            self.playing = True

        if blocking:
            self.event.clear()
            self.event.wait()

    def resume(self) -> None:
        """Resume playback"""
        with self.lock:
            self.playing = True

    def pause(self) -> None:
        """Pause playback"""
        with self.lock:
            self.playing = False

    def stop(self) -> None:
        """Stop playback and clear current audio"""
        with self.lock:
            self.playing = False
            self.current_frame = 0
            self.current_audio = None
            self.event.set()

    @property
    def is_playing(self) -> bool:
        """Check if audio is actively playing"""
        with self.lock:
            return self.current_audio is not None

    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, "stream"):
            self.stream.stop()
            self.stream.close()
