#!/usr/bin/env python

"""
Client.py: the client program for EasyChat.
A simple chat application for CSEE W4119 Computer Networks.
by Artur Upton Renault (aur2103)

"""

import select
import signal
import socket
import sys


# Exit gracefully
def quit(sig_num, status):
    print("\rYou have quit the chat.")
    sock.close()
    exit(0)

# Prompt user for input
def prompt():
    sys.stdout.write("> ")
    sys.stdout.flush()


if __name__ == "__main__":
    # Get address and port from command line
    try:
        serv_addr = socket.gethostbyname(sys.argv[1])
        serv_port = int(sys.argv[2])
    except IndexError, TypeError:
        exit("usage: ./Client.py <server_host> <server_port>")

    signal.signal(signal.SIGINT, quit)

    while True:
        # Create socket
        # No need for arguments because the defaults,
        # socket.AF_INET and socket.SOCK_STREAM are what
        # we want.
        sock = socket.socket()

        # Prompt user for info on startup
        username = raw_input("Username: ")
        password = raw_input("Password: ")

        try:
            sock.connect((serv_addr, serv_port))
        except socket.error:
            exit("Connection failed.")

        # Send authentication info to server.
        # I chose to send it all at once so the server doesn't
        # have to wait around for user input.
        sock.send(username + " " + password)

        # Receive welcome message or rejection
        response = sock.recv(4096).strip().split("\n",1)


        # React accordingly to the response
        if response[0] == "JOIN":
            print(response[1])
            break # Welcome to the chat!
        elif response[0] == "WRONG":
            print(response[1])
            sock.close()
            continue # Some sort of authentication error, try again.
        elif response[0] == "BLOCK":
            sock.close()
            exit(response[1]) # Blocked. Quit clitn.

    # If you get here, you are logged in.
    while True:
        # Check to see if stdin or the socket have new messages ready.

        prompt()
        new_messages, spam, eggs = select.select([sys.stdin, sock], [], [])

        if new_messages:
            # print new messages
            for source in new_messages:
                if source is sock:
                    messages = sock.recv(4096)
                    if messages: # Carriage return to erase prompt
                        sys.stdout.write("\r" + messages)
                    else:
                        exit(
                            "\rConnection lost.\n"
                            "The server may have crashed,"
                            "or you may have been disconnected due to inactivity.")
                else:
                    message = sys.stdin.readline()

                    # logout is the only command handled by the client.
                    # It behaves exactly like CTRL+C.
                    if message.split()[0] == "logout":
                        quit(0, 0)
                    sock.send(message)
