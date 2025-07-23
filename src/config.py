from rich.console import Console

SAMPLE_RATE = 24000  # Kokoro-82M sample rate
MIN_SPEED = 0.5
MAX_SPEED = 2.0
DEFAULT_SPEED = 1.2
DEFAULT_LANGUAGE = "a"
DEFAULT_VOICE = "af_heart"
REPO_ID = "hexgrad/Kokoro-82M"
HISTORY_FILE = ".kokorodoki_history"
HISTORY_LIMIT = 1024
PROMPT = "> "

COMMANDS = [
    "!lang",
    "!voice",
    "!speed",
    "!stop",
    "!pause",
    "!resume",
    "!next",
    "!back",
    "!status",
    "!list_langs",
    "!list_voices",
    "!list_all_voices",
    "!clear",
    "!clear_history",
    "!verbose",
    "!help",
    "!quit",
    "!ctrlc",
    "!status",
]
HOST = "127.0.0.1"
PORT = 5561
TITLE = "KokoroDoki"
WINDOW_SIZE = "700x600"
VERSION = "v0.1.0"
DEFAULT_THEME = 1

console = Console()
