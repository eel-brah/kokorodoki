#!/bin/bash
set -e

echo "Starting..."
echo "TTY: $(tty)"

./kdoki/kokorodoki -t " "

exec ./kdoki/kokorodoki "$@"
