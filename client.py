import argparse
import socket
import struct
import os
import mimetypes
import sys
import errno

CHUNK_SIZE = 1024
TIMEOUT = 5


def parse_arguments():
    parser = argparse.ArgumentParser(description='Client for sending file contents over UNIX domain socket.')
    parser.add_argument('files', metavar='FILE', nargs='+', help='Files to send to the server')
    parser.add_argument('--socket', '-s', default='/tmp/example_socket', help='Path to the UNIX domain socket')
    return parser.parse_args()


def connect_to_server(socket_path):
    client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    client_socket.settimeout(TIMEOUT)

    try:
        if not os.path.exists(socket_path):
            raise FileNotFoundError(f"Error: Socket file {socket_path} does not exist.")

        client_socket.connect(socket_path)
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)
    except socket.timeout:
        print(f"Error: Connection to server timed out after {TIMEOUT} seconds.")
        sys.exit(1)
    except socket.error as e:
        if e.errno == errno.ECONNREFUSED:
            print(f"Error: No server running at {socket_path}. Connection refused.")
        elif e.errno == errno.ENOENT:
            print(f"Error: Socket file {socket_path} does not exist.")
        else:
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
    if file_path.endswith('.sh'):
        return True

    return False


def send_file_content(file_path, client_socket):
    if not is_supported_text_file(file_path):
        print(f"File type not supported: {file_path}")
        return False

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

        # After sending the file content, attempt to receive the server's response
        try:
            response_size_data = client_socket.recv(8)
        except TimeoutError:
            print("Error: No response from server. The connection timed out.")
            return False

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

    except socket.error as e:
        print(f"Socket error: {e}")
        return False


def main():
    args = parse_arguments()
    client_socket = connect_to_server(args.socket)

    # Loop through each file path and send the file contents
    for file_path in args.files:
        send_file_content(file_path, client_socket)

    client_socket.close()


if __name__ == '__main__':
    main()

