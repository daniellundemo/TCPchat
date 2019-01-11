import curses
from threading import Thread
import socket
import time
from queue import Queue

message_queue = Queue()

def my_input(stdscr):
    curses.echo()
    stdscr.addstr(27, 2, '--------------------------------------------------------------------------------------------')
    stdscr.addstr(28, 2, '[0]')
    stdscr.addstr(29, 2, '--------------------------------------------------------------------------------------------')
    stdscr.refresh()
    input = stdscr.getstr(28, 6, 18)
    return input  #


def start_thread(ip, port):
    t = Thread(target=connect_socket, args=(ip, port))
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
        print("received data:", data)
        time.sleep(1)


def parse_commands(cmds):
    stdscr.refresh()
    if not '/' in cmds:
        cmds = '[msg]' + cmds
    if '[msg]' in cmds:
        message_queue.put(cmds)
    if '/quit' in cmds:
        print('Bye.')
        exit(1)


if __name__ == "__main__":
    start_thread('127.0.0.1', 5000)
    stdscr = curses.initscr()
    display_list = []
    while True:
        try:
            stdscr.clear()
            parse_commands(str(my_input(stdscr)))
            pop_display()
            stdscr.getch()
        except KeyboardInterrupt:
            print('Bye.')
            exit(1)
