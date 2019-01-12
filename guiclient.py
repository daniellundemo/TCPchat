import curses
from threading import Thread
import socket
import time
from queue import Queue
from windows import Windows

in_message_queue = Queue()
out_message_queue = Queue()
debug = True

users = []
buffer = []
# TODO placeholder for something else
auth_string = 'auth=teq:teq'


def authenticate(socket, buffer_size=1024):
    while True:
        socket.send(str.encode(auth_string))
        try:
            data = socket.recv(buffer_size)
            if 'OK_CHALLENGE' in str(data):
                return True
        except (ConnectionResetError, OSError):
            socket.close()
            return False


def connect_socket(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, port))
    if not authenticate(s):
        s.close()
        return False
    else:
        # start receiver thread
        t = Thread(target=receive_data_thread, args=(s,))
        t.setDaemon(True)
        t.start()
        # start sender thread
        t = Thread(target=send_data_thread, args=(s,))
        t.setDaemon(True)
        t.start()


def receive_data_thread(s, buffer_size=1024):
    while True:
        try:
            data = s.recv(buffer_size)
            in_message_queue.put(data)
        except (ConnectionResetError, OSError):
            s.close()
            return 1


def send_data_thread(socket):
    while True:
        if not out_message_queue.empty():
            socket.send(out_message_queue.get())
        time.sleep(1)


def refresh_chat_window():
    t = Thread(target=refresh_chat_window_thread)
    t.setDaemon(True)
    t.start()


def refresh_chat_window_thread():
    h, w = windows.channel_window.getmaxyx()
    while True:
        if not in_message_queue.empty():

            buffer.append(in_message_queue.get())
            messages = buffer
            messages.reverse()
            counter = 1
            for message in messages:
                m = str(message)
                counter += 1
                if '[SERVER]' in m:
                    windows.channel_window.addstr(h - counter, 1, m, curses.color_pair(1))
                else:
                    windows.channel_window.addstr(h - counter, 1, m)
                if counter > 20:
                    break
            windows.channel_window.refresh()

        if debug:
            print("in_message_queue: {}".format(in_message_queue.qsize()))
            print("buffer length: {}".format(len(buffer)))
        time.sleep(0.5)


def parse_commands(byte_msg):

    if '/' not in str(byte_msg):
        message = b"[msg]=" + byte_msg
        out_message_queue.put(message)
    if '/quit' in str(byte_msg):
        print('Bye.')
        exit(1)


def get_input():
    while True:
        h, w = windows.text_window.getmaxyx()
        try:

            new_msg = windows.text_window.getstr(h - 2, w - w + 3, 90)
            parse_commands(new_msg)
            windows.refresh_text_window()

        except KeyboardInterrupt:
            print('Bye.')
            exit(1)


if __name__ == "__main__":
    windows = Windows(curses.initscr())  # draw curses windows
    refresh_chat_window()                # spawn a thread to keep chat window updated
    connect_socket('127.0.0.1', 5000)    # spawn two thread connections, one sender, one receiver
    get_input()                          # loop waiting for user input
