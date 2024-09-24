import socket
import os
import struct
import signal
import sys

SOCKET_PATH = '/tmp/example_socket'
exit_flag = False


def signal_handler(signum, frame):
    global exit_flag
    exit_flag = True


def create_socket():
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    return server_socket


def bind_socket(server_socket, path):
    try:
        os.unlink(path)  # Remove the socket if it already exists
    except OSError:
        if os.path.exists(path):
            raise
    server_socket.bind(path)
    print(f"Bound to domain socket: {path}")


def start_listening(server_socket):
    server_socket.listen()
    print("Listening for incoming connections...")


def accept_connection(server_socket):
    client_socket, _ = server_socket.accept()
    print("Accepted a new connection")
    return client_socket


def process_request(client_socket):
    try:
        while True:
            # Read the size of the incoming request (1 byte)
            req_size_data = client_socket.recv(1)
            if not req_size_data:
                break

            req_size = struct.unpack('B', req_size_data)[0]  # Unpack the size as 1 byte

            # Read the request of the specified size
            request_data = client_socket.recv(req_size).decode()
            print(f"Received Request: {request_data}")

            # Simulate processing the request
            response = f"Processed: {request_data}"

            # Send the response size and the response itself
            response_len = len(response)
            client_socket.sendall(struct.pack('B', response_len))
            client_socket.sendall(response.encode())

    except socket.error as e:
        print(f"Socket error: {e}")
    finally:
        try:
            client_socket.close()
        except socket.error as e:
            print(f"Error closing socket: {e}")


def main():
    signal.signal(signal.SIGINT, signal_handler)

    server_socket = create_socket()
    bind_socket(server_socket, SOCKET_PATH)
    start_listening(server_socket)

    while not exit_flag:
        client_socket = accept_connection(server_socket)
        process_request(client_socket)

    server_socket.close()
    os.unlink(SOCKET_PATH)


if __name__ == '__main__':
    main()
