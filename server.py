#!/usr/bin/env python
import signal
import socket
import string
import sys
import time

# Ensure graceful exit on CTRL+C
def quit(sig_num, status):
    print("\nServer terminated.")
    exit(0)

signal.signal(signal.SIGINT, quit)

try:
    port = int(sys.argv[1])
except (IndexError, ValueError):
    sys.exit("usage: ./server.py <port>")

# Create dictionary of usernames and passwords
passwords = dict()
try:
    user_file = open("user_pass.txt")
except IOError:
    sys.exit("\"user_pass.txt\" not found.")
for line in user_file:
    user = string.split(line)
    passwords[user[0]] = user[1]

# Create socket
# No parameters needed because Python defaults to
# AF_INET and SOCK_STREAM, which are what we want.
serv_sock = socket.socket()

# Make reusing addresses possible
serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind to local host with specified port
serv_sock.bind(("", port))

# Create dictionary for socket storage
sockets = dict()

# Set socket to listen
status = serv_sock.listen(5)
print("Chat server is listening on port " + str(port))
while True:
    (clnt_sock, clnt_addr) = serv_sock.accept()

    print("Connected to " + str(clnt_addr))

    attempts = 0
    loggedin = False
    while not loggedin and attempts < 3:
        # Prompts for username and password
        clnt_sock.send("Username: ")
        username = clnt_sock.recv(4096)
        clnt_sock.send("Password: ")
        password = clnt_sock.recv(4096)

        try:
            if passwords[username] == password:
                loggedin = True
                # Correct user; add him/her
                sockets[username] = clnt_sock
                clnt_sock.send("JOIN\nWelcome to EasyChat!\n")
            else:
                attempts += 1
                if attempts < 3:
                    clnt_sock.send("WRONG\nWrong password.\n")
                else:
                    clnt_sock.send("BLOCK\nToo many wrong attempts. Blocked.\n")
        except KeyError:
            attempts += 1
            if attempts < 3:
                clnt_sock.send("WRONG\nWrong password.\n")
            else:
                clnt_sock.send("BLOCK\nToo many wrong attempts. Blocked.\n")
        time.sleep(1)
