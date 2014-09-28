#!/usr/bin/env python
import datetime
import select
import signal
import socket
import string
import sys

# Constant time variables
LAST_HOUR = datetime.timedelta(hours=1)
BLOCK_TIME = datetime.timedelta(seconds=60)
TIME_OUT = datetime.timedelta(minutes=30)

# Create dictionary for usernames and passwords
passwords = dict()

# Create dictionary for socket storage
users = dict()

# Create dictionary for attempt tracking
last_attempt = dict()

# Keeps track of last time user logged out
last_activity = dict()

# Create list for block times for users
block_times = dict()


# Ensure graceful exit on CTRL+C
def quit(sig_num, status):
    print("\nServer terminated.")
    exit(0)


# Find user from socket
def owner(s):
    return users.keys()[users.values().index(s)]


# Check if a user has been logged out in the last hour
def last_hour(username):
    time_since_active = datetime.datetime.now() - last_activity[username]
    return time_since_active < LAST_HOUR


# Check if a user is logged in but idle
def idle(username):
    time_since_active = datetime.datetime.now() - last_activity[username]
    return time_since_active > TIME_OUT and username in users


# Check if a user is currently blocked at a given IP address
def blocked(address, username):
    try:
        time_since_blocked = datetime.datetime.now() - block_times[address][username]
        if time_since_blocked < BLOCK_TIME:
            return True
        else:
            return False
    except KeyError:
        return False


# Authenticate new users
def authenticate(client, address):
    ip = address[0]
    credentials = client.recv(4096)
    username, password = credentials.strip().split(" ")
    if not blocked(ip, username):
        if username in passwords:
            if passwords[username] == password:
                if username not in users:
                    users[username] = client
                    client.send("JOIN\nWelcome to EasyChat!")
                    last_activity[username] = datetime.datetime.now()
                else:
                    client.send("WRONG\nUser is already logged in.")
            else:
                if ip not in last_attempt or last_attempt[ip][0] != username:
                    last_attempt[ip] = [username, 1]
                    client.send("WRONG\nWrong password.")
                else:
                    last_attempt[ip][1] += 1
                    if last_attempt[ip][1] >= 3:
                        client.send("BLOCK\nToo many wrong attempts. Temporarily blocked.")
                        if ip not in block_times:
                            block_times[ip] = dict()
                        block_times[ip][username] = datetime.datetime.now()
                    else:
                        client.send("WRONG\nWrong password.")
        else:
            client.send("WRONG\nInvalid username.")
    else:
        client.send("BLOCK\nYou are currently blocked. Try again later.")


# Send message to all users
def broadcast(source, text):
    text = "\n" + sender + ": " + text
    for u in users:
        if users[u] is not source:
            try:
                users[u].send(text)
            except socket.error:
                users[u].close()
                users.pop(u)


# Send private message
def message(source, destination, text):
    try:
        users[destination].send("\n(private)" + sender + ": " + text)
    except KeyError:
        source.send("\nThat user is not logged in.")
    except socket.error:
        source.send("\nThat user is not available.")
        users[dest].close()
        users.pop(user)

# main method
if __name__ == "__main__":
    signal.signal(signal.SIGINT, quit)

    try:
        port = int(sys.argv[1])
    except (IndexError, ValueError):
        sys.exit("usage: ./server.py <port>")

    # Create dictionary of usernames and passwords
    try:
        user_file = open("user_pass.txt")
    except IOError:
        sys.exit("\"user_pass.txt\" not found.")
    for line in user_file:
        user = string.split(line)
        passwords[user[0]] = user[1]
        last_activity[user[0]] = datetime.datetime.min

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

    # Set socket to listen
    status = serv_sock.listen(5)
    print("Chat server is listening on port " + str(port))
    while True:
        for user in last_activity:
            if idle(user):
                users[user].close()
                users.pop(user)
        ready, spam, eggs = select.select(users.values() + [serv_sock], [], [], 0)
        for sock in ready:
            if sock is serv_sock:
                # Accept new connection
                (clnt_sock, clnt_addr) = serv_sock.accept()
                clnt_sock.settimeout(0.1)
                authenticate(clnt_sock, clnt_addr)
            else:
                try:
                    # Handle new messages
                    data = sock.recv(4096)
                    if data:
                        sender = owner(sock)

                        # Update last activity for the user
                        last_activity[sender] = datetime.datetime.now()

                        l = data.strip("\n").split(" ", 1)
                        command = l[0]

                        # Handle the case where it's there's also a message,
                        # not just a command.
                        if len(l) > 1:
                            text = l[1]

                        if command == "broadcast":
                            broadcast(sock, text)

                        elif command == "message":
                            dest, text = text.split(" ", 1)
                            message(sock, dest, text)

                        elif command == "whoelse":
                            response = "\nLogged in:"
                            for key in users.keys():
                                if key != sender:
                                    response += "\n" + key
                            sock.send(response)

                        elif command == "wholasthr":
                            response = "\nActive in the last hour:"
                            for key in last_activity:
                                if last_hour(key) and key != sender:
                                    response += "\n" + key + " (at " + str(last_activity[key].time())[:5] + ")"
                            sock.send(response)

                        else:
                            sock.send("\nCommand not recognized.")

                    else:
                        # If we get here, client is dead. Log him out.
                        sock.close()
                        users.pop(owner(sock))

                except socket.error:
                    last_activity[owner(sock)] = datetime.datetime.now()
                    sock.close()
                    users.pop(owner(sock))