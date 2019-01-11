#!/usr/bin/env python

import socket
import time
TCP_IP = '127.0.0.1'
TCP_PORT = 5000
BUFFER_SIZE = 1024
MESSAGE = b"ping"
AUTH = b"auth=teq:teq\n"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))


auth = 0
while True:
    while auth == 0:
        s.send(AUTH)
        s.send(MESSAGE)
        data = s.recv(BUFFER_SIZE)
        print("received data:", data)
        if 'OK_CHALLENGE' in data.decode('utf-8'):
            auth = 1
    s.send(MESSAGE)
    data = s.recv(BUFFER_SIZE)
    print("received data:", data)
    time.sleep(1)

