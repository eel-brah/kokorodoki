#!/usr/bin/env python3

import sys

from input_hander import parse_args
from utils import init_history


def main():
    """Main entry point."""
    language, voice, speed, history_off, device, input_text, output_file = parse_args()

    init_history(history_off)

    from run import start

    start(language, voice, speed, history_off, device, input_text, output_file)


if __name__ == "__main__":
    sys.exit(main())
