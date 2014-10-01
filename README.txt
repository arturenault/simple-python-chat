README.txt
Computer Networks Lab 1
Artur Upton Renault

This is the README for EasyChat, a simple chat program written in Python. It was developed using PyCharm as an IDE, revision controlled using git, and tested on my machine, a Mac OS X Mavericks running python 2.7.8, as well as the CLIC lab.

The program includes two different files, Server.py and Client.py; the names are self-explanatory.

Server.py contains the server program. It listens on the given port and waits for connections. Upon a new connection it authenticates the user according to the user_pass.txt file; it does not allow concurrent duplicate users and will block a user at a given IP address for 60 seconds after three consecutive failed attempts to log into that user from that IP address. It can be executed with "python Server.py <port#>" or simply "./Server.py <port#>" if the file is made executable.
Client.py handles the user's interface with the chat application. It sends the client's credentials to the server to authenticate him or her. After that, it prints out all messages received from the server and sends all commands to the server. There is one exception to this; the "logout" command is handled by the client itself, and the server handles it independently as it would a client that has quit using CTRL+C. IT can be executed with "python Client.py <server host> <#port>" or "./Client.py <server host> <#port>" if Client.py is made executable.

The following commands are available to the user once logged into the server:
whoelse: prints out names of other connected users
wholasthr: prints names of users that have been active in the past hour and the time they were last seen.
lastseen: prints out the time at which each user was last seen.
broadcast <message>: sends <message> to all other users.
message <user> <message>: sends a private message to a user.
help: display available commands
logout: log out the user (handled by client)

Additional functionalities:
help: Help command displays available commands (minor)
lastseen: Prints out when the user was last active in the app (minor, extended from wholasthr)
offline messaging: users that that are not online will receive all their messages in a dictionary for that purpose. When they log in, they will receive all the messages along with the user who sent each one and at what time. Unfortunately this does not handle.