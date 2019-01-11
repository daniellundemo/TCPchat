import curses
from threading import Thread
import socket
import time
from queue import Queue

in_message_queue = Queue()
out_message_queue = Queue()

buffer = []

stdscr = curses.initscr()
display_window = curses.newwin(5, self.scr_height - 1, 5, 10)
scr_height, width = self.scr.getmaxyx()

def print_bot():
    x = 2
    while x < 118:
        stdscr.addstr(27, x, '-')
        stdscr.addstr(29, x, '-')
        x += 1
    stdscr.addstr(28, 2, '[0] ')


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
            s.send(b'auth=teq:teq\n')
            s.send(b'ping\n')
            data = s.recv(buffer_size)
            print("received data:", data)
            if 'OK_CHALLENGE' in data.decode('utf-8'):
                auth = 1
        s.send(b'ping\n')
        # send data
        text = message_queue.get()
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
    start_pos = 26
    while True:
        if not in_message_queue.empty():

            buffer.append(in_message_queue.get())

            messages = buffer
            messages.reverse()
            counter = 0
            stdscr.erase()
            for message in messages:
                counter += 1
                stdscr.addstr(start_pos - counter, 2, message)
                if counter == 20:
                    break
            print_bot()
            stdscr.refresh()


if __name__ == "__main__":
    print_bot()
    socket_thread('127.0.0.1', 5000)
    display_thread()

    while True:
        try:
            key = stdscr.getch()
            if key == 10 or key == 13:
                print("KEY", key)
                new_msg = stdscr.getstr(28, 6, 90)
                parse_commands(str(new_msg))
                print_bot()

        except KeyboardInterrupt:
            print('Bye.')
            exit(1)
