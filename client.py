import argparse
import socket
import subprocess

SERVER_IP = "127.0.0.1"
PORT = 5561


def get_clipboard():
    try:
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    except subprocess.CalledProcessError as e:
        print(f"Error reading clipboard: {e}")
        print(f"Command returned {e.returncode}")
        print(f"Error output: {e.stderr}")
        return None
    except FileNotFoundError:
        print("Error: xclip is not installed. Please install it first.")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def send_clipboard():
    clipboard_content = get_clipboard()
    if clipboard_content is not None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((SERVER_IP, PORT))
            client_socket.sendall(clipboard_content.encode())


def stop():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((SERVER_IP, PORT))
        client_socket.sendall("!stop".encode())


def main():
    parser = argparse.ArgumentParser(
        description="Send clipboard content to kokorodoki or stop reading",
    )

    parser.add_argument(
        "-s",
        action="store_true",
        help="Stop reading",
    )

    args = parser.parse_args()

    if args.s:
        stop()
    else:
        send_clipboard()


if __name__ == "__main__":
    main()
