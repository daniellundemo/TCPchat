import curses
from threading import Thread
import socket
import time
from queue import Queue

in_message_queue = Queue()
out_message_queue = Queue()

users = []
buffer = []
# TODO placeholder for something else
auth_string = 'auth=teq:teq'

# init screen
stdscr = curses.initscr()
w_height, w_width = stdscr.getmaxyx()

# init colors
curses.start_color()
curses.use_default_colors()
curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_BLACK)
curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)

# header window
header = curses.newwin(1, 40, 0, 1)
header.addstr(0, 1, 'chat client by teQ')
header.refresh()

# channel window
channel_window = curses.newwin(w_height - 4, w_width - 15, 1, 0)
channel_window.border()
channel_window.refresh()

# users window
users_window = curses.newwin(0, 15, 1, w_width - 15)
users_window.border()
users_window.refresh()

# input text window
text_window = curses.newwin(3, w_width - 15, w_height - 3, 0)


def refresh_input():
    h, w = text_window.getmaxyx()
    text_window.clear()
    text_window.border()
    text_window.addstr(h - 2, w - w + 2, '> ')
    text_window.refresh()


def socket_thread(ip, port):
    t = Thread(target=connect_socket, args=(ip, port))
    t.setDaemon(True)
    t.start()


def display_thread():
    t = Thread(target=pop_display)
    t.setDaemon(True)
    t.start()


def connect_socket(ip, port, buffer_size=1024):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, port))
    auth = 0
    while True:
        while auth == 0:
            s.send(str.encode(auth_string))
            data = s.recv(buffer_size)
            in_message_queue.put(data)
            if 'OK_CHALLENGE' in data.decode('utf-8'):
                auth = 1
        # send data
        text = out_message_queue.get()
        if text:
            s.send(str.encode(text) + b"\n")

        # receieve data
        data = s.recv(buffer_size)
        in_message_queue.put(data)
        time.sleep(1)


def parse_commands(cmds):
    if not '/' in cmds:
        cmds = '[msg]°' + cmds
    if '[msg]' in cmds:
        s = cmds.split("°")[1]
        out_message_queue.put(s)
    if '/quit' in cmds:
        print('Bye.')
        exit(1)


def pop_display():
    h, w = channel_window.getmaxyx()
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
                    channel_window.addstr(h - counter, 1, m, curses.color_pair(1))
                else:
                    channel_window.addstr(h - counter, 1, m)
                if counter > 20:
                    break
            channel_window.border()
            channel_window.refresh()
            refresh_input()


def get_input():
    while True:
        h, w = text_window.getmaxyx()
        try:
            refresh_input()
            new_msg = text_window.getstr(h - 2, w - w + 3, 90)
            parse_commands(str(new_msg))
            text_window.erase()

        except KeyboardInterrupt:
            print('Bye.')
            exit(1)


if __name__ == "__main__":
    socket_thread('127.0.0.1', 5000)
    display_thread()
    get_input()
