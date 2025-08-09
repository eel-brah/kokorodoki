FROM nvidia/cuda:12.8.0-cudnn-runtime-ubuntu24.04

RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-tk \
    portaudio19-dev \
    espeak \
    libreadline-dev libncurses-dev pulseaudio-utils \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /root/.local/bin

COPY . kdoki

WORKDIR /root/.venvs
RUN python3.12 -m venv kdvenv
RUN /bin/bash -c "source kdvenv/bin/activate && pip install --upgrade pip && pip install -r /root/.local/bin/kdoki/requirements.txt"

RUN /root/.venvs/kdvenv/bin/python3.12 /root/.local/bin/kdoki/src/main.py --setup

ENTRYPOINT ["/root/.local/bin/kdoki/kokorodoki"]
CMD []
