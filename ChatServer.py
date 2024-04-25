import socket  # Importing the socket module for network communication
import sys     # Importing sys module to access command line arguments and exit function
import threading  # Importing threading module to handle multiple connections concurrently
import json    # Importing json module to work with JSON data
import time    # Importing time module to work with timestamps

class ChatServer:
    def __init__(self, port):
        self.port = port
        self.server_socket = None
        self.clients = {}  # Dictionary to store connected clients
        self.running = False

    def start(self):
        self.running = True
        # Creating a TCP socket for the server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Binding the server socket to localhost and the specified port
        try:
            self.server_socket.bind(('localhost', self.port))
        except OSError as e:
            # Handle the case where the socket cannot be created
            if e.errno == 98:
                print(f"ERR - cannot create ChatServer socket using port number {self.port}: Address already in use")
            else:
                print(f"ERR - cannot create ChatServer socket using port number {self.port}: {e}")
            sys.exit(1)
        # Listening for incoming connections
        self.server_socket.listen(5)
        print(f"ChatServer started with server IP: localhost, port: {self.port}")

        try:
            # Continuously accept incoming connections
            while self.running:
                client_socket, client_address = self.server_socket.accept()
                # Spawning a new thread to handle each client connection
                threading.Thread(target=self.handle_client, args=(client_socket, client_address)).start()
        
        except KeyboardInterrupt:
            print("Server shutting down...")
            self.shutdown()

    def shutdown(self):
        self.running = False
        # Closing connections with all clients
        for client_socket in self.clients.keys():
            client_socket.close()
        self.server_socket.close()
        sys.exit(0)

    def handle_client(self, client_socket, client_address):
        try:
            nickname = None
            client_id = None
            # Continuously receive and process messages from the client
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                message = json.loads(data.decode())
                if message["type"] == "nickname":
                    nickname = message["nickname"]
                    client_id = message["clientID"]
                    if nickname in self.clients.values():
                        error_message = {"type": "error", "message": "Nickname already in use"}
                        client_socket.sendall(json.dumps(error_message).encode())
                        
                    elif client_id in self.clients.values():
                        error_message = {"type": "error", "message": "ClientID must be unique"}
                        client_socket.sendall(json.dumps(error_message).encode())
                        
                    else:
                        # Add client to the dictionary of connected clients
                        self.clients[client_socket] = nickname
                        # Notify about the client's connection
                        connection_message = f"{self.get_timestamp()}::{nickname}: connected."
                        print(connection_message)
                        
                elif message["type"] == "message":
                    print(f"Received: IP:{client_address[0]}, Port:{client_address[1]}, "
                          f"Client-Nickname: {nickname}, ClientID: {client_id}, "
                          f"Date/Time: {message.get('timestamp', self.get_timestamp())}, "
                          f"Msg-Size: {sys.getsizeof(data)}")
                    # Broadcast the message to all clients except the sender
                    broadcast_message = {
                        "type": "broadcast",
                        "nickname": nickname,
                        "content": message["message"],
                        "timestamp": message.get("timestamp", self.get_timestamp())
                    }
                    self.broadcast_message(client_socket, broadcast_message)
                elif message["type"] == "disconnect":
                    print(f"{message.get('timestamp', self.get_timestamp())}::{nickname}: disconnected.")
                    # Remove client from the dictionary and close the connection
                    del self.clients[client_socket]
                    client_socket.close()
                    break
        except (ConnectionResetError, ConnectionAbortedError, KeyError):
            print(f"Connection with {client_address} lost.")
            if client_socket in self.clients:
                del self.clients[client_socket]
            client_socket.close()

    def broadcast_message(self, sender_socket, message):
        # Retrieve a list of all clients except the sender
        receivers = [client_socket for client_socket in self.clients.keys() if client_socket != sender_socket]
        # Broadcast the message to all receivers
        for client_socket in receivers:
            try:
                client_socket.sendall(json.dumps(message).encode())
            except BrokenPipeError:
                # Handle broken pipe error (client disconnected)
                print("Client disconnected unexpectedly.")
                del self.clients[client_socket]
        if receivers:
            print("Broadcasted:", ", ".join(self.clients[client] for client in receivers))

    def get_timestamp(self):
        # Get the current timestamp in a specific format
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def main():
    # Checking if the port number is provided as a command line argument
    if len(sys.argv) != 2:
        print("ERR -arg 1")
        sys.exit(1)
    
    try:
        port = int(sys.argv[1])
        # Validating the provided port number
        if not 10000 <= port <= 11000:
            raise ValueError
    except ValueError:
        print("ERR -arg 1")
        sys.exit(1)

    # Creating an instance of the ChatServer class and starting the server
    chat_server = ChatServer(port)
    chat_server.start()

if __name__ == "__main__":
    main()
