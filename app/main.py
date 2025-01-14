import socket
import threading
import sys

def handle_client(client):
    try:
        client_msg = client.recv(4096).decode().split(" ")
        path = client_msg[1]
        
        print(f"Received message from client: {client_msg}")
        
        if path == "/":
            client.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
        else:
            endpoint_arr = path.split("/")
            if endpoint_arr[1] == "echo":
                client.sendall(
                    f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(endpoint_arr[2])}\r\n\r\n{endpoint_arr[2]}\r\n".encode()
                )
            elif endpoint_arr[1] == "user-agent":
                user_agent = ""
                for i, part in enumerate(client_msg):
                    if "User-Agent:" in part:
                        user_agent = client_msg[i + 1].split("\r\n")[0]
                        break
                
                client.sendall(
                    f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(user_agent)}\r\n\r\n{user_agent}\r\n".encode()
                )
            elif endpoint_arr[1] == "files":
                if client_msg[0] == "GET":
                    file_name = endpoint_arr[2]
                    try:
                        with open(f"{directory}{file_name}", "r") as file:
                            content = file.read()
                            client.sendall(
                                f"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {len(content)}\r\n\r\n{content}\r\n".encode()
                            )
                    except FileNotFoundError:
                        client.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
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
        thread.daemon = True  # Make thread daemon so it exits when main thread exits
        thread.start()

if __name__ == "__main__":
    main()