import logging
import time

import paramiko
import stomp


_LOGGER = logging.getLogger(__name__)


class SshBasedTransport(stomp.transport.BaseTransport):
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
                    time.sleep(0.2)
            except paramiko.ssh_exception.SSHException as ex:
                time.sleep(sleep_time)
                if sleep_time < 100:
                    sleep_time *= 2

    def send(self, encoded_frame):
        if not self.is_connected():
            raise stomp.exception.NotConnectedException()
        self.channel.sendall(encoded_frame)

    def receive(self):
        result = self.channel.recv(4096)
        _LOGGER.debug("Got %s", result)
        return result

    def cleanup(self):
        self.channel.close()
        self.channel = None

    def disconnect_socket(self):
        self.channel.close()
        self.client.close()


class SshBasedConnection(stomp.Connection12):
    """
    STOMP connection that uses SshBasedTransport.
    """

    def __init__(self, hostname, port, username, keyfile,
                 heartbeats=(0,0),
                 auto_content_length=True,
                 heart_beat_receive_scale=1.5):
        transport = SshBasedTransport(hostname, port, username, keyfile)
        stomp.connect.BaseConnection.__init__(self, transport)
        stomp.protocol.Protocol12.__init__(self, transport, heartbeats, auto_content_length,
                                           heart_beat_receive_scale=heart_beat_receive_scale)
