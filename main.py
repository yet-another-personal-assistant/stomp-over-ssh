#!/usr/bin/env python3
import argparse
import configparser
import logging
import json
import os
import sys
import random
import time

import paramiko
import stomp

from sshstomp import Connection, SshBasedTransport


_LOGGER = logging.getLogger(__name__)


class KeepAlivesFilter:
    def filter(self, record):
        return 'keepalive@' not in record.msg


def setup_logging(level, logfile):
    paramiko.util.get_logger('paramiko.transport').addFilter(KeepAlivesFilter())
    log_format = "%(asctime)-8s:%(levelname)5s:%(name)s: %(message)s"
    logging.basicConfig(stream=sys.stderr,
                        level=level,
                        format=log_format,
                        datefmt="%H:%M:%S")
    if logfile is not None:
        handler = logging.FileHandler(logfile)
        handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger('').addHandler(handler)


class MyListener(stomp.ConnectionListener):

    def __init__(self, conn):
        self.conn = conn
        self.done = False

    def on_error(self, headers, message):
        print('received an error', message)

    def on_connected(self, headers, message):
        print('connected')
        self.conn.subscribe('brain', id=1)

    def on_message(self, headers, message):
        print('received a message', message)
        msg = json.loads(message)
        if msg['from']['channel'] == 'tg':
            sender = f"tg:{msg['from']['user_id']}"
        else:
            sender = msg['from']['channel']
        print(f"Message from {sender}:", msg['text'])

        if msg['from']['channel'] == 'tg':
            if msg['from']['user_id'] == msg['from']['chat_id']: # private message
                self.conn.send(body=make_message(["Я не поняла",
                                                  f"А что значит \"{msg['text']}\"?"]),
                               destination='tg')

    def on_disconnected(self):
        print('disconnected')
        if not self.done:
            _LOGGER.info('sleep 5')
            time.sleep(5)
            self.conn.connect()
            self.conn.send(body=make_message(random.choice(["Ой, что-то поломалось",
                                                            "Тут что-то сломалось",
                                                            "Кажется, связь моргнула"])),
                           destination='tg')


_CHAT_ID = None


def make_message(text, chat_id=None):
    if chat_id is None:
        chat_id = _CHAT_ID
    return json.dumps({"from": {"channel": "brain", "name": "niege"},
                       "to": {"channel": "tg", "chat_id": chat_id},
                       "text": text})


def set_message_chat_id(chat_id):
    global _CHAT_ID
    _CHAT_ID = chat_id


def process_config(args):
    config_file = args.config or "/etc/sshstomp/sshstomp.conf"
    config_file = os.path.expanduser(config_file)

    config = configparser.ConfigParser()
    if os.path.exists(config_file):
        config.read(config_file)
        config = config['sshstomp']
    else:
        config.read_dict({})

    log_file = args.log_file or config.get('log-file')
    if args.debug or config.getboolean('debug', fallback=False):
        setup_logging(logging.DEBUG, log_file)
    else:
        setup_logging(logging.INFO, log_file)

    host = args.host or config['host']
    port = args.port or config.getint('port')
    user = args.user or config['user']
    keyfile = os.path.expanduser(args.key or config['key'])
    chat_id = args.chat_id or config['chat-id']
    set_message_chat_id(chat_id)
    return host, port, user, keyfile


def main(args):
    host, port, user, keyfile = process_config(args)
    transport = SshBasedTransport(host, port, user, keyfile)
    conn = Connection(transport, heartbeats=(120000,180000))
    listener = MyListener(conn)
    conn.set_listener('', listener)
    conn.connect()
    conn.send(body=make_message("я тут"), destination='tg')
    while True:
        try:
            time.sleep(3600+random.randint(-600, 600))
            text = random.choice(["Привет",
                                  "Ой, приветик",
                                  "Чем занят?",
                                  "Мне скучно"])
            conn.send(body=make_message(text), destination='tg')
        except KeyboardInterrupt:
            break
    listener.done = True
    conn.disconnect()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-h', '--host')
    parser.add_argument('-p', '--port', type=int)
    parser.add_argument('-k', '--key')
    parser.add_argument('-u', '--user')
    parser.add_argument('--chat-id', type=int)
    parser.add_argument('-c', '--config')
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-o', '--log-file')

    args = parser.parse_args()

    main(args)
