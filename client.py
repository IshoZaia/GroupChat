import socket
import tkinter as tk
from tkinter import messagebox
from threading import Thread


# Function to recieve messages from the server
def receive_messages():
    while True:
        try:
            msg = s.recv(1024).decode('utf-8')  # Receive and decode the message from the server
            chat_box.config(state=tk.NORMAL)  # Enable the widget to insert message
            chat_box.insert(tk.END, msg + '\n')  # Insert the message into the chat box
            chat_box.config(state=tk.DISABLED)  # Disable the widget again
        except Exception as e:  # Error handling
            print(f"An error occurred: {e}")
            break


def send_message(event=None):
    message = message_entry.get()  # Gets text written inside the chat box
    if message:
        if message == 'exit':  # Check if the message is "exit"
            s.send(message.encode())
            s.close()  # Close the connection to the server
            root.quit()  # Close the GUI
        else:
            nickname = root.title().split(': ')[1]  # Getting the nickname of the user
            formatted_message = f"{nickname}: {message}"  # Formatting the message to include the nickname and message
            s.send(formatted_message.encode())  # Send the formatted message
    message_entry.delete(0, tk.END)  # Removes the message you input to prepare for a new message


def enter_nickname():
    nickname = nickname_entry.get() # Get the user inputted nickname from the GUI
    if nickname:  # Check if a nickname exists
        root.title(f"Chat Application: {nickname}")  # Give the chat application a title with the nickname
        nickname_frame.pack_forget()  # Hide the nickname frame
        chat_frame.pack()  # Show the chat frame
        message_entry.focus()  # Set focus to message entry
        start_chat(nickname)  # Calling the start chat function to connect to the server


def start_chat(nickname):
    global s  # Global variable s to simplify use in different functions
    host = '10.0.0.207'  # Replace with your server IP
    port = 60001  # Replace with your server port
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Creating a tcp socket
        s.connect((host, port))  # Establishing connection to server

        # Send the nickname to the server
        s.send(nickname.encode())
    except ConnectionRefusedError:
        messagebox.showerror("Connection Error", "Server may not be running")
        root.quit()

    receive_thread = Thread(target=receive_messages)  # Create a thread with function receive_messages
    receive_thread.daemon = True  # Making daemon thread true to prevent hanging threads
    receive_thread.start()  # Starting the thread to run receive_messages


def main():
    global root, nickname_entry, chat_frame, chat_box, message_entry, nickname_frame

    # Creating the main window
    root = tk.Tk()
    root.title("Chat Application - Enter Nickname")

    # Creating a frame for entering the nickname
    nickname_frame = tk.Frame(root)
    nickname_frame.pack(padx=10, pady=10)

    # Label for entering the nickname
    label = tk.Label(nickname_frame, text="Enter Nickname:")
    label.pack()

    # Entry field for the user to input their nickname
    nickname_entry = tk.Entry(nickname_frame, width=50)
    nickname_entry.pack()

    # Button to submit the entered nickname
    enter_button = tk.Button(nickname_frame, text="Enter", command=enter_nickname)
    enter_button.pack()

    # Creating a frame for the chat interface
    chat_frame = tk.Frame(root)

    # Text box for displaying the chat messages
    chat_box = tk.Text(chat_frame, height=20, width=50)
    chat_box.pack()

    # Entry field for the user to input messages
    message_entry = tk.Entry(chat_frame, width=50)
    message_entry.pack(padx=10, pady=10)
    message_entry.bind("<Return>", send_message)

    # Button to send messages
    send_button = tk.Button(chat_frame, text="Send", command=send_message)
    send_button.pack()

    # Running the application's main event loop
    root.mainloop()


if __name__ == '__main__':
    main()
