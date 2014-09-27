#!/usr/bin/env python

import select
import signal
import socket
import sys


# Exit gracefully
def quit(sig_num, status):
    print("\nYou have quit the chat.")
    sock.close()
    exit(0)


# Wait for input from user
def wait_for_input():
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

        response = sock.recv(4096).split("\n")
        if response[0] != "AUTHENTICATE":
            sock.close()
            exit("Protocol error")

        sock.send("AUTHENTICATE\n" + username + " " + password)

        # Receive welcome message or rejection
        response = sock.recv(4096).split("\n")

        if response[0] == "JOIN":
            print(response[1])
            break
        elif response[0] == "WRONG":
            print(response[1])
            sock.close()
            continue
        elif response[0] == "BLOCK":
            sock.close()
            exit(response[1])

    # If you get here, you are logged in.
    while True:
        wait_for_input()
        new_messages, spam, eggs = select.select([sys.stdin, sock], [], [])

        if new_messages:
            for source in new_messages:
                if source is sock:
                    messages = sock.recv(4096)
                    if messages:
                        print(messages)
                    else:
                        exit("Server error.")
                else:
                    message = sys.stdin.readline()
                    sock.send(message)