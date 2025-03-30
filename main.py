#!/usr/bin/env python3

import sys

from input_hander import Args, parse_args
from utils import init_history


def main():
    """Main entry point."""
    args: Args = parse_args()

    init_history(args.history_off)

    from run import start

    start(args)


if __name__ == "__main__":
    sys.exit(main())
