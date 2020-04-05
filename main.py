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
        handler = logging.FileHandler(os.path.expanduser(logfile))
        handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger('').addHandler(handler)


class MyListener(stomp.ConnectionListener):

    def __init__(self, conn, chat_id):
        self.conn = conn
        self.done = False
        self.chat_id = chat_id

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
                                                  f"А что значит \"{msg['text']}\"?"],
                                                 chat_id=msg['from']['chat_id']),
                               destination='tg')

    def on_disconnected(self):
        print('disconnected')
        if not self.done:
            _LOGGER.info('sleep 5')
            time.sleep(5)
            self.conn.connect()
            self.conn.send(body=make_message(random.choice(["Ой, что-то поломалось",
                                                            "Тут что-то сломалось",
                                                            "Кажется, связь моргнула"]),
                                             chat_id=self.chat_id),
                           destination='tg')


def make_message(text, chat_id):
    return json.dumps({"from": {"channel": "brain", "name": "niege"},
                       "to": {"channel": "tg", "chat_id": chat_id},
                       "text": text})


def coalesce(x1, x2):
    return x2 if x1 is None else x1


def get_config(config_file_arg):
    config_file = os.path.expanduser(config_file_arg)

    config = configparser.ConfigParser()
    if os.path.exists(config_file):
        config.read(config_file)
    else:
        config.read_dict({'sshstomp':{}})

    return config['sshstomp']


def process_config(args):
    config = get_config(args.config)

    log_file = coalesce(args.log_file, config.get('log-file', fallback=None))
    if coalesce(args.debug, config.getboolean('debug', fallback=False)):
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    setup_logging(log_level, log_file)

    host = coalesce(args.host, config.get('host'))
    port = coalesce(args.port, config.getint('port'))
    user = coalesce(args.user, config.get('user'))
    keyfile = os.path.expanduser(coalesce(args.key, config.get('key')))
    chat_id = coalesce(args.chat_id, config.getint('chat-id'))
    return host, port, user, keyfile, chat_id


def main(args):
    host, port, user, keyfile, owner = process_config(args)
    transport = SshBasedTransport(host, port, user, keyfile)
    conn = Connection(transport, heartbeats=(120000,180000))
    listener = MyListener(conn, owner)
    conn.set_listener('', listener)
    conn.connect()
    conn.send(body=make_message("я тут", chat_id=owner), destination='tg')
    while True:
        try:
            time.sleep(3600+random.randint(-600, 600))
            text = random.choice(["Привет",
                                  "Ой, приветик",
                                  "Чем занят?",
                                  "Мне скучно"])
            conn.send(body=make_message(text, chat_id=owner),
                      destination='tg')
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
    parser.add_argument('-c', '--config', default="/etc/sshstomp/sshstomp.conf")
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-o', '--log-file')

    args = parser.parse_args()

    main(args)
