#!/usr/bin/env python3
import argparse
import logging
import json
import os
import sys
import random
import time

import paramiko
import stomp

from sshstomp import SshBasedConnection


_LOGGER = logging.getLogger(__name__)


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


class KeepAlivesFilter:
    def filter(self, record):
        return 'keepalive@' not in record.msg


def set_message_chat_id(chat_id):
    global _CHAT_ID
    _CHAT_ID = chat_id


def main(host, port, user, keyfile):
    conn = SshBasedConnection(host, port, user, keyfile,
                              heartbeats=(120000,180000))
    listener = MyListener(conn)
    conn.set_listener('', listener)
    conn.connect()
    conn.send(body=make_message("я тут"), destination='tg')
    while True:
        try:
            time.sleep(600+random.randint(-120, 120))
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
    parser.add_argument('-h', '--host', required=True)
    parser.add_argument('-p', '--port', required=True, type=int)
    parser.add_argument('-k', '--key', required=True)
    parser.add_argument('-u', '--user', required=True)
    parser.add_argument('-c', '--chat-id', required=True, type=int)
    logging.basicConfig(stream=sys.stderr,
                        level=logging.DEBUG,
                        format="%(asctime)-8s:%(levelname)5s:%(name)s: %(message)s",
                        datefmt="%H:%M:%S")
    paramiko.util.get_logger('paramiko.transport').addFilter(KeepAlivesFilter())
    handler = logging.FileHandler('my_stomp.log')
    handler.setFormatter(logging.Formatter("%(asctime)-8s:%(levelname)5s:%(name)s: %(message)s"))
    logging.getLogger('').addHandler(handler)

    args = parser.parse_args()

    set_message_chat_id(args.chat_id)

    main(args.host, args.port, args.user, os.path.expanduser(args.key))
