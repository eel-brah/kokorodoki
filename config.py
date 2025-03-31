from rich.console import Console

SAMPLE_RATE = 24000  # Kokoro-82M sample rate
MIN_SPEED = 0.5
MAX_SPEED = 2.0
DEFAULT_SPEED = 1.0
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
    "!list_langs",
    "!list_voices",
    "!clear",
    "!clear_history",
    "!help",
    "!quit",
]
HOST = "0.0.0.0" 
PORT = 5561     


console = Console()
