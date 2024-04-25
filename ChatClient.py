import socket
import sys
import json
import time
import threading

class ChatClient:
    def __init__(self, server_ip, server_port, nickname, client_id):
        self.server_ip = server_ip
        self.server_port = server_port
        self.nickname = nickname
        self.client_id = client_id
        self.socket = None
        self.connected = False
        self.receive_thread = None
        # Statistics attributes
        self.sent_messages_count = 0
        self.received_messages_count = 0
        self.sent_characters_count = 0
        self.received_characters_count = 0
        self.start_time = None  # Initialize start time

    def start(self):
        # Set start time when the chat starts
        self.start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
       
        self.connect_to_server()

        while not self.connected:
            time.sleep(1)

        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.start()
        
        print("Enter Message:")
        self.capture_user_input()

    def connect_to_server(self):
        try:
            # Resolve hostname if provided
            ip = socket.gethostbyname(self.server_ip)
            self.server_ip = ip
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.server_port))
            self.connected = True
            initial_message = {
                "type": "nickname",
                "nickname": self.nickname,
                "clientID": self.client_id,
                "timestamp": self.get_timestamp()
            }
            self.send_message(initial_message)
        except socket.error as e:
            print(f"Error: {e}")

    def capture_user_input(self):
        try:
            while self.connected :
                
                message = input("> ")
                if message.lower() == "disconnect":
                    self.disconnect()
                    
                else:
                    message_data = {
                        "type": "message",
                        "nickname": self.nickname,
                        "message": message,
                        "timestamp": self.get_timestamp()
                    }
                    self.send_message(message_data)
        except KeyboardInterrupt:
            self.disconnect()
            
        

    def send_message(self, message):
        try:
            self.socket.sendall(json.dumps(message).encode())
            # Update statistics if the message contains text
            if "message" in message:
                self.sent_messages_count += 1
                self.sent_characters_count += len(message["message"])
        except socket.error as e:
            print(f"Error sending message: {e}")
            self.connected = False

    def receive_messages(self):
        while self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                message = json.loads(data.decode())
                if message["type"] == "error":
                    # Handling error messages from the server
                    print(f"Error: {message['message']}")
                    self.handle_error(message['message'])
                    
                elif message["type"] == "broadcast":
                    # Displaying broadcast messages from other clients
                    print(f"{self.format_timestamp(message['timestamp'])}::{message['nickname']}: {message['content']}")
                    # Update statistics
                    if "content" in message:
                        self.received_messages_count += 1
                        self.received_characters_count += len(message["content"])
            except json.JSONDecodeError:
                print("Error decoding JSON message from server.")
                continue
            except socket.error as e:
                print(f"Error receiving message: {e}")
                self.connected = False

    def handle_error(self, error_message):
        # Handling different types of errors from the server
        if "Nickname already in use" in error_message:
            
            print("Please choose a different nickname.")
            self.nickname = input("Enter your nickname: ")
            self.connected = False
            self.socket.close()
            self.connect_to_server()  # Reconnect with new nickname
        elif "ClientID must be unique" in error_message:
            print("Client ID must be unique. Please choose a different ID.")
            self.client_id = input("Enter your client ID: ")
            self.connected = False
            self.socket.close()
            self.connect_to_server()  # Reconnect with new client ID
        else:
            print(f"Unknown error: {error_message}")
            sys.exit(1)

    def get_timestamp(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    def format_timestamp(self, timestamp):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.strptime(timestamp, "%Y-%m-%d %H:%M:%S"))
    def disconnect(self):
        # Send a disconnect message to the server and close the socket
        print("\nDisconnecting from the chat...")
        disconnect_message = {
            "type": "disconnect",
            "nickname": self.nickname,
            "clientID": self.client_id
        }
        self.send_message(disconnect_message)
        self.socket.close()
        # Calculate statistics
        end_time = self.get_timestamp()
        total_sent_messages = self.sent_messages_count
        total_received_messages = self.received_messages_count
        total_sent_characters = self.sent_characters_count
        total_received_characters = self.received_characters_count
        # Print summary
        print("Summary:")
        print(f"  start: {self.start_time}, end: {end_time}")
        print(f"  msg sent: {total_sent_messages}, msg rev: {total_received_messages}")
        print(f"  char sent: {total_sent_characters}, char rev: {total_received_characters}")
        # Exit the client
        print("Disconnected from the chat.")
        # Set the connected flag to False
        self.connected = False
        sys.exit(0)
        

def main():
    
    # Check if any argument is missing
    for i in range(1, 5):
        try:
            arg = sys.argv[i]
        except IndexError:
            print(f"ERR -arg {i}")
            sys.exit(1)

    # Assigning command line arguments to variables
    try:
        server_ip = sys.argv[1]
        server_port = int(sys.argv[2])
        nickname = sys.argv[3]
        client_id = sys.argv[4]
    except ValueError:
        print("ERR - Incorrect argument type.")
        sys.exit(1)

    chat_client = ChatClient(server_ip, server_port, nickname, client_id)
    # Print the startup message
    def get_timestamp():
    # Get the current timestamp in the specified format
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"ChatClient started with server IP: {server_ip}, port: {server_port}, "
    f"nickname: {nickname}, client ID: {client_id}, Date/Time: {get_timestamp()}")
    

    try:
        chat_client.start()
    except KeyboardInterrupt:
        chat_client.disconnect()

if __name__ == "__main__":
    main()
