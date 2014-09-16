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

    # Send username after server prompt
    sock.send(raw_input(sock.recv(4096)))

    # Send password after server prompt
    sock.send(raw_input(sock.recv(4096)))

    # Receive welcome message or rejection
    print(sock.recv(4096))
except socket.error:
    sock.close()
    exit("Connection failed.")
