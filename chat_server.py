import socket
from queue import Queue
import json
from json.decoder import JSONDecodeError
from time import sleep
import logging
from datetime import datetime

# set up logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')


class ChatServer:
    def __init__(self, ip="127.0.0.1", port=5000):
        # dict with all clients
        self.clients_connected = {}  # {connection = { ip: <ip> }}
        # queues for incoming/outgoing messages
        self.queue_incoming_messages = Queue()
        self.queue_outgoing_messages = Queue()
        # amount of seconds to wait between checking for new queue messages
        self.queue_poll_time = 0.1
        # amount of seconds to wait when checking received data from client
        self.connection_poll_time = 0.1
        # client timeout, close connection after x seconds
        self.client_timeout = 15
        # hold all queues configured above in this dict
        self.all_queues = [x for x in dir(self) if 'queue' in x if 'messages' in x]
        # dict with all users
        # TODO: make db
        self.user_database = {'teq': {'password': 'teq'}}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((ip, port))
        self.socket.listen(1)

    @staticmethod
    def send_message_to_connection(connection, message_type, message, operation):
        try:
            connection.send(json.dumps({'message_type': message_type, 'message': message, 'operation': operation}).encode())
        except ConnectionResetError:
            pass

    def process_message(self, data):
        """
        This function will contain all valid operations the client can send to us. The function handle_connections
        has already validated the message JSON. Should not be required with any exceptions on syntax.
        :param operation: {'connection', 'message_type', 'operation', 'content'}
        :param message: {}
        :return: { connections: [], message_type: str(), message: str() }
        """
        # set default response to be private and back to connection from which the message came
        response = {'connections': [data['connection']], 'message_type': 'private', 'message': '',
                    'operation': data['operation']}

        # operation authorize_user
        if data['operation'] == 'authorize_user':
            # example client code:
            # {"message_type": "private", "message": {"operation": "authorize_user", "content": {"username": "lobo","password": "lobo"}}}
            # need try block in case encapsulated JSON in "message" key does not contain valid fields
            try:
                msg = data['content']
                if self.db_validate_user(msg['username'], msg['password']):
                    self.clients_connected[data['connection']].update({'username': msg['username']})
                    response['message'] = f"Successfully authorized {msg['username']}"
                else:
                    response['message'] = "Username or password was not correct"
                return response
            except ValueError:
                response['message'] = "Unexpected error E1102"
                return response

        # operation create_user
        if data['operation'] == 'create_user':
            # example client code:
            # {"message_type": "private", "message": {"operation": "create_user", "content": {"username": "lobo","password": "lobo"}}}
            try:
                msg = data['content']
                if not self.db_check_if_duplicate_username(msg['username']):
                    self.db_create_user(msg['username'], msg['password'])
                    response['message'] = f"Successfully created user {msg['username']}"
                else:
                    response['message'] = f"Username '{msg['username']}' already exists"
                return response
            except ValueError:
                response['message'] = "Unexpected error E1101"
                return response
        if data['operation'] == 'list_users':
            users = []
            for c in self.clients_connected.keys():
                try:
                    users.append(self.clients_connected[c]['username'])
                except KeyError:
                    pass
            response['message'] = ','.join(users)
            return response

        # send channel message
        if data['operation'] == 'channel_message':
            t = datetime.now()
            timestamp = f"{t.hour}:{t.minute}:{t.second}"
            user = self.clients_connected[data['connection']]['username']
            response['connections'] = [c for c in self.clients_connected.keys()]
            response['message'] = f"{timestamp} - {user}: {data['content']}"
            return response

    def get_connections(self):
        connection, address = self.socket.accept()
        self.clients_connected.update({connection: {'ip': address}})
        return connection

    def db_create_user(self, username, password):
        self.user_database.update({username: {'password': password}})

    def db_validate_user(self, username, password):
        try:
            if self.user_database[username]['password'] == password:
                return True
        except KeyError:
            return False

    # return true if exists, false if username does not exist
    def db_check_if_duplicate_username(self, username):
        if username in self.user_database:
            return True
        return False

    def insert_outgoing_queue(self, connection, message_type, message):
        self.queue_incoming_messages.put({'connection': connection, 'message_type': message_type, 'message': message})

    def process_outgoing_messages(self):
        while True:
            queue_size = self.queue_outgoing_messages.qsize()
            if queue_size > 0:
                msg = self.queue_outgoing_messages.get()
                self.send_message_to_connection(msg['connection'], msg['message_type'], msg['message'])
            sleep(self.queue_poll_time)

    def insert_incoming_queue(self, connection, message_type, operation, content):
        # add one entry to the queue
        self.queue_incoming_messages.put({'connection': connection,
                                          'message_type': message_type,
                                          'operation': operation,
                                          'content': content})

    def process_incoming_messages(self):
        # see insert_incoming_queue for dict object you get from queue
        while True:
            queue_size = self.queue_incoming_messages.qsize()
            if queue_size > 0:
                # process message on server
                response = self.process_message(self.queue_incoming_messages.get())
                # send processed response back to client. Expect that process message return list of connections.
                for connection in response['connections']:
                    self.send_message_to_connection(connection, response['message_type'], response['message'],
                                                    response['operation'])
            sleep(self.queue_poll_time)

    # This will run for as long as connection is up.
    def handle_connections(self, connection):
        logging.debug(f'Spawning thread for connection: {connection}')
        while True:
            connection.settimeout(self.client_timeout)
            try:
                data = connection.recv(1024).decode()
                client_data = json.loads(data)
                message = client_data['message']
                # check if valid fields are set, except KeyError if not
                _validate_data_fields = client_data['message_type'], client_data['message']
                _validate_message_fields = message['operation'], message['content']
                # if it passed validation put on incoming queue
                self.insert_incoming_queue(connection, client_data['message_type'], message['operation'], message['content'])
            except (ValueError, KeyError, JSONDecodeError):
                self.send_message_to_connection(connection, 'private', 'Server did not undestand your message',
                                                'server_message')
            except (ConnectionResetError, OSError):
                del self.clients_connected[connection]
                exit(1)
            except socket.timeout:
                try:
                    logging.debug(f"User {self.clients_connected[connection]['username']} timed out. Removing")
                except KeyError:
                    pass
                del self.clients_connected[connection]
                exit(1)
            sleep(self.connection_poll_time)
