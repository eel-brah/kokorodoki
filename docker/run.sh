#!/usr/bin/env bash

export UIDD=$(id -u)
export XDG_RUNTIME_DIR="/run/user/$UIDD"
export WAYLAND_DISPLAY="wayland-0"
export DISPLAY=${DISPLAY:-:0} 

docker compose up "$@"
