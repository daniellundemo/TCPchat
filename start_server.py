#!/usr/bin/env python

from chat_server import ChatServer
from threading import Thread
import logging


def main():
    # set up logger
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')

    # initalize chat server instance
    logging.debug("Initialize chat server")
    server = ChatServer()

    # set up handler for processing outgoing messages
    # TODO: add support for more threads, only necessary if heavy load. So probably will never do this.
    logging.debug(f"Setting up handler for processing outgoing messages")
    t = Thread(target=server.process_outgoing_messages)
    t.setDaemon(True)
    t.start()

    # set up handler for processing outgoing messages
    # TODO: add support for more threads, only necessary if heavy load. So probably will never do this.
    logging.debug(f"Setting up handler for processing incoming messages")
    t = Thread(target=server.process_incoming_messages)
    t.setDaemon(True)
    t.start()

    # spawn a thread to handle send/recv for each connection we receive
    while True:
        try:
            # handle_connections waits for new connections, if the function returns we create a thread to handle
            # the new connection. Then we wait for another one.
            t = Thread(target=server.handle_connections, args=(server.get_connections(),))
            t.setDaemon(True)
            t.start()
        except KeyboardInterrupt:
            print('Bye.')
            exit(1)


main()
