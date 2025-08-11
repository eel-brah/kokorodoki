#!/bin/bash
set -e

echo "Starting..."
echo "TTY: $(tty)"

if [ "$SKIP_STARTUP_MSG" != "1" ]; then
    /root/.local/bin/kdoki/kokorodoki -t "Starting..."
fi

exec /root/.local/bin/kdoki/kokorodoki "$@"
