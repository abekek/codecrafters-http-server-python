import socket
import threading
import sys

def parse_http_request(data):
    # Split the request into headers and body
    request_parts = data.split('\r\n\r\n', 1)
    headers_part = request_parts[0]
    body = request_parts[1] if len(request_parts) > 1 else ''
    
    # Parse the request line and headers
    headers_lines = headers_part.split('\r\n')
    method, path, _ = headers_lines[0].split(' ')
    
    # Parse headers into a dictionary
    headers = {}
    for line in headers_lines[1:]:
        if ': ' in line:
            key, value = line.split(': ', 1)
            headers[key] = value
    
    return {
        'method': method,
        'path': path,
        'headers': headers,
        'body': body
    }

def handle_client(client):
    try:
        # Receive the complete HTTP request
        request_data = b''
        while True:
            chunk = client.recv(4096)
            request_data += chunk
            if b'\r\n\r\n' in request_data:
                # If this is a POST request, ensure we have the complete body
                if request_data.startswith(b'POST'):
                    headers_end = request_data.index(b'\r\n\r\n') + 4
                    headers = request_data[:headers_end].decode('utf-8')
                    for line in headers.split('\r\n'):
                        if line.startswith('Content-Length: '):
                            content_length = int(line.split(': ')[1])
                            while len(request_data) < headers_end + content_length:
                                chunk = client.recv(4096)
                                if not chunk:
                                    break
                                request_data += chunk
                break
            if not chunk:
                break

        # Parse the HTTP request
        request = parse_http_request(request_data.decode('utf-8'))
        path = request['path']
        
        if path == "/":
            client.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
        else:
            endpoint_arr = path.split("/")
            if endpoint_arr[1] == "echo":
                client.sendall(
                    f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(endpoint_arr[2])}\r\n\r\n{endpoint_arr[2]}\r\n".encode()
                )
            elif endpoint_arr[1] == "user-agent":
                user_agent = request['headers'].get('User-Agent', '')
                client.sendall(
                    f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(user_agent)}\r\n\r\n{user_agent}\r\n".encode()
                )
            elif endpoint_arr[1] == "files":
                if request['method'] == "GET":
                    file_name = endpoint_arr[2]
                    try:
                        with open(f"{directory}{file_name}", "r") as file:
                            content = file.read()
                            client.sendall(
                                f"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {len(content)}\r\n\r\n{content}\r\n".encode()
                            )
                    except FileNotFoundError:
                        client.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
                elif request['method'] == "POST":
                    file_name = endpoint_arr[2]
                    with open(f"{directory}{file_name}", "w") as file:
                        file.write(request['body'])
                    client.sendall(b"HTTP/1.1 201 Created\r\n\r\n")
            else:
                client.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
    finally:
        client.close()

def main():
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    if "--directory" in sys.argv:
        global directory
        directory = sys.argv[sys.argv.index("--directory") + 1]
    
    while True:
        client, _ = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    main()