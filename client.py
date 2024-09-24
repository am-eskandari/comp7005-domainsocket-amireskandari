import socket
import sys
import struct
import os
import mimetypes

SOCKET_PATH = '/tmp/example_socket'


def parse_arguments():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file1> [<file2> ...]")
        sys.exit(1)
    return sys.argv[1:]  # Return a list of file paths


def connect_to_server(socket_path):
    client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client_socket.connect(socket_path)
    except socket.error as e:
        print(f"Connection failed: {e}")
        sys.exit(1)
    return client_socket


def is_supported_text_file(file_path):
    # Use mimetypes to determine the file type
    mime_type, _ = mimetypes.guess_type(file_path)

    # Only support text-based files (text/plain or files with no extension)
    return mime_type is None or mime_type.startswith('text')


def send_file_content(file_path, client_socket):
    if not is_supported_text_file(file_path):
        print(f"File type not supported: {file_path}")
        return False  # Indicate that the file was not sent

    try:
        # Read the entire file content into one line
        with open(file_path, 'r') as file:
            file_content = file.read().replace('\n', ' ')  # Replace newlines with spaces for a single line

        print(f"\nSending text contents of {file_path}...")

        # Send the content as one line
        file_len = len(file_content)
        if file_len > 255:
            print("File content exceeds maximum length")
            client_socket.close()
            sys.exit(1)

        client_socket.sendall(struct.pack('B', file_len))  # Send content length
        client_socket.sendall(file_content.encode())  # Send the file content as one line

        # After sending the file content, receive the server's response
        response_len = struct.unpack('B', client_socket.recv(1))[0]
        response = client_socket.recv(response_len).decode()

        # Print success message with actual file content
        print(f"Process succeeded: content of file '{file_path}' sent in one line.")
        print(f"File Content: {file_content}")
        print(f"Content of '{file_path}' sent and response received.\n")
        return True  # Indicate that the file was successfully sent

    except FileNotFoundError:
        print(f"File {file_path} not found")
        return False  # Indicate that the file was not sent


def main():
    file_paths = parse_arguments()  # Get the list of file paths
    client_socket = connect_to_server(SOCKET_PATH)

    # Loop through each fi
    # le path and send the file contents
    for file_path in file_paths:
        send_file_content(file_path, client_socket)

    client_socket.close()


if __name__ == '__main__':
    main()
