#!/bin/bash

HOME_DIR="$HOME"

DISPLAY_VAR="${DISPLAY:-:0}"

WORKING_DIR="$HOME_DIR/.local/bin/kdoki/src"
PYTHON_EXEC="$HOME_DIR/.venvs/kdvenv/bin/python3.12"
MAIN_SCRIPT="$WORKING_DIR/main.py"
SERVICE_PATH="$HOME_DIR/.config/systemd/user/kokorodoki.service"

mkdir -p "$(dirname "$SERVICE_PATH")"

cat > "$SERVICE_PATH" <<EOF
[Unit]
Description=kokorodoki
After=network.target sound.target 
Wants=sound.target

[Service]
Type=simple
WorkingDirectory=$WORKING_DIR
ExecStart=$PYTHON_EXEC $MAIN_SCRIPT --daemon
Environment=DISPLAY=$DISPLAY_VAR
Restart=on-failure
RestartSec=5
ExecStartPre=/bin/sleep 5

[Install]
WantedBy=default.target
EOF

echo "Service file written to: $SERVICE_PATH"
