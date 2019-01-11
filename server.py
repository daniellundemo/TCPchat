#!/usr/bin/env python

import socket
import time
from threading import Thread
from queue import Queue

message_queue = Queue(maxsize=200000)
database = ['teq:teq']


def socket_in(ip='127.0.0.1', port=5000, buffer_size=1024):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ip, port))
    s.listen(1)
    id = 0
    while True:
        id += 1
        conn, addr = s.accept()
        t = Thread(target=in_thread, args=(conn, addr, id))
        t.setDaemon(True)
        t.start()


# def socket_out(ip='127.0.0.1', port=5001, buffer_size=1024):
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     s.bind((ip, port))
#     s.listen(1)
#     while True:
#         conn, addr = s.accept()
#         t = Thread(target=out_thread, args=(s, conn, addr))
#         t.setDaemon(True)
#         t.start()


def in_thread(conn, addr, id, counter=0, auth=0):
    print("Started thread {} with {} {}".format(id, conn, addr))
    while 1:
        # challenge password
        while auth == 0:
            conn.send(b'[out] ping')
            counter += 1
            data = conn.recv(1024).decode("utf-8").split("\n")
            print(data)
            if counter == 5:
                conn.send(b'unable to authenticate\n')
                conn.close()
                return 1
            if 'auth' in str(data):
                for line in data:
                    if 'auth' in line:
                        check = challenge(line)
                        print("CHECK DEBUG:", check)
                        if check:
                            conn.send(b'OK_CHALLENGE\n')
                            auth = 1
                        else:
                            conn.send(b'user and pass not in database\n')
                            conn.close()
                            return 1

        data = conn.recv(1024)
        if not data:
            break

        try:
            # tcp keepalive
            conn.send(b'[out] ping\n')
            print("{} - {}".format(conn, addr))
        except ConnectionResetError:
            return 0
        time.sleep(1)
    conn.close()


# def out_thread(conn, addr):
#     while 1:
#         conn.send(b'[out] pong')
#         time.sleep(1)


def challenge(string):
    userpass = string.split("=")[1]
    print("USERPASS:", userpass, database)
    if userpass not in str(database):
        return False
    else:
        return True


def main():
    t = Thread(target=socket_in)
    t.setDaemon(True)
    t.start()

    # t = Thread(target=socket_out)
    # t.setDaemon(True)
    # t.start()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print('Bye.')
            exit(1)


main()
