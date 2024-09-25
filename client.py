import argparse
import socket
import struct
import os
import mimetypes
import sys

CHUNK_SIZE = 1024  # Send and receive data in 1024-byte chunks


def parse_arguments():
    parser = argparse.ArgumentParser(description='Client for sending file contents over UNIX domain socket.')
    parser.add_argument('files', metavar='FILE', nargs='+', help='Files to send to the server')
    parser.add_argument('--socket', '-s', default='/tmp/example_socket', help='Path to the UNIX domain socket')
    return parser.parse_args()


def connect_to_server(socket_path):
    client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client_socket.connect(socket_path)
    except socket.error as e:
        print(f"Connection failed: {e}")
        sys.exit(1)
    return client_socket


def is_supported_text_file(file_path):
    # Check if the file exists before using mimetypes
    if not os.path.isfile(file_path):
        print(f"File {file_path} not found")
        return False

    # Use mimetypes to determine the file type
    mime_type, _ = mimetypes.guess_type(file_path)

    # Allow shell scripts (.sh) and other plain text files
    if mime_type is None or mime_type.startswith('text'):
        return True

    # Explicitly allow certain extensions like .sh
    if file_path.endswith('.sh'):
        return True

    # Add more extensions here if needed
    return False


def send_file_content(file_path, client_socket):
    if not is_supported_text_file(file_path):
        print(f"File type not supported: {file_path}")
        return False  # Indicate that the file was not sent

    try:
        # Get the size of the file content
        file_size = os.path.getsize(file_path)

        print(f"\nSending text contents of {file_path} (size: {file_size} bytes)...")

        # Send the file size as a fixed-size 8-byte integer
        client_socket.sendall(struct.pack('Q', file_size))

        # Open the file and send its content in chunks
        with open(file_path, 'r') as file:
            while True:
                chunk = file.read(CHUNK_SIZE)
                if not chunk:
                    break
                client_socket.sendall(chunk.encode())

        # After sending the file content, receive the server's response
        response_size_data = client_socket.recv(8)  # Read 8 bytes for the response size
        if not response_size_data:
            print("No response from server.")
            return False

        response_size = struct.unpack('Q', response_size_data)[0]
        response = b''

        # Read the response in chunks
        while len(response) < response_size:
            response_chunk = client_socket.recv(CHUNK_SIZE)
            if not response_chunk:
                break
            response += response_chunk

        print(f"Server Response: {response.decode()}\n")
        return True  # Indicate that the file was successfully sent

    except FileNotFoundError:
        print(f"File {file_path} not found")
        return False  # Indicate that the file was not sent


def main():
    args = parse_arguments()
    client_socket = connect_to_server(args.socket)

    # Loop through each file path and send the file contents
    for file_path in args.files:
        send_file_content(file_path, client_socket)

    client_socket.close()


if __name__ == '__main__':
    main()
