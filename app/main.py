import socket
import threading
import sys
import gzip
import io

response_200_format_basic = "HTTP/1.1 200 OK\r\nContent-Type: {}\r\nContent-Length: {}\r\n\r\n{}"
response_200_format_encoding = "HTTP/1.1 200 OK\r\nContent-Type: {}\r\nContent-Encoding: gzip\r\nContent-Length: {}\r\n\r\n"
response_404 = "HTTP/1.1 404 Not Found\r\n\r\n"
response_201 = "HTTP/1.1 201 Created\r\n\r\n"

def compress_content(content):
    """Compress content using gzip"""
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode='w') as gz:
        gz.write(content.encode('utf-8'))
    return out.getvalue()

def send_response(client, content_type, content, headers):
    """Send response with compression if supported"""
    accept_encoding = headers.get('Accept-Encoding', '')
    if 'gzip' in accept_encoding:
        # Compress the content
        compressed_content = compress_content(content)
        # Send headers
        header = response_200_format_encoding.format(
            content_type, 
            len(compressed_content)
        ).encode('utf-8')
        # Send response in parts
        client.sendall(header)
        client.sendall(compressed_content)
    else:
        # Send uncompressed response
        response = response_200_format_basic.format(
            content_type,
            len(content),
            content
        ).encode('utf-8')
        client.sendall(response)

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
        headers = request['headers']
        
        if path == "/":
            client.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
        else:
            endpoint_arr = path.split("/")
            if endpoint_arr[1] == "echo":
                send_response(client, "text/plain", endpoint_arr[2], headers)
            elif endpoint_arr[1] == "user-agent":
                user_agent = headers.get('User-Agent', '')
                send_response(client, "text/plain", user_agent, headers)
            elif endpoint_arr[1] == "files":
                if request['method'] == "GET":
                    file_name = endpoint_arr[2]
                    try:
                        with open(f"{directory}{file_name}", "r") as file:
                            content = file.read()
                            send_response(client, "application/octet-stream", content, headers)
                    except FileNotFoundError:
                        client.sendall(response_404.encode())
                elif request['method'] == "POST":
                    file_name = endpoint_arr[2]
                    with open(f"{directory}{file_name}", "w") as file:
                        file.write(request['body'])
                    client.sendall(response_201.encode())
            else:
                client.sendall(response_404.encode())
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