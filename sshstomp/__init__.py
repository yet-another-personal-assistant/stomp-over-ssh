import logging
import time

import paramiko
import stomp

import pdb


_LOGGER = logging.getLogger(__name__)


class SshBasedTransport:
    """
    STOMP transport that utilizes ssh connection instead of socket.
    """

    def __init__(self, hostname, port, username, key):
        super().__init__()
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.hostname = hostname
        self.port = port
        self.username = username
        self.vhost = f"{username}@{hostname}:{port}"
        self.channel = None
        self.key = key

    def is_connected(self):
        return self.channel is not None and not self.channel.closed

    def attempt_connection(self):
        sleep_time = 8
        while not self.is_connected():
            try:
                transport = self.client.get_transport()
                if transport is None or not transport.is_active():
                    self.client.connect(self.hostname, self.port, self.username, key_filename=self.key)
                    self.current_host_and_port = (self.hostname, self.port)

                _LOGGER.debug("transport connected")
                if self.channel is None or self.channel.closed:
                    self.client.get_transport().set_keepalive(60)
                    self.channel = self.client.invoke_shell()
            except paramiko.ssh_exception.SSHException as ex:
                time.sleep(sleep_time)
                if sleep_time < 100:
                    sleep_time *= 2

    def send(self, encoded_frame):
        if not self.is_connected():
            raise stomp.exception.NotConnectedException()
        self.channel.sendall(encoded_frame)
        self.channel.send(b'\n')
        return len(encoded_frame)

    def receive(self):
        result = self.channel.recv(4096)
        return result

    def cleanup(self):
        self.channel.close()
        self.channel = None

    def disconnect_socket(self):
        self.channel.close()
        self.client.close()
