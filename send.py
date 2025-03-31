import socket
import subprocess

SERVER_IP = "127.0.0.1"
PORT = 5561


def send_clipboard():
    clipboard_content = subprocess.run(
        ["xclip", "-selection", "clipboard", "-o"], capture_output=True, text=True
    ).stdout.strip()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((SERVER_IP, PORT))
        client_socket.sendall(clipboard_content.encode())


if __name__ == "__main__":
    send_clipboard()
