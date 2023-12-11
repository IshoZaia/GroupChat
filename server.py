import socket
import threading
import sqlite3
from datetime import datetime
from Crypto.Cipher import AES

lock = threading.Lock()  # Lock for thread-safe operations on client list
clients_list = []  # List to keep track of connected clients
threads = []  # List to keep track of threads
# Key used for message encryption into database
key = b'\x01\x23\x45\x67\x89\xab\xcd\xef\x01\x23\x45\x67\x89\xab\xcd\xef'


def create_database_connection():
    # Connects to a SQLLite database
    return sqlite3.connect('group-chat_database.db')


def create_messages_table(conn, cursor):
    # Creates a table for the database that stores the name
    # message and timestamp
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Messages (
            MessageID INTEGER PRIMARY KEY AUTOINCREMENT,
            SenderName TEXT,
            Content TEXT,
            Timestamp DATETIME
        )
    ''')
    conn.commit()  # Commit the data to the database


def encrypt_msg(message):
    cipher = AES.new(key, AES.MODE_EAX)  # Creates AES cipher instance
    ciphertext, tag = cipher.encrypt_and_digest(message)  # Creates encrypted message and tag to verify integirty for decryption
    nonce = cipher.nonce  # Random number generated needed for decryption, not used b/c we do not decrypt
    return ciphertext.hex()  # Returning only the encrypted message as hexidecimal value to be displayed in database
    # Otherwise returns BLOB inside DB


def broadcast(message, sender_name, local_cursor, local_conn):
    with lock:  # Lock thread for safe access of client list
        for client in clients_list:  # Iterate through each client
            try:
                client.send(message)  # Sends message to each client
            except Exception as e:
                print(e)  # Print the error
                client.close()  # Closes the connection on error
                # if the connection is broken, the client is removed
                remove(client)

        encrypted_message = encrypt_msg(message)  # Encrypting the message

        # Insert encrypted messages into the database
        local_cursor.execute('INSERT INTO Messages (SenderName, Content, Timestamp) VALUES (?, ?, ?)',
                            (sender_name, encrypted_message, datetime.now()))
        local_conn.commit()


def server_message(message):
    with lock:
        if clients_list:
            for client in clients_list:
                try:
                    client.send(message)  # Sends system message to each client
                except Exception as e:
                    print(e)  # Print the error
                    client.close()  # Closes the connection on error
                    # if the connection is broken, the client is removed
                    remove(client)


def remove(connection):
    with lock:  # Ensure it is safe to remove client from list
        if connection in clients_list:
            clients_list.remove(connection)  # For the connection that disconnects we remove them from the list
            connection.close()


def server_connection(connection, nickname):
    # Create a separate database connection for each thread
    local_conn = create_database_connection()
    local_cursor = local_conn.cursor()
    try:
        while True:
            message = connection.recv(1024)  # Receive messages from the client
            if message:
                print(message.decode())  # Decode the message and print it
                if message.decode() == "exit":
                    # Removes the client when disconnected
                    connection.close()
                    remove(connection)
                    local_cursor.close()
                    local_conn.close()
                    server_message(f"{nickname} has left the chat".encode())
                    break
                else:
                    broadcast(message, nickname, local_cursor, local_conn)  # Call the broadcast function to display the message
            else:
                remove(connection, nickname)  # Removes the client when disconnected
                local_cursor.close()
                local_conn.close()
                connection.close()
                break

    except Exception as e: # Prints any error that occurs
        print(f"Error in server_connection: {e}")
    finally:
        local_conn.close()  # Closes the database connection when done


def server_setup():
    host = '0.0.0.0'  # Host address to listen on entire network
    port = 60001  # Port number for server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Creating TCP Connection
    server_socket.bind((host, port))  # Bind socket to host and port
    server_socket.listen(10)
    return server_socket  # Return the socket created


def accept_client_conn(server_socket):
    while True:
        conn, addr = server_socket.accept()  # Accept incoming client connection
        with lock:  # Lock thread while appending clients list
            clients_list.append(conn)  # Append the client to the client lst
            nickname = conn.recv(1024).decode()  # Receive the nickname from the client that connected
            print(nickname, addr, 'Connected to the server')
            # Start a new thread for each client that connects
            thread = threading.Thread(target=server_connection, args=(conn, nickname))
            threads.append(thread)  # Adding thread to a list of threads
            thread.start()  # Running the thread
        server_message(f"{nickname} has joined the chat".encode()) # Sending a message to clients to tell them someone joined


def main():
    server_socket = server_setup()  # Storing the server setup
    print(f'Server listening on {server_socket.getsockname()}')  # Displaying the connection serverside

    # Create a global database connection and cursor
    global_conn = create_database_connection()
    global_cursor = global_conn.cursor()

    # Create the Messages table if it doesn't exist
    create_messages_table(global_conn, global_cursor)

    try:  # Accept and handle clients
        accept_client_conn(server_socket)
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        global_conn.close()  # Close the database connection
        server_socket.close()  # Close the server socket
        for thread in threads:
            thread.join()  # Joining threads ensures server is shutdown correctly


if __name__ == '__main__':
    main()
