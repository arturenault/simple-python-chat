#!/usr/bin/env python
import sys
import socket

# Get address and port from command line
try:
    serv_addr = socket.gethostbyname(sys.argv[1])
    serv_port = int(sys.argv[2])
except IndexError, TypeError:
    exit("usage: ./Client.py <server_host> <server_port>")

# Create socket
# No need for arguments because the defaults,
# socket.AF_INET and socket.SOCK_STREAM are what
# we want.
sock = socket.socket()

try:
    sock.connect((serv_addr, serv_port))

    while True:
        # Send username after server prompt
        sock.send(raw_input(sock.recv(4096)))

        # Send password after server prompt
        sock.send(raw_input(sock.recv(4096)))

        # Receive welcome message or rejection
        response = sock.recv(4096).split("\n")
        print(response[1])

        if response[0] == "JOIN":
            break
        elif response[0] == "WRONG":
            continue
        elif response[0] == "BLOCK":
            sock.close()
            exit(1)
except socket.error:
    sock.close()
    exit("Connection failed.")
