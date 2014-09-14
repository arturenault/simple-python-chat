#!/usr/bin/python
import string

passwords = dict()
user_file = open("user_pass.txt")
for line in user_file:
    user = string.split(line)
    passwords[user[0]] = user[1]
