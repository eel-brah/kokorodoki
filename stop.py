import socket
import subprocess

SERVER_IP = "127.0.0.1"
PORT = 5561


def stop():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((SERVER_IP, PORT))
        client_socket.sendall("!stop".encode())


if __name__ == "__main__":
    stop()
