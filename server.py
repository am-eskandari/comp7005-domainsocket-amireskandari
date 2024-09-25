import argparse
import socket
import os
import struct
import signal
import sys

CHUNK_SIZE = 1024
exit_flag = False

def signal_handler(signum, frame):
    global exit_flag
    exit_flag = True

def parse_arguments():
    parser = argparse.ArgumentParser(description='Server for processing client requests over UNIX domain socket.')
    parser.add_argument('--socket', '-s', default='/tmp/example_socket', help='Path to the UNIX domain socket')
    return parser.parse_args()

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
            # Read the size of the incoming file (8 bytes)
            file_size_data = client_socket.recv(8)
            if not file_size_data:
                break

            file_size = struct.unpack('Q', file_size_data)[0]
            print(f"Receiving a file of size {file_size} bytes...")

            # Read the file content in chunks
            file_content = b''
            while len(file_content) < file_size:
                chunk = client_socket.recv(min(CHUNK_SIZE, file_size - len(file_content)))
                if not chunk:
                    break
                file_content += chunk

            file_content = file_content.decode()
            print(f"Received file content: {file_content[:50]}...")  # Print first 50 characters for brevity

            # Simulate processing the file content
            processed_content = file_content.upper()

            # Send the size of the processed content
            response_size = len(processed_content)
            client_socket.sendall(struct.pack('Q', response_size))

            # Send the processed content in chunks
            sent = 0
            while sent < response_size:
                chunk = processed_content[sent:sent + CHUNK_SIZE]
                client_socket.sendall(chunk.encode())
                sent += len(chunk)

    except socket.error as e:
        print(f"Socket error: {e}")
    finally:
        try:
            client_socket.close()
        except socket.error as e:
            print(f"Error closing socket: {e}")

def main():
    signal.signal(signal.SIGINT, signal_handler)

    args = parse_arguments()
    server_socket = create_socket()
    bind_socket(server_socket, args.socket)
    start_listening(server_socket)

    while not exit_flag:
        client_socket = accept_connection(server_socket)
        process_request(client_socket)

    server_socket.close()
    os.unlink(args.socket)

if __name__ == '__main__':
    main()
