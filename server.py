#!/usr/bin/env python

import socket
import time
from threading import Thread
from queue import Queue

message_queue = Queue(maxsize=200000)
connections_queue = Queue(maxsize=10000)
database = ['teq:teq']
debug = True


def socket_thread(ip='127.0.0.1', port=5000):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((ip, port))
    sock.listen(1)
    id = 0
    while True:
        id += 1
        conn, addr = sock.accept()
        connections_queue.put(conn)
        if debug:
            print("[DEBUG] - There are {} connections".format(connections_queue.qsize()))
        t = Thread(target=connection_thread, args=(conn, addr, id))
        t.setDaemon(True)
        t.start()


def send_message(connection, message):
    connection.send(message)


def update_clients():
    while True:
        if not message_queue.empty():
            queue = connections_queue
            conn = queue.get()
            for message in message_queue.get():
                t = Thread(target=send_message, args=(conn, message))
                t.setDaemon(True)
                t.start()


def connection_thread(conn, addr, id):
    if debug:
        print("[DEBUG] - [Thread id {}] - New connection from {}".format(id, addr))
    # challenge user and password
    if not challenge_user(conn):
        conn.close()
        return False
    if debug:
        print("[DEBUG] - User challenged OK")
    while 1:
        try:
            if debug:
                print("[DEBUG] - [Thread id {}] - Waiting for response".format(id))
            data = conn.recv(1024)
            if debug:
                print("[DEBUG] - [Thread id {}] - Got response response: {}".format(id, str(data)))
            if '[msg]' in data:
                message_queue.put(data)
            else:
                conn.send(b'[SERVER]: Could not understand message')
        except (ConnectionResetError, OSError):
            print("[DEBUG] - [Thread id {}] - Closing connection".format(id))
            connections_queue.get(conn)
            conn.close()
            return 1


def challenge_user(conn, counter=0):
    while True:
        data = conn.recv(1024).decode("utf-8").split("\n")
        counter += 1
        if counter == 5:
            conn.send(b'[SERVER] unable to authenticate you, closing connection...\n')
            conn.close()
            return False
        # TODO: Store users somewhere
        if 'auth' in str(data):
            if debug:
                print("[DEBUG] - Trying to authenticate user", str(data))
            for line in data:
                if 'auth' in str(line):
                    userpass = line.split("=")[1]
                    if debug:
                        print("[DEBUG] - Got userpass:", userpass)
                    if userpass not in str(database):
                        conn.send(b'[SERVER] wrong username or password, closing connection...\n')
                        conn.close()
                        return False
                    else:
                        return True


def main():
    t = Thread(target=socket_thread)
    t.setDaemon(True)
    t.start()

    t = Thread(target=update_clients)
    t.setDaemon(True)
    t.start()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print('Bye.')
            exit(1)


main()
