import os
from pathlib import Path


def install_service():
    home = Path.home()
    service_path = home / ".config/systemd/user/kokorodoki.service"

    display = os.environ.get("DISPLAY", ":0")

    service_path.parent.mkdir(parents=True, exist_ok=True)

    content = f"""[Unit]
Description=KokoroDoki
After=network.target sound.target
Wants=sound.target

[Service]
Type=simple
ExecStart=%h/.local/bin/kokorodoki --daemon
Environment=DISPLAY={display}
Restart=on-failure
RestartSec=5
ExecStartPre=/bin/sleep 5

[Install]
WantedBy=default.target
"""

    service_path.write_text(content)

    print(f"Service file written to: {service_path}")
    print()
    print("👉 Then run:")
    print("systemctl --user daemon-reload")
    print("systemctl --user enable kokorodoki.service")
    print("systemctl --user start kokorodoki.service")
