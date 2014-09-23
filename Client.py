#!/usr/bin/env python
import sys
import socket

# Get address and port from command line
try:
    serv_addr = socket.gethostbyname(sys.argv[1])
    serv_port = int(sys.argv[2])
except IndexError, TypeError:
    exit("usage: ./Client.py <server_host> <server_port>")

try:
    while True:
        # Create socket
        # No need for arguments because the defaults,
        # socket.AF_INET and socket.SOCK_STREAM are what
        # we want.
        sock = socket.socket()


        # Prompt user for info on startup
        username = raw_input("Username: ")
        password = raw_input("Password: ")

        sock.connect((serv_addr, serv_port))

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
except socket.error:
    sock.close()
    exit("Connection failed.")
