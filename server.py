#!/usr/bin/env python

"""
Server.py: the server for EasyChat.
A simple chat application for CSEE W4119 Computer Networks.
by Artur Upton Renault (aur2103)

"""

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
users = dict()

# Create dictionary for socket storage
online = dict()

# Create dictionary for attempt tracking
last_attempt = dict()

# Keeps track of last time user logged out
last_activity = dict()

# Create list for block times for users
block_times = dict()

# Create buffers for offline messages
offline_messages = dict()

# Ensure graceful exit on CTRL+C
def quit(sig_num, status):
    print("\nServer terminated.")
    exit(0)


# Find user from socket
def owner(s):
    return online.keys()[online.values().index(s)]


# Check if a user has been logged out in the last hour
def last_hour(username):
    time_since_active = datetime.datetime.now() - last_activity[username]
    return time_since_active < LAST_HOUR


# Check if a user is logged in but idle
def idle(username):
    time_since_active = datetime.datetime.now() - last_activity[username]
    return time_since_active > TIME_OUT and username in online


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
    try:
        username, password = credentials.strip().split(" ")
    except ValueError:
        client.send("WRONG\nAuthentication error.")
        return
    if not blocked(ip, username):
        if username in users:
            if users[username] == password:
                if username not in online:

                    # Successful authentication
                    online[username] = client
                    client.send("JOIN\nWelcome to EasyChat!\n"
                                "--------------------------------------------------------\n")
                    last_activity[username] = datetime.datetime.now()
                    if ip in last_attempt:
                        last_attempt.pop(ip)
                    if offline_messages[username]:
                        # Send offline messages
                        client.send("What you missed:\n" +
                        offline_messages[username] +
                        "--------------------------------------------------------\n")
                        offline_messages[username] = ""
                else:

                    # Prevent concurrent duplicate users
                    client.send("WRONG\nUser is already logged in.")
            else:
                if ip not in last_attempt or last_attempt[ip][0] != username:

                    # Keep track of last failed attempt by this ip address
                    last_attempt[ip] = [username, 1]
                    client.send("WRONG\nWrong password.")
                else:

                    # Block users
                    last_attempt[ip][1] += 1
                    if last_attempt[ip][1] >= 3:
                        client.send("BLOCK\nToo many wrong attempts. Temporarily blocked.")
                        if ip not in block_times:
                            block_times[ip] = dict()
                        block_times[ip][username] = datetime.datetime.now()
                        last_attempt.pop(ip)
                    else:
                        client.send("WRONG\nWrong password.")
        else:
            client.send("WRONG\nInvalid username.")
            if ip in last_attempt:
                last_attempt.pop(ip)
    else:
        client.send("BLOCK\nYou are currently blocked. Try again later.")


# Send message to all users
def broadcast(source, text):
    formatted_text = sender + ": " + text + "\n"
    for u in users:
        if u in online:
            if online[u] is not source:
                try:
                    online[u].send(formatted_text)
                except socket.error:
                    online[u].close()
                    online.pop(u)
        else:
            offline_messages[u] += ("(" +
                                    str(datetime.datetime.now().time())[:5] +
                                    ") " +
                                    formatted_text)


# Send private message
def message(source, destination, text):
    formatted_text = owner(source) + " (private): " + text + "\n"
    if destination in online:
        online[destination].send(formatted_text)
    else:
        offline_messages[destination] += ("(" +
                        str(datetime.datetime.now().time())[:5] +
                        ") " +
                        formatted_text)

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

        # Initialize all info about users
        user = string.split(line)
        users[user[0]] = user[1]
        last_activity[user[0]] = datetime.datetime.min
        offline_messages[user[0]] = ""

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
    print("Chat server is listening at " +
          socket.gethostbyname(socket.gethostname()) +
          ":" + str(port))
    while True:
        for user in last_activity:
            if idle(user):
                online[user].close()
                online.pop(user)
        ready, spam, eggs = select.select(online.values() + [serv_sock], [], [], 0)
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
                        try:
                            sender = owner(sock)

                            # Update last activity for the user
                            last_activity[sender] = datetime.datetime.now()

                            list = data.strip("\n").split(" ", 1)
                            command = list[0]
                            command = command.lower()

                            # Handle the case where it's there's also a message,
                            # not just a command.
                            text = ""
                            if len(list) > 1:
                                text = list[1]

                            if command == "broadcast":
                                if not text:
                                    raise ValueError
                                broadcast(sock, text)

                            elif command == "message":
                                dest, text = text.split(" ", 1)
                                message(sock, dest, text)

                            elif command == "whoelse":
                                response = ("Logged in:\n"
                                            "--------------------------------------------------------\n")
                                for key in online.keys():
                                    if key != sender:
                                        response += key + "\n"
                                response += "--------------------------------------------------------\n"
                                sock.send(response)

                            elif command == "wholasthr":
                                response = ("Active in the last hour:\n"
                                            "--------------------------------------------------------\n")
                                for key in last_activity:
                                    if last_hour(key) and key != sender:
                                        response += (key + " (at " + str(last_activity[key].time())[:5] + ")\n")
                                response += "--------------------------------------------------------\n"
                                sock.send(response)

                            elif command == "lastseen":
                                response = ("Time last seen:\n"
                                            "--------------------------------------------------------\n")
                                for user in last_activity:
                                    if last_activity[user] != datetime.datetime.min and user != owner(sock):
                                        response += user + ": " + str(last_activity[user].time())[:5] + "\n"
                                    else:
                                        response += user + ": never\n"
                                response += "--------------------------------------------------------\n"
                                sock.send(response)
                            elif command == "help":

                                # Help menu
                                response = ("Available commands:\n"
                                            "--------------------------------------------------------\n"
                                            "whoelse: list other online users\n"
                                            "wholasthr: list users active in the past hour\n"
                                            "lastseen: prints time at which users were last seen\n"
                                            "broadcast <message>: send <message> to all other users\n"
                                            "message <user> <message>: send <message> to <user>\n"
                                            "logout: logout of chat\n"
                                            "help: get list of available commands\n"
                                            "--------------------------------------------------------\n")
                                sock.send(response)
                            else:

                                # Unrecognized command.
                                sock.send("Invalid command.\n")

                        except ValueError:
                            # Handle the case where a user sends a command with a missing message,
                            # e.g. "broadcast"
                            sock.send("Invalid command.\n")
                        except KeyError:
                            # Invalid username
                            sock.send("Invalid user.\n")
                    else:
                        # If we get here, client is dead. Log him out.
                        sock.close()
                        online.pop(owner(sock))

                except socket.error:
                    # Handle all problems with user sockets: just log them out.
                    last_activity[owner(sock)] = datetime.datetime.now()
                    sock.close()
                    online.pop(owner(sock))