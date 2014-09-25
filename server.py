#!/usr/bin/env python
import select
import signal
import socket
import string
import sys
import time

# Ensure graceful exit on CTRL+C
def quit(sig_num, status):
    print("\nServer terminated.")
    exit(0)

def send_to_all(sock, message):
    for x in users:
        if users[x] is not sock:
            try:
                users[x].send(message)
            except socket.error:
                users[x].close()
                users.remove(user)

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

# Make socket non-blocking so it doesn't just wait for new connections.
serv_sock.setblocking(0)

# Make reusing addresses possible
serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind to local host with specified port
serv_sock.bind(("", port))

# Create dictionary for socket storage
users = dict()

# Create dictionary for attempt tracking
attempts = dict()

# Create list for blocked users
blocked = []

# Set socket to listen
status = serv_sock.listen(5)
print("Chat server is listening on port " + str(port))
while True:
    try:
        (clnt_sock, clnt_addr) = serv_sock.accept()
        clnt_sock.settimeout(0.1)
        clnt_ip = clnt_addr[0]

        print("Connection from " + str(clnt_addr))

        if str(clnt_addr) not in blocked:
            clnt_sock.send("AUTHENTICATE\n");
            response = clnt_sock.recv(4096).split("\n")
            if response[0] == "AUTHENTICATE":
                username, password = response[1].split(" ")
                if username in passwords and passwords[username] == password:
                    users[username] = clnt_sock
                    attempts[clnt_ip] = 0
                    clnt_sock.send("JOIN\nWelcome to EasyChat!")
                else:
                    if clnt_ip in attempts:
                        attempts[clnt_ip] += 1
                    else:
                        attempts[clnt_ip] = 1

                    if attempts[clnt_ip] >= 3:
                        blocked.append(clnt_ip)
                        attempts[clnt_ip] = 0
                        clnt_sock.send("BLOCK\nToo many wrong attempts. Blocked.")
                    else:
                        clnt_sock.send("WRONG\nWrong password.")
            else:
                clnt_sock.send("ERROR\nWrong protocol.")
    except socket.error:
        ready, spam, eggs = select.select(users.values(),[],[],0)
        for sock in ready:
            message = sock.recv(4096)
            if message:
                username = users.keys()[users.values().index(sock)]
                neat_message = "\n" + username + ": " + message.strip()
                sys.stdout.write(neat_message)
                send_to_all(sock, neat_message)