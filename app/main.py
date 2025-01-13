import socket  # noqa: F401

def main():
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    client, addr = server_socket.accept()

    client_msg = client.recv(4096).decode().split(" ")

    path = client_msg[1]

    if path == "/":
        client.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
    else:
        endpoint_arr = path.split("/")
        if endpoint_arr[1] == "echo":
            client.sendall(
                f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(endpoint_arr[2])}\r\n\r\n{endpoint_arr[2]}\r\n".encode()
            )
        elif endpoint_arr[1] == "user-agent":
            client.sendall(
                f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(client_msg[5])}\r\n\r\n{client_msg[5]}\r\n".encode()
            )
        else:
            client.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")

if __name__ == "__main__":
    main()
