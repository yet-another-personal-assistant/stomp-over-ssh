#!/usr/bin/env python3
import logging
import socket
import sys
import time

import stomp


_LOGGER = logging.getLogger(__name__)


class UnixSocketTransport(stomp.transport.BaseTransport):

    def __init__(self, sockname):
        super().__init__()
        self.socket = None
        self.current_host_and_port = sockname
        self.vhost = f'localhost'
        self.connected = False

    def is_connected(self):
        return self.connected

    def disconnect_socket(self):
        _LOGGER.info("disconnect socket is called")
        self.socket.close()

    def send(self, encoded_frame):
        if not self.connected:
            raise stomp.exception.NotConnectedException()
        return self.socket.sendall(encoded_frame)

    def receive(self):
        result = self.socket.recv(1024)
        _LOGGER.debug("Got %s", result)
        return result

    def cleanup(self):
        _LOGGER.info("cleanup called")
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.detach()
        self.connected = False

    def attempt_connection(self):
        if self.socket is not None:
            _LOGGER.info("closing old socket")
            self.socket.close()
        self.socket = socket.socket(socket.AF_UNIX)
        _LOGGER.info("connecting")
        self.socket.connect(self.current_host_and_port)
        self.connected = True

    def set_ssl(self,
                for_hosts=[],
                key_file=None,
                cert_file=None,
                ca_certs=None,
                cert_validator=None,
                ssl_version=None,
                password=None):
        pass

    def get_ssl(self, host_and_port=None):
        return None


class UnixSocketConnection(stomp.connect.StompConnection12):
    def __init__(self,
                 sockname,
                 heartbeats=(0, 0),
                 auto_content_length=True,
                 heart_beat_receive_scale=1.5):
        transport = UnixSocketTransport(sockname)
        stomp.connect.BaseConnection.__init__(self, transport)
        stomp.protocol.Protocol12.__init__(self, transport, heartbeats, auto_content_length,
                                           heart_beat_receive_scale=heart_beat_receive_scale)


class MyListener(stomp.ConnectionListener):

    def __init__(self, conn, pub, sub):
        super().__init__()
        self.conn = conn
        self.done = False
        self.pub = pub
        self.sub = sub
        self.queue = []

    def on_error(self, headers, message):
        _LOGGER.info('received an error %s', message)

    def on_connected(self, headers, message):
        _LOGGER.info('connected')
        self.conn.subscribe(self.sub, id=1)
        while self.queue:
            item = self.queue.pop(0)
            try:
                self.conn.send(body=item, destination=self.pub)
            except:
                self.queue.insert(0, item)

    def on_message(self, headers, message):
        _LOGGER.info('received a message %s', message)

    def on_disconnected(self):
        _LOGGER.info('disconnected')
        if not self.done:
            _LOGGER.info('sleep 5')
            time.sleep(5)
            self.queue.append("reconnect")
            self.conn.connect()


def main():
    conn = UnixSocketConnection("/tmp/xtomp.sock", heartbeats=(120000,75000))
    listener = MyListener(conn, 'memq', 'memq')
    listener.queue.append('ping')
    conn.set_listener('', listener)
    conn.connect()
    while True:
        try:
            time.sleep(240)
#            conn.send(body='ping', destination='memq')
        except KeyboardInterrupt:
            break
    listener.done = True
    conn.disconnect()


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr,
                        level=logging.DEBUG,
                        format="%(asctime)-8s:%(levelname)5s:%(name)s: %(message)s",
                        datefmt="%H:%M:%S")
    handler = logging.FileHandler('heartbeat.log')
    handler.setFormatter(logging.Formatter("%(asctime)-8s:%(levelname)5s:%(name)s: %(message)s"))
    logging.getLogger('').addHandler(handler)
    main()
