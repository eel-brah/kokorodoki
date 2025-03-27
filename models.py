import queue
import threading
import time

import sounddevice as sd
from kokoro import KPipeline

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
            self.pipeline = KPipeline(lang_code=self.language, repo_id=REPO_ID, device=device)
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

        # Clear the queue
        while True:
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
            except Exception:
                break
        if printm:
            console.print("\n[yellow]Playback stopped.[/]\n")

    def speak(self, text: str) -> None:
        """Start TTS generation and playback in separate threads."""
        try:
            self.stop_event.clear()

            # Empty the queue if there's anything left
            try:
                while True:
                    self.audio_queue.get_nowait()
                    self.audio_queue.task_done()
            except queue.Empty:
                pass

            # Start generation thread
            gen_thread = threading.Thread(
                target=self.generate_audio, args=(text,), daemon=True
            )
            gen_thread.start()

            # Start playback thread
            play_thread = threading.Thread(target=self.play_audio, daemon=True)
            play_thread.start()

            # Wait for playback to complete
            play_thread.join()
        except KeyboardInterrupt:
            self.stop_playback()
            console.print("\n[bold yellow]Interrupted. Type !q to exit.[/]")
