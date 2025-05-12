import os
import queue
import signal
import threading
import tkinter as tk
from tkinter import messagebox
from typing import Dict, Optional

import easyocr
import ttkbootstrap as ttk
from kokoro import KPipeline
from ttkbootstrap.tooltip import ToolTip

from config import MAX_SPEED, MIN_SPEED, TITLE, VERSION, WINDOW_SIZE
from models import TTSPlayer
from utils import (
    get_easyocr_language_map,
    get_gui_themes,
    get_language_map,
    get_nltk_language,
    get_nltk_language_map,
    get_voices,
    split_text_to_sentences,
)


class Gui:
    def __init__(
        self,
        root: ttk.Window,
        pipeline: KPipeline,
        language: str,
        voice: str,
        speed: float,
        device: Optional[str],
        image_reader: easyocr.Reader,
        dark_theme: bool,
    ):
        self.root = root
        self.dark_theme = dark_theme
        self.languages = [lang for _, lang in get_language_map().items()]
        self.voices = get_voices()
        self.current_language_code = language
        self.current_language = get_language_map()[language]
        self.current_voice = voice
        self.speed = speed
        self.device = device
        self.pipeline = pipeline
        self.player = TTSPlayer(
            self.pipeline, self.current_language, self.current_voice, self.speed, False
        )
        self.current_thread = None
        self.speech_paused = False
        self.prev_text = ""
        self.prev_sentences = []
        self.nltk_language = get_nltk_language(self.current_language_code)
        self.sentence_indices = []

        self.reader = image_reader

        self.queue = queue.Queue()
        self.root.after(100, self.process_queue)

        self.default_font = "Segoe UI"
        self.is_speaking = False

        self._color_cache = {}

        self.create_widgets()

        self.default_bg = self.text_area.cget("background")
        self.default_fg = self.text_area.cget("foreground")
        self.default_cursor = self.text_area.cget("cursor")
        self.text_area.tag_config(
            "highlight", background="#3a86ff", foreground="#ffffff"
        )

    def process_queue(self) -> None:
        try:
            while True:
                item = self.queue.get_nowait()
                if isinstance(item, tuple):
                    func, args = item
                    func(*args)
                else:
                    func = item
                    func()
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    def change_speed(self, event) -> None:
        """Change speed"""
        speed = self.speed_scale.get()
        self.speed = speed
        self.player.change_speed(speed)
        self.speed_label.config(text=f"{speed:.1f}x")
        self.status_label.config(text=f"Speed set to: {self.speed:.2f}x")

    def change_voice(self, *args) -> None:
        """Change voice"""
        self.current_voice = self.voice_var.get()
        self.player.change_voice(self.current_voice)
        self.status_label.config(text=f"Voice set to: {self.current_voice}")

    def change_lang(self, event, voice_menu: ttk.Combobox) -> None:
        """Change language and update voice menu"""
        self.current_language = self.lang_var.get()
        self.current_language_code = next(
            code
            for code, lang in get_language_map().items()
            if lang == self.current_language
        )
        self.player.change_language(self.current_language_code, self.device)
        self.status_label.config(text=f"Language set to: {self.current_language}")

        easyocr_lang = [
            lang
            for code, lang in get_easyocr_language_map().items()
            if code == self.current_language_code
        ]
        self.reader = easyocr.Reader(easyocr_lang)

        self.nltk_language = get_nltk_language(self.current_language_code)

        # Update voice menu
        if not self.current_voice.startswith(self.current_language_code):
            voice_menu["values"] = [
                voice
                for voice in self.voices
                if voice.startswith(self.current_language_code)
            ]
            self.voice_var.set(voice_menu["values"][0])
            self.current_voice = self.voice_var.get()

    def play_speech(self) -> None:
        """Play or resume if it was paused"""
        text = self.text_area.get("1.0", tk.END).strip()

        if self.prev_text == text and self.speech_paused is True:
            self.speech_paused = False
            self.resume_speech()
        else:
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert("1.0", text)
            self.prev_text = text
            self.prev_sentences = split_text_to_sentences(text, self.nltk_language)
            if self.current_thread is not None and self.current_thread.is_alive():
                self.player.stop_playback()
                self.current_thread.join()
            self.current_thread = threading.Thread(
                target=self.speak_thread, args=(self.prev_sentences,), daemon=True
            )
            self.current_thread.start()
            self.calculate_sentence_indices()
            self.status_label.config(text="Playback: started")

    def speak_thread(self, text: str) -> None:
        """Player speak wrapper"""
        try:
            self.queue.put(
                lambda: self.text_area.config(
                    state="disabled",
                    background=self.darken_color(self.default_bg),
                    foreground=self.darken_color(self.default_fg),
                    cursor="arrow",
                )
            )
            self.player.speak(text, console_mode=False, gui_highlight=self)
            self.queue.put(
                lambda: self.text_area.config(
                    state="normal",
                    background=self.default_bg,
                    foreground=self.default_fg,
                    cursor=self.default_cursor,
                )
            )
        except Exception as e:
            print(f"Error in thread: {str(e)}")

    def pause_speech(self) -> None:
        """Pause speech"""
        self.speech_paused = True
        self.text_area.config(
            state="normal",
            background=self.default_bg,
            foreground=self.default_fg,
            cursor=self.default_cursor,
        )
        self.player.pause_playback()
        self.status_label.config(text="Playback: paused")

    def resume_speech(self) -> None:
        """Resume speech"""
        self.text_area.config(
            state="disabled",
            background=self.darken_color(self.default_bg),
            foreground=self.darken_color(self.default_fg),
            cursor="arrow",
        )
        self.player.resume_playback()
        self.status_label.config(text="Playback: resumed")

    def darken_color(self, color, factor=0.8) -> str:
        """Darken a color by a given factor"""
        cache_key = (color, factor)
        if cache_key in self._color_cache:
            return self._color_cache[cache_key]
        rgb = self.root.winfo_rgb(color)
        darkened = tuple(int(c * factor / 65535 * 255) for c in rgb[:3])
        result = f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
        self._color_cache[cache_key] = result
        return result

    def calculate_sentence_indices(self) -> None:
        """Calculate start and end indices for each sentence."""
        self.sentence_indices.clear()
        current_pos = 0
        text_content = self.prev_text

        for sentence in self.prev_sentences:
            start_pos = text_content.find(sentence, current_pos)
            if start_pos == -1:
                continue

            # Calculate line and column for start index
            text_before = text_content[:start_pos]
            start_line = text_before.count("\n") + 1
            start_char = (
                start_pos - text_before.rfind("\n") - 1
                if text_before.rfind("\n") != -1
                else start_pos
            )

            # Calculate end position
            end_pos = start_pos + len(sentence)
            text_before_end = text_content[:end_pos]
            end_line = text_before_end.count("\n") + 1
            end_char = (
                end_pos - text_before_end.rfind("\n") - 1
                if text_before_end.rfind("\n") != -1
                else end_pos
            )

            self.sentence_indices.append(
                {"start": f"{start_line}.{start_char}", "end": f"{end_line}.{end_char}"}
            )
            current_pos = end_pos

    def remove_highlight(self) -> None:
        """Remove highlight"""
        self.text_area.tag_remove("highlight", "1.0", tk.END)

    def highlight(self, sentence: int) -> None:
        """Highlight a sentence"""
        if not self.sentence_indices:
            return

        self.text_area.tag_remove("highlight", "1.0", tk.END)
        indices = self.sentence_indices[sentence % len(self.prev_sentences)]
        self.text_area.tag_add("highlight", indices["start"], indices["end"])
        self.text_area.see(indices["start"])

    def skip_sentence(self) -> None:
        """Skip a sentence"""
        self.player.skip_sentence()
        self.status_label.config(text="Playback: to the next sentence")

    def back_sentence(self) -> None:
        """Back a sentence"""
        self.player.back_sentence()
        self.status_label.config(text="Playback: back one sentence")

    def create_widgets(self) -> None:
        """Create widgets"""
        # Main frame
        container = ttk.Frame(self.root, padding=15)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        self.add_title(container)
        self.add_text_area(container)
        self.add_control_panel(container)
        self.add_status_bar(container)

    def add_title(self, container):
        """Add Title and subtitle"""
        title_frame = ttk.Frame(container)
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        title_frame.columnconfigure(2, weight=1)

        style = "light" if self.dark_theme else "dark"
        title_label = ttk.Label(
            title_frame,
            text="KokoroDoki",
            font=(self.default_font, 18, "bold"),
            bootstyle=style,
        )
        title_label.grid(row=0, column=0, sticky="w")

        style = "secondary" if self.dark_theme else "default"
        subtitle_label = ttk.Label(
            title_frame,
            text="Text-to-Speech Reader",
            font=(self.default_font, 10),
            bootstyle="secondary",
        )
        subtitle_label.grid(row=0, column=1, sticky="w", padx=10, pady=5)

    def add_status_bar(self, container):
        """Create status bar"""
        status_frame = ttk.Frame(container)
        status_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        status_frame.columnconfigure(1, weight=1)

        self.status_label = ttk.Label(
            status_frame,
            text="Ready",
            font=(self.default_font, 9),
            bootstyle="info",
        )
        self.status_label.grid(row=0, column=0, sticky="w")

        version_label = ttk.Label(
            status_frame,
            text=VERSION,
            font=(self.default_font, 9),
            bootstyle="secondary",
        )
        version_label.grid(row=0, column=2, sticky="e")

    def choose_file(self):
        try:
            file_path = tk.filedialog.askopenfilename(
                title="Select a Text file of an image",
                filetypes=[("All files", "*.*"), ("Text files", "*.txt")],
            )
            if file_path:
                self.file_path_var.set(f"File: {file_path}")
                try:
                    image_extensions = [
                        ".png",
                        ".jpg",
                        ".jpeg",
                        ".webp",
                        ".bmp",
                        ".tiff",
                        ".tif",
                    ]
                    _, file_ext = os.path.splitext(file_path.lower())

                    if file_ext in image_extensions:
                        self.text_area.delete(1.0, tk.END)
                        results = self.reader.readtext(file_path)
                        image_text = ""
                        image_text = " ".join(
                            text for _, text, _ in results if text
                        ).strip()

                        self.text_area.insert(
                            tk.END,
                            image_text,
                        )
                    else:
                        with open(file_path, "r", encoding="utf-8") as file:
                            self.text_area.delete(1.0, tk.END)
                            self.text_area.insert(tk.END, file.read())
                except Exception as e:
                    self.text_area.delete(1.0, tk.END)
                    self.text_area.insert(tk.END, f"Error reading file: {str(e)}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def add_text_area(self, container):
        """Create text area"""
        text_frame = ttk.LabelFrame(container, text="Text Content", padding=10)
        text_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        # Text area
        self.text_area = tk.Text(
            text_frame,
            height=15,
            wrap="word",
            font=(self.default_font, 12),
            borderwidth=0,
        )
        self.text_area.grid(row=0, column=0, sticky="nsew")

        # Scrollbar
        text_scroll = ttk.Scrollbar(text_frame, command=self.text_area.yview)
        text_scroll.grid(row=0, column=1, sticky="ns")
        self.text_area.configure(yscrollcommand=text_scroll.set)

        # File selector
        button_frame = ttk.Frame(text_frame)
        button_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        button_frame.columnconfigure(1, weight=1)

        choose_button = ttk.Button(
            button_frame, text="Choose File", command=self.choose_file
        )
        choose_button.grid(row=0, column=0, sticky="w", padx=(0, 10))

        # Create a StringVar to hold the file path
        self.file_path_var = tk.StringVar()
        self.file_path_var.set("No file or image selected")

        # Entry to display the file path
        file_path_display = ttk.Entry(
            button_frame,
            textvariable=self.file_path_var,
            state="readonly",
        )
        file_path_display.grid(row=0, column=1, sticky="ew")

        # Add placeholder text
        self.add_place_holder()

    def add_place_holder(self):
        """Add placeholder text"""
        placeholder = "Type or select a file..."
        self.text_area.insert("1.0", placeholder)
        self.text_area.tag_add("placeholder", "1.0", "end")
        self.text_area.tag_config("placeholder", foreground="gray")

        def clear_placeholder(event):
            if self.text_area.tag_ranges("placeholder"):
                self.text_area.delete("1.0", "end")
                self.text_area.tag_remove("placeholder", "1.0", "end")

        def restore_placeholder(event):
            if not self.text_area.get("1.0", "end-1c"):
                self.text_area.insert("1.0", placeholder)
                self.text_area.tag_add("placeholder", "1.0", "end")
                self.text_area.tag_config("placeholder", foreground="gray")

        self.text_area.bind("<KeyPress>", clear_placeholder)
        self.text_area.bind("<KeyRelease>", restore_placeholder)
        # self.text_area.bind("<FocusIn>", lambda e: clear_placeholder(e) if self.text_area.get("1.0", "end-1c") == placeholder else None)

    def add_control_panel(self, container):
        """Create control panel"""
        control_panel = ttk.LabelFrame(container, text="Control Panel", padding=10)
        control_panel.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        control_panel.columnconfigure(0, weight=1)

        # Playback controls section
        playback_frame = ttk.Frame(control_panel)
        playback_frame.grid(row=0, column=0, sticky="ew", pady=5)
        playback_frame.columnconfigure(0, weight=1)

        # Buttons frame
        buttons_frame = ttk.Frame(playback_frame)
        buttons_frame.grid(row=0, column=0, pady=10)
        buttons_frame.columnconfigure((0, 1, 2, 3), weight=1)

        prev_btn = ttk.Button(
            buttons_frame,
            text="⏮",
            command=self.back_sentence,
            bootstyle="info-outline",
            width=8,
        )
        prev_btn.grid(row=0, column=0, padx=5)
        ToolTip(prev_btn, text="Prev", bootstyle="info")

        play_btn = ttk.Button(
            buttons_frame,
            text="▶",
            command=self.play_speech,
            bootstyle="success-outline",
            width=8,
        )
        play_btn.grid(row=0, column=1, padx=5)
        ToolTip(play_btn, text="Play/Resume", bootstyle="success")

        stop_btn = ttk.Button(
            buttons_frame,
            text="⏹",
            command=self.pause_speech,
            bootstyle="danger-outline",
            width=8,
        )
        stop_btn.grid(row=0, column=2, padx=5)
        ToolTip(stop_btn, text="Pause", bootstyle="danger")

        next_btn = ttk.Button(
            buttons_frame,
            text="⏭",
            command=self.skip_sentence,
            bootstyle="info-outline",
            width=8,
        )
        next_btn.grid(row=0, column=3, padx=5)
        ToolTip(next_btn, text="Next", bootstyle="info")

        # Settings section
        settings_frame = ttk.Frame(control_panel)
        settings_frame.grid(row=1, column=0, sticky="ew", pady=10)
        settings_frame.columnconfigure((0, 1, 2), weight=1)

        # Language dropdown
        lang_frame = ttk.Frame(settings_frame)
        lang_frame.grid(row=0, column=0, sticky="ew", padx=5)
        lang_frame.columnconfigure(1, weight=1)

        lang_label = ttk.Label(
            lang_frame, text="Language:", font=(self.default_font, 12)
        )
        lang_label.grid(row=0, column=0, sticky="w", padx=(0, 5))

        self.lang_var = tk.StringVar(value=self.current_language)
        lang_menu = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_var,
            values=self.languages,
            state="readonly",
            width=12,
            style="primary",
        )
        lang_menu.grid(row=0, column=1, sticky="ew")
        # lang_menu.bind("<<ComboboxSelected>>", self.change_lang)
        lang_menu.bind(
            "<<ComboboxSelected>>", lambda event: self.change_lang(event, voice_menu)
        )

        # Voice dropdown
        voice_frame = ttk.Frame(settings_frame)
        voice_frame.grid(row=0, column=1, sticky="ew", padx=5)
        voice_frame.columnconfigure(1, weight=1)

        voice_label = ttk.Label(
            voice_frame, text="Voice:", font=(self.default_font, 12)
        )
        voice_label.grid(row=0, column=0, sticky="w", padx=(0, 5))

        self.voice_var = tk.StringVar(value=self.current_voice)
        voice_menu = ttk.Combobox(
            voice_frame,
            textvariable=self.voice_var,
            values=[
                voice
                for voice in self.voices
                if voice.startswith(self.current_language_code)
            ],
            state="readonly",
            width=12,
            style="primary",
        )
        voice_menu.grid(row=0, column=1, sticky="ew")
        voice_menu.bind("<<ComboboxSelected>>", self.change_voice)

        # Speed control
        speed_frame = ttk.Frame(settings_frame)
        speed_frame.grid(row=0, column=2, sticky="ew", padx=5)
        speed_frame.columnconfigure(1, weight=1)

        speed_label = ttk.Label(
            speed_frame, text="Speed:", font=(self.default_font, 12)
        )
        speed_label.grid(row=0, column=0, sticky="w", padx=(0, 5))

        speed_container = ttk.Frame(speed_frame)
        speed_container.grid(row=0, column=1, sticky="ew")
        speed_container.columnconfigure(0, weight=1)

        self.speed_scale = ttk.Scale(
            speed_container,
            from_=0.5,
            to=2.0,
            value=self.speed,
            bootstyle="info",
            command=self.change_speed,
        )
        self.speed_scale.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        speed_labels = ttk.Frame(speed_container)
        speed_labels.grid(row=1, column=0, sticky="ew")
        speed_labels.columnconfigure(1, weight=1)

        min_label = ttk.Label(
            speed_labels,
            text=f"{MIN_SPEED:.1f}x",
            font=(self.default_font, 8),
            bootstyle="secondary",
        )
        min_label.grid(row=0, column=0, sticky="w")

        self.speed_label = ttk.Label(
            speed_labels,
            text=f"{self.speed:.1f}x",
            font=(self.default_font, 9, "bold"),
            bootstyle="primary",
        )
        self.speed_label.grid(row=0, column=1)

        max_label = ttk.Label(
            speed_labels,
            text=f"{MAX_SPEED:.1f}x",
            font=(self.default_font, 8),
            bootstyle="secondary",
        )
        max_label.grid(row=0, column=2, sticky="e")

    def close(self):
        if self.current_thread is not None and self.current_thread.is_alive():
            self.player.stop_playback()
            self.current_thread.join()


def setup_signal_handler(root, app):
    """Set up a signal handler for SIGINT (Ctrl+C) to close the Tkinter window."""

    def signal_handler(sig, frame):
        print("\nClosing...")
        app.close()
        root.after(0, root.destroy)

    signal.signal(signal.SIGINT, signal_handler)


def run_gui(
    pipeline: KPipeline,
    language: str,
    voice: str,
    speed: float,
    device: Optional[str],
    theme: int,
    image_reader: easyocr.Reader,
) -> None:
    """Start gui mode"""
    try:
        root = ttk.Window(themename=get_gui_themes()[theme])
        root.title(TITLE)
        root.geometry(WINDOW_SIZE)
        root.resizable(True, True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # Check if it is a Dark or Light theme
        dark_theme = 1 <= theme <= 4
        app = Gui(
            root, pipeline, language, voice, speed, device, image_reader, dark_theme
        )

        def on_closing():
            if messagebox.askokcancel("Quit", "Do you want to quit?"):
                print("Exiting...")
                app.close()
                root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        setup_signal_handler(root, app)

        root.mainloop()

    except Exception as e:
        print(f"An error occurred: {e}")
        messagebox.showerror("Error", f"Application failed to start: {e}")
