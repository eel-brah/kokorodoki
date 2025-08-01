# KokoroDoki Docker Setup

## Prerequisites

* **NVIDIA GPU Drivers**
  Ensure that your system has a compatible NVIDIA driver installed.

  Run the following command to verify:

  ```bash
  nvidia-smi
  ```

  Make sure the reported **CUDA Version** is **≥ 12.8**.

* **Docker**
  Install Docker if it isn't already installed:
  [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)

## Setup

### 1. Install NVIDIA Container Toolkit

Follow the official installation and configuration guides:

* **Installation**:
  [NVIDIA Container Toolkit Installation Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

* **Configuration**:
  [Configuration Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#configuration)

### 2. Verify NVIDIA Container Runtime

Run a sample workload to test your setup:
[NVIDIA Sample Workload Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/sample-workload.html)


If you encounter the error like this:
```
Failed to initialize NVML: Unknown Error
```

This workaround may help:
👉 [GitHub Issue #381 - Comment](https://github.com/NVIDIA/nvidia-container-toolkit/issues/381#issuecomment-1970824522)

After applying the workaround, run the following command to verify it's working:
```bash
docker run --rm --runtime=nvidia --device=nvidia.com/gpu=all ubuntu nvidia-smi
```

## Docker Compose Configuration

Depending on whether you applied the NVML fix mentioned above:

* **If you applied the fix**:

  ```bash
  cp docker-compose-v2.yml docker-compose.yml
  chmod +x run.sh
  ```

* **Otherwise**:

  ```bash
  cp docker-compose-v1.yml docker-compose.yml
  chmod +x run.sh
  ```

## Running the Application

### Console Mode

```bash
docker compose build kdoki
./run.sh kdoki -d
docker attach <container_name>
```

### GUI Mode

Make X server available to Docker:
```bash
xhost +local:docker
```

Then run:
```bash
docker compose build kdoki_gui
./run.sh kdoki_gui
```

### Daemon Mode

```bash
python3 -m venv mvenv
source mvenv/bin/activate
pip install rich nltk

docker compose build kdoki_daemon
./run.sh kdoki_daemon
```

You can send clipboard content to the daemon using `src/client.py` (port `6155`):

Example:

1. Copy some text like:
   ```
   This is a test.
   ```

2. Run:
   ```bash
   source mvenv/bin/activate
   python3 src/client.py --port 6155
   python3 src/client.py -h
   ```

### Generate an Audio File from Text

Place the text you want to convert into input/input.txt.
Use the following command to generate the output file:
```bash
INPUT_FILE=input.txt OUTPUT_FILE=output.wav ./run.sh kdoki_gen
```
This will produce the audio file at: output/output.wav
